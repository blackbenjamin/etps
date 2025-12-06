"""
Bullet Rewriter Service

LLM-powered bullet rewriting for resume optimization.
Rewrites bullets to include JD keywords while preserving factual accuracy.
"""

import re
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

from sqlalchemy.orm import Session

from db.models import Bullet, JobProfile
from schemas.resume_tailor import SelectedBullet

logger = logging.getLogger(__name__)


def load_prompt_template() -> str:
    """Load the bullet rewrite prompt template."""
    prompt_path = Path(__file__).parent / "llm" / "prompts" / "bullet_rewrite.txt"
    with open(prompt_path, "r") as f:
        return f.read()


def extract_metrics(text: str) -> set:
    """Extract numbers, percentages, and metrics from text."""
    patterns = [
        r'\d+(?:,\d{3})*(?:\.\d+)?%?',  # Numbers with commas, decimals, percentages
        r'\$\d+(?:,\d{3})*(?:\.\d+)?[KMB]?',  # Currency
        r'\d+[KMB]?\+?',  # Shorthand numbers like 500K, 2M+
    ]
    metrics = set()
    for pattern in patterns:
        metrics.update(re.findall(pattern, text))
    return metrics


def extract_proper_nouns(text: str) -> set:
    """Extract capitalized words (proper nouns) from text."""
    # Match capitalized words that aren't at the start of a sentence
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    # Filter out common action verbs that might be capitalized
    common_verbs = {'Led', 'Built', 'Delivered', 'Drove', 'Implemented',
                    'Architected', 'Designed', 'Established', 'Scaled',
                    'Transformed', 'Optimized', 'Managed', 'Created'}
    return {w for w in words if w not in common_verbs}


def extract_action_verb(text: str) -> Optional[str]:
    """Extract the first action verb from a bullet."""
    words = text.strip().split()
    if words:
        first_word = words[0].rstrip(',.:;')
        return first_word
    return None


def validate_rewrite(original: str, rewritten: str) -> Tuple[bool, List[str]]:
    """
    Validate that a rewritten bullet preserves factual accuracy.

    Checks:
    - All metrics/numbers from original appear in rewritten
    - All proper nouns from original appear in rewritten

    Returns:
        (is_valid, list_of_violations)
    """
    violations = []

    # Extract and compare metrics
    original_metrics = extract_metrics(original)
    rewritten_metrics = extract_metrics(rewritten)

    missing_metrics = original_metrics - rewritten_metrics
    if missing_metrics:
        violations.append(f"Missing metrics: {', '.join(missing_metrics)}")

    # Extract and compare proper nouns
    original_nouns = extract_proper_nouns(original)
    rewritten_nouns = extract_proper_nouns(rewritten)

    missing_nouns = original_nouns - rewritten_nouns
    if missing_nouns:
        violations.append(f"Missing proper nouns: {', '.join(missing_nouns)}")

    is_valid = len(violations) == 0
    return is_valid, violations


async def rewrite_bullet(
    bullet_text: str,
    jd_keywords: List[str],
    llm_client: Any,
    star_notes: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> Tuple[str, bool]:
    """
    Rewrite a single bullet using LLM.

    Args:
        bullet_text: Original bullet text
        jd_keywords: Keywords from job description to incorporate
        llm_client: OpenAI client instance
        star_notes: Optional STAR method notes for enrichment
        model: LLM model to use

    Returns:
        (rewritten_text, was_successful)
    """
    prompt_template = load_prompt_template()
    current_verb = extract_action_verb(bullet_text) or "Unknown"

    prompt = prompt_template.format(
        bullet_text=bullet_text,
        star_notes=star_notes or "Not provided",
        jd_keywords=", ".join(jd_keywords[:10]),  # Limit to top 10 keywords
        current_verb=current_verb
    )

    try:
        response = await llm_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a resume bullet optimizer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        rewritten = response.choices[0].message.content.strip()

        # Validate the rewrite
        is_valid, violations = validate_rewrite(bullet_text, rewritten)

        if not is_valid:
            logger.warning(
                f"Bullet rewrite validation failed: {violations}. "
                f"Original: {bullet_text[:50]}..."
            )
            return bullet_text, False  # Return original if validation fails

        return rewritten, True

    except Exception as e:
        logger.error(f"Error rewriting bullet: {e}")
        return bullet_text, False


def store_version_history(
    db: Session,
    bullet: Bullet,
    rewritten_text: str,
    job_profile_id: int,
    keywords_added: List[str],
    rewrite_type: str = "keyword_optimization"
) -> None:
    """
    Store a rewritten version in the bullet's version history.

    Args:
        db: Database session
        bullet: Bullet model instance
        rewritten_text: The rewritten bullet text
        job_profile_id: ID of the job profile this rewrite was for
        keywords_added: Keywords that were incorporated
        rewrite_type: Type of rewrite performed
    """
    version_entry = {
        "text": rewritten_text,
        "created_at": datetime.utcnow().isoformat(),
        "context": f"job_profile_{job_profile_id}",
        "rewrite_type": rewrite_type,
        "keywords_added": keywords_added,
        "original_ref": bullet.id
    }

    # Initialize version_history if None
    if bullet.version_history is None:
        bullet.version_history = {"versions": []}

    # Append new version
    bullet.version_history["versions"].append(version_entry)

    # Keep only last 10 versions to prevent unbounded growth
    if len(bullet.version_history["versions"]) > 10:
        bullet.version_history["versions"] = bullet.version_history["versions"][-10:]

    db.add(bullet)
    db.commit()


async def rewrite_bullets_for_job(
    selected_bullets: List[SelectedBullet],
    job_profile: JobProfile,
    llm_client: Any,
    db: Session,
    bullets_db: Dict[int, Bullet],
    strategy: str = "both"
) -> List[SelectedBullet]:
    """
    Rewrite all selected bullets for a job application.

    Args:
        selected_bullets: List of SelectedBullet objects to rewrite
        job_profile: JobProfile with extracted skills/keywords
        llm_client: OpenAI client instance
        db: Database session for storing version history
        bullets_db: Dict mapping bullet_id to Bullet model (for STAR notes and version history)
        strategy: Rewrite strategy - "keywords", "star_enrichment", or "both"

    Returns:
        Updated list of SelectedBullet with rewritten text
    """
    # Extract keywords from job profile
    jd_keywords = []
    if job_profile.extracted_skills:
        jd_keywords.extend(job_profile.extracted_skills)
    if job_profile.must_have_capabilities:
        jd_keywords.extend(job_profile.must_have_capabilities)
    if job_profile.core_priorities:
        jd_keywords.extend(job_profile.core_priorities)

    # Deduplicate and limit keywords
    jd_keywords = list(set(jd_keywords))[:15]

    rewritten_bullets = []

    for sb in selected_bullets:
        bullet_db = bullets_db.get(sb.bullet_id)
        star_notes = bullet_db.star_notes if bullet_db and strategy in ("star_enrichment", "both") else None

        rewritten_text, success = await rewrite_bullet(
            bullet_text=sb.text,
            jd_keywords=jd_keywords,
            llm_client=llm_client,
            star_notes=star_notes
        )

        if success and rewritten_text != sb.text:
            # Store version history
            if bullet_db:
                keywords_in_rewrite = [k for k in jd_keywords if k.lower() in rewritten_text.lower()]
                store_version_history(
                    db=db,
                    bullet=bullet_db,
                    rewritten_text=rewritten_text,
                    job_profile_id=job_profile.id,
                    keywords_added=keywords_in_rewrite,
                    rewrite_type="keyword_optimization" if strategy == "keywords" else "combined"
                )

            # Create updated SelectedBullet
            rewritten_bullets.append(SelectedBullet(
                bullet_id=sb.bullet_id,
                text=rewritten_text,
                relevance_score=sb.relevance_score,
                was_rewritten=True,
                original_text=sb.text,
                tags=sb.tags,
                selection_reason=sb.selection_reason,
                engagement_id=sb.engagement_id
            ))
        else:
            # Keep original bullet
            rewritten_bullets.append(sb)

    logger.info(
        f"Rewrote {sum(1 for b in rewritten_bullets if b.was_rewritten)}/{len(selected_bullets)} "
        f"bullets for job_profile {job_profile.id}"
    )

    return rewritten_bullets


async def compress_bullet_for_space(
    bullet_text: str,
    target_reduction: float = 0.20,
    llm_client: Optional[Any] = None,
    use_llm: bool = False
) -> Tuple[str, bool]:
    """
    Compress a bullet to reduce character count while preserving meaning.

    Two modes:
    1. Heuristic mode (default): Uses pattern-based compression
    2. LLM mode: Uses LLM to intelligently shorten while preserving facts

    Args:
        bullet_text: Original bullet text
        target_reduction: Target reduction percentage (0.20 = 20%)
        llm_client: Optional OpenAI client for LLM mode
        use_llm: If True, use LLM for smarter compression

    Returns:
        Tuple of (compressed_text, was_modified)
    """
    if not bullet_text:
        return bullet_text, False

    original_length = len(bullet_text)

    if use_llm and llm_client:
        # LLM-based compression
        prompt = f'''Shorten this resume bullet point by approximately {int(target_reduction * 100)}% while:
1. Preserving ALL factual information (numbers, metrics, outcomes)
2. Keeping the same meaning and impact
3. Maintaining professional tone
4. Starting with a strong action verb

Original bullet ({original_length} chars):
"{bullet_text}"

Shortened version (aim for ~{int(original_length * (1 - target_reduction))} chars):'''

        try:
            response = await llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )
            compressed = response.choices[0].message.content.strip()

            # Remove quotes if present
            compressed = compressed.strip('"\'')

            # Validate compression didn't remove too much
            if len(compressed) > original_length * 0.5:  # At least 50% of original
                return compressed, True
        except Exception as e:
            logger.warning(f"LLM compression failed, falling back to heuristic: {e}")

    # Heuristic compression (import from pagination)
    from services.pagination import compress_bullet_text
    compressed = compress_bullet_text(bullet_text, target_reduction)

    was_modified = compressed != bullet_text
    return compressed, was_modified
