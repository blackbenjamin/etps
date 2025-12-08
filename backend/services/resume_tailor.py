"""
Resume Tailoring Service

Intelligently selects and optimizes resume content (bullets, skills, summary)
to maximize alignment with specific job requirements.
"""

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from sqlalchemy.orm import Session

from db.models import Bullet, Engagement, Experience, JobProfile, User


# Configuration loader
def _load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = os.path.join(
        os.path.dirname(__file__), '..', 'config', 'config.yaml'
    )
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}


_CONFIG = _load_config()
# Sprint 8B.6: Read defaults from config.yaml
DEFAULT_MAX_ITERATIONS = int(_CONFIG.get('critic', {}).get('max_iterations', 3))
from schemas.resume_tailor import (
    SelectedBullet,
    SelectedEngagement,
    SelectedRole,
    SelectedSkill,
    TailoredResume,
    TailoringRationale,
)
from schemas.skill_gap import SkillGapResponse
from services.skill_gap import (
    SKILL_SYNONYMS,
    analyze_skill_gap,
    normalize_skill,
    find_skill_match_sync,
)
from services.llm.base import BaseLLM
from services.bullet_rewriter import rewrite_bullets_for_job
from services.summary_rewrite import rewrite_summary_for_job
# Sprint 8: Learning from approved outputs (available for future integration)
from services.output_retrieval import (
    retrieve_similar_bullets,
    retrieve_similar_summaries,
    format_examples_for_prompt,
)
from services.pagination import PaginationService, PageSplitSimulator


logger = logging.getLogger(__name__)


# Banned phrases that should be removed from generated summaries
BANNED_PHRASES = [
    "seasoned professional",
    "results-oriented",
    "proven track record",
    "dynamic",
    "synergy",
    "leverage",
    "best-in-class",
    "world-class",
    "cutting-edge",
    "innovative thinker",
    "go-getter",
    "team player",
    "detail-oriented",
    "hard-working",
    "passionate about",
]


def is_ai_heavy_job(job_profile: JobProfile) -> bool:
    """
    Determine if a job is AI/ML-heavy based on job type tags and extracted skills.

    A job is considered AI-heavy if it has 2+ AI-related terms in its tags or skills.
    """
    ai_terms = {
        'ai', 'ml', 'machine learning', 'deep learning', 'llm', 'nlp',
        'natural language processing', 'generative ai', 'ai governance',
        'ai strategy', 'ai ethics', 'computer vision', 'neural network',
        'transformers', 'gpt', 'large language model', 'ai/ml', 'ai risk'
    }

    job_terms = set()

    # Collect terms from job profile
    if job_profile.job_type_tags:
        job_terms.update(t.lower() for t in job_profile.job_type_tags)
    if job_profile.extracted_skills:
        job_terms.update(s.lower() for s in job_profile.extracted_skills)
    if job_profile.core_priorities:
        for p in job_profile.core_priorities:
            job_terms.update(p.lower().split())

    # Count AI-related matches
    ai_matches = len(ai_terms & job_terms)
    return ai_matches >= 2


def get_portfolio_bullets(user: User, job_profile: JobProfile, db: Session) -> List[Bullet]:
    """
    Generate synthetic bullets from ai_portfolio for AI-heavy jobs.

    Creates temporary Bullet objects from the user's ai_portfolio projects
    when the job emphasizes AI/ML skills.

    Args:
        user: User model with candidate_profile containing ai_portfolio
        job_profile: JobProfile to check AI relevance
        db: Database session (not used for portfolio bullets, they're synthetic)

    Returns:
        List of synthetic Bullet objects for portfolio projects
    """
    if not is_ai_heavy_job(job_profile):
        return []

    candidate_profile = user.candidate_profile or {}
    portfolio = candidate_profile.get('ai_portfolio', [])

    if not portfolio:
        return []

    bullets = []
    for idx, project in enumerate(portfolio):
        # Extract project details
        name = project.get('name', 'AI Project')
        description = project.get('description', '')
        tech_stack = project.get('tech_stack', [])
        impact = project.get('impact', '')

        # Build bullet text
        if impact:
            bullet_text = f"Designed and built {name}: {description} - {impact}"
        else:
            bullet_text = f"Designed and built {name}: {description}"

        # Truncate if too long
        if len(bullet_text) > 200:
            bullet_text = bullet_text[:197] + "..."

        # Create synthetic bullet (not persisted to DB)
        synthetic_bullet = Bullet(
            id=-1000 - idx,  # Negative ID to distinguish from real bullets
            user_id=user.id,
            experience_id=None,  # Will be assigned to current consulting role
            engagement_id=None,
            text=bullet_text,
            tags=['ai_portfolio'] + tech_stack,
            seniority_level='senior',
            bullet_type='achievement',
            relevance_scores={'ai': 0.95, 'ml': 0.90, 'technology': 0.85},
            ai_first_choice=True,
            importance='high',
            order=100 + idx,  # Place after regular bullets
        )
        bullets.append(synthetic_bullet)

    logger.info(f"Generated {len(bullets)} portfolio bullets for AI-heavy job")
    return bullets


def select_bullets_for_role(
    experience: Experience,
    bullets: List[Bullet],
    job_profile: JobProfile,
    skill_gap_result: SkillGapResponse,
    max_bullets: int = 4
) -> List[SelectedBullet]:
    """
    Select optimal bullets for a role based on multi-factor scoring.

    Scoring formula:
    - Tag matching (40%): How well bullet tags align with job skills
    - Relevance score (30%): Pre-computed relevance scores for bullets
    - Usage/recency (20%): Prefer less-used bullets for freshness
    - Type diversity (10%): Bonus for diverse bullet types

    Args:
        experience: The experience/role to select bullets for
        bullets: List of all bullets for this experience
        job_profile: Target job profile
        skill_gap_result: Skill gap analysis for guidance
        max_bullets: Maximum number of bullets to select

    Returns:
        List of selected bullets with scoring metadata
    """
    if not bullets:
        return []

    # Filter out retired bullets
    active_bullets = [b for b in bullets if not b.retired]
    if not active_bullets:
        return []

    # Extract job skills and matched skills for scoring
    job_skills = job_profile.extracted_skills or []
    matched_skills = {m.skill for m in skill_gap_result.matched_skills}
    priority_tags = skill_gap_result.bullet_selection_guidance.get('prioritize_tags', [])

    # Sprint 10E: Use user-selected skills if available
    user_selected_skills = set()
    skill_priority_map = {}  # Maps skill -> priority weight (0.0-1.0)

    if job_profile.selected_skills:
        for selected in job_profile.selected_skills:
            if selected.get('included', True):
                skill = selected['skill']
                user_selected_skills.add(skill.lower())
                # Higher order (earlier in list) = higher priority
                # Convert order (0-N) to weight (1.0 - 0.3)
                max_order = len(job_profile.selected_skills)
                priority_weight = 1.0 - (selected.get('order', 0) / max(max_order, 1) * 0.7)
                skill_priority_map[skill.lower()] = priority_weight

    # Extract positioning keywords from skill gap analysis (Sprint 8B.3)
    positioning_keywords = set()
    if skill_gap_result and skill_gap_result.key_positioning_angles:
        for angle in skill_gap_result.key_positioning_angles[:3]:
            # Extract significant words from positioning angles
            words = set(word.lower() for word in angle.split()
                       if len(word) > 3 and word.lower() not in {'and', 'the', 'with', 'for', 'that', 'this'})
            positioning_keywords.update(words)

    # Extract user advantages for bonus scoring
    user_advantage_terms = set()
    if skill_gap_result and skill_gap_result.user_advantages:
        for advantage in skill_gap_result.user_advantages[:3]:
            words = set(word.lower() for word in advantage.split()
                       if len(word) > 3 and word.lower() not in {'and', 'the', 'with', 'for', 'that', 'this'})
            user_advantage_terms.update(words)

    # Score each bullet
    scored_bullets: List[Tuple[Bullet, float, str]] = []

    for bullet in active_bullets:
        # 1. Tag matching score (40%)
        tag_score = 0.0
        matching_tags = []
        if bullet.tags:
            for tag in bullet.tags:
                tag_lower = tag.lower()

                # Sprint 10E: Bonus for user-selected skills (highest priority)
                if user_selected_skills and tag_lower in user_selected_skills:
                    priority_weight = skill_priority_map.get(tag_lower, 0.8)
                    tag_score += priority_weight * 1.5  # 1.5x multiplier for user selection
                    if tag not in matching_tags:
                        matching_tags.append(tag)
                    continue  # Skip other checks if user selected this skill

                # Check against matched skills
                for job_skill in job_skills:
                    if find_skill_match_sync(job_skill, [tag]):
                        tag_score += 1.0
                        matching_tags.append(tag)
                        break

                # Bonus for priority tags
                if tag in priority_tags:
                    tag_score += 0.5
                    if tag not in matching_tags:
                        matching_tags.append(tag)

        # Normalize tag score (cap at 1.0)
        tag_score = min(tag_score / max(len(job_skills), 1), 1.0) * 0.4

        # 2. Relevance score (30%)
        relevance_score = 0.0
        if bullet.relevance_scores:
            # Average relevance for matched skills
            relevant_scores = [
                score for skill, score in bullet.relevance_scores.items()
                if any(find_skill_match_sync(ms, [skill]) for ms in matched_skills)
            ]
            if relevant_scores:
                relevance_score = (sum(relevant_scores) / len(relevant_scores)) * 0.3
            else:
                # Use max relevance if no matched skills
                relevance_score = max(bullet.relevance_scores.values(), default=0.5) * 0.3
        else:
            relevance_score = 0.5 * 0.3  # Default mid-range score

        # 3. Usage/recency score (20%) - prefer less used bullets
        usage_score = 0.0
        if bullet.usage_count == 0:
            usage_score = 1.0 * 0.2  # Never used - highest score
        else:
            # Exponential decay - more used = lower score
            usage_score = (1.0 / (1.0 + bullet.usage_count * 0.5)) * 0.2

        # 4. Type diversity bonus (10%)
        type_score = 0.1  # Default
        if bullet.bullet_type:
            # Slight preference for achievement and metric_impact types
            if bullet.bullet_type in ['achievement', 'metric_impact']:
                type_score = 0.15
            elif bullet.bullet_type == 'responsibility':
                type_score = 0.08

        # 5. Importance flag bonus
        importance_bonus = 0.0
        if hasattr(bullet, 'importance') and bullet.importance:
            if bullet.importance == 'high':
                importance_bonus = 0.08
            elif bullet.importance == 'medium':
                importance_bonus = 0.04
            elif bullet.importance == 'low':
                importance_bonus = 0.0

        # 6. AI-first choice bonus for AI/ML jobs
        ai_first_choice_bonus = 0.0
        if hasattr(bullet, 'ai_first_choice') and bullet.ai_first_choice:
            if is_ai_heavy_job(job_profile):
                ai_first_choice_bonus = 0.12

        # 7. Positioning alignment bonus (Sprint 8B.3) - up to +0.10
        positioning_bonus = 0.0
        if positioning_keywords and bullet.text:
            bullet_words = set(word.lower() for word in bullet.text.split())
            overlap_count = len(positioning_keywords & bullet_words)
            if overlap_count > 0:
                positioning_bonus = min(overlap_count * 0.03, 0.10)

        # 8. User advantage alignment bonus (Sprint 8B.3) - up to +0.08
        advantage_bonus = 0.0
        if user_advantage_terms and bullet.text:
            bullet_words = set(word.lower() for word in bullet.text.split())
            if len(user_advantage_terms & bullet_words) > 0:
                advantage_bonus = 0.08

        # Calculate total score
        total_score = tag_score + relevance_score + usage_score + type_score + importance_bonus + ai_first_choice_bonus + positioning_bonus + advantage_bonus

        # Build selection reason
        reason_parts = []
        if matching_tags:
            reason_parts.append(f"Matches key skills: {', '.join(matching_tags[:3])}")
        if bullet.bullet_type in ['achievement', 'metric_impact']:
            reason_parts.append(f"Strong {bullet.bullet_type} statement")
        if bullet.usage_count == 0:
            reason_parts.append("Fresh content (not recently used)")
        if positioning_bonus > 0:
            reason_parts.append("Aligns with positioning strategy")
        if advantage_bonus > 0:
            reason_parts.append("Highlights user advantage")

        selection_reason = "; ".join(reason_parts) if reason_parts else "Relevant experience"

        scored_bullets.append((bullet, total_score, selection_reason))

    # Sort by score descending
    scored_bullets.sort(key=lambda x: x[1], reverse=True)

    # Select top N bullets, ensuring type diversity
    selected: List[SelectedBullet] = []
    type_counts: Dict[str, int] = {}

    for bullet, score, reason in scored_bullets:
        if len(selected) >= max_bullets:
            break

        # Encourage type diversity (no more than max_bullets - 1 of same type)
        bullet_type = bullet.bullet_type or 'general'
        if type_counts.get(bullet_type, 0) >= max_bullets - 1:
            continue

        selected.append(SelectedBullet(
            bullet_id=bullet.id,
            text=bullet.text,
            relevance_score=round(score, 2),
            was_rewritten=False,  # No rewriting in initial implementation
            original_text=None,
            tags=bullet.tags or [],
            selection_reason=reason,
        ))

        type_counts[bullet_type] = type_counts.get(bullet_type, 0) + 1

    # If we didn't get enough, fill with remaining bullets
    if len(selected) < max_bullets:
        remaining_bullets = [
            (b, s, r) for b, s, r in scored_bullets
            if not any(sb.bullet_id == b.id for sb in selected)
        ]
        for bullet, score, reason in remaining_bullets[:max_bullets - len(selected)]:
            selected.append(SelectedBullet(
                bullet_id=bullet.id,
                text=bullet.text,
                relevance_score=round(score, 2),
                was_rewritten=False,
                original_text=None,
                tags=bullet.tags or [],
                selection_reason=reason,
            ))

    return selected


def select_engagements_for_experience(
    experience: Experience,
    job_profile: JobProfile,
    max_engagements: int = 3,
) -> List[Engagement]:
    """
    Select the most relevant engagements for a consulting role.

    Scoring:
    - domain_tags overlap with job requirements (50%)
    - tech_tags overlap with job skills (30%)
    - Recency/order (20%)

    Args:
        experience: Experience with engagements to select from
        job_profile: Target job profile
        max_engagements: Maximum engagements to select (default 3)

    Returns:
        List of selected Engagement objects, ordered by relevance
    """
    if not experience.engagements:
        return []

    # Build job context for matching
    job_domains = set()
    job_skills = set()

    if job_profile.job_type_tags:
        job_domains.update(t.lower() for t in job_profile.job_type_tags)
    if job_profile.extracted_skills:
        job_skills.update(s.lower() for s in job_profile.extracted_skills)
    if job_profile.must_have_capabilities:
        job_skills.update(c.lower() for c in job_profile.must_have_capabilities)

    scored_engagements = []

    for eng in experience.engagements:
        # Domain tag overlap (50%)
        eng_domains = set((t.lower() for t in (eng.domain_tags or [])))
        domain_overlap = len(eng_domains & job_domains)
        domain_score = min(domain_overlap * 0.15, 0.50)  # Cap at 50%

        # Tech tag overlap (30%)
        eng_techs = set((t.lower() for t in (eng.tech_tags or [])))
        tech_overlap = len(eng_techs & job_skills)
        tech_score = min(tech_overlap * 0.10, 0.30)  # Cap at 30%

        # Order/recency bonus (20%) - lower order = more recent
        order_score = max(0.20 - (eng.order * 0.02), 0.0)

        total_score = domain_score + tech_score + order_score
        scored_engagements.append((total_score, eng))

    # Sort by score descending
    scored_engagements.sort(key=lambda x: x[0], reverse=True)

    # Select top N
    selected = [eng for _, eng in scored_engagements[:max_engagements]]

    logger.debug(
        f"Selected {len(selected)}/{len(experience.engagements)} engagements "
        f"for {experience.employer_name}"
    )

    return selected


def select_and_order_skills(
    user_bullets: List[Bullet],
    job_profile: JobProfile,
    skill_gap_result: SkillGapResponse,
    max_skills: int = 12
) -> List[SelectedSkill]:
    """
    Select and order skills for resume skills section using tier-based approach.

    Tier-based selection:
    - Tier 1: Critical matched skills (high match strength)
    - Tier 2: Strong matched skills (match_strength >= 0.7)
    - Tier 3: Important job requirements (even if weak match)
    - Tier 4: Weak signals and transferable skills

    Args:
        user_bullets: User's bullet points with tags
        job_profile: Target job profile
        skill_gap_result: Skill gap analysis result
        max_skills: Maximum number of skills to include

    Returns:
        Ordered list of selected skills with metadata
    """
    selected_skills: List[SelectedSkill] = []
    selected_skill_names: Set[str] = set()

    # Tier 1: Critical matched skills (match_strength >= 0.75)
    critical_matches = [
        m for m in skill_gap_result.matched_skills
        if m.match_strength >= 0.75
    ]
    for match in sorted(critical_matches, key=lambda m: m.match_strength, reverse=True):
        if len(selected_skills) >= max_skills:
            break

        normalized = normalize_skill(match.skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=match.skill,
                priority_score=match.match_strength,
                match_type="direct_match",
                source="job_requirements",
            ))
            selected_skill_names.add(normalized)

    # Tier 2: Strong matched skills (0.5 <= match_strength < 0.75)
    strong_matches = [
        m for m in skill_gap_result.matched_skills
        if 0.5 <= m.match_strength < 0.75
    ]
    for match in sorted(strong_matches, key=lambda m: m.match_strength, reverse=True):
        if len(selected_skills) >= max_skills:
            break

        normalized = normalize_skill(match.skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=match.skill,
                priority_score=match.match_strength,
                match_type="direct_match",
                source="job_requirements",
            ))
            selected_skill_names.add(normalized)

    # Tier 3: Important job skills from job profile (extracted skill names only)
    # Note: We use extracted_skills here, NOT must_have_capabilities, because
    # must_have_capabilities contains full requirement sentences (e.g., "3-6 years
    # of experience in consulting...") which are not suitable as skill names.
    job_skills = job_profile.extracted_skills or []

    for skill in job_skills[:max_skills - len(selected_skills)]:
        normalized = normalize_skill(skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=skill,
                priority_score=0.7,  # Moderate priority
                match_type="adjacent_skill",
                source="job_requirements",
            ))
            selected_skill_names.add(normalized)

    # Tier 4: Weak signals (adjacent capabilities)
    weak_signals = skill_gap_result.weak_signals
    for weak in weak_signals[:max_skills - len(selected_skills)]:
        normalized = normalize_skill(weak.skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=weak.skill,
                priority_score=0.5,
                match_type="transferable",
                source="user_master_resume",
            ))
            selected_skill_names.add(normalized)

    # If still under max_skills, add remaining matched skills
    remaining_matches = [
        m for m in skill_gap_result.matched_skills
        if normalize_skill(m.skill) not in selected_skill_names
    ]
    for match in sorted(remaining_matches, key=lambda m: m.match_strength, reverse=True):
        if len(selected_skills) >= max_skills:
            break

        normalized = normalize_skill(match.skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=match.skill,
                priority_score=match.match_strength,
                match_type="direct_match",
                source="job_requirements",
            ))
            selected_skill_names.add(normalized)

    return selected_skills[:max_skills]


async def generate_tailored_summary(
    user_name: str,
    experiences: List[Experience],
    job_profile: JobProfile,
    skill_gap_result: SkillGapResponse,
    selected_skills: List[SelectedSkill],
    llm: BaseLLM
) -> str:
    """
    Generate tailored executive summary optimized for target job.

    .. deprecated:: Sprint 5B
        Use :func:`services.summary_rewrite.rewrite_summary_for_job` instead.
        This function is kept for backward compatibility but will be removed
        in a future version. The new function uses candidate_profile for better
        personalization and enforces PRD 2.10 constraints (60 word limit).

    Uses LLM to generate 60-80 word summary emphasizing matched skills,
    relevant seniority, and key achievements aligned with job priorities.

    Args:
        user_name: User's full name
        experiences: User's work experiences
        job_profile: Target job profile
        skill_gap_result: Skill gap analysis
        selected_skills: Skills selected for resume
        llm: LLM instance for generation

    Returns:
        Tailored professional summary (60-80 words)
    """
    import warnings
    warnings.warn(
        "generate_tailored_summary is deprecated. Use rewrite_summary_for_job instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Extract key information for summary
    top_skills = [s.skill for s in selected_skills[:5]]
    matched_skills = [m.skill for m in skill_gap_result.matched_skills[:3]]
    seniority = job_profile.seniority or "experienced"
    job_title = job_profile.job_title
    positioning_angles = skill_gap_result.key_positioning_angles[:2]  # Top 2 positioning strategies

    # Calculate years of experience
    years_exp = 0
    if experiences:
        for exp in experiences:
            years = (exp.end_date or datetime.now().date()).year - exp.start_date.year
            years_exp += max(years, 0)

    # Build context for LLM
    context = {
        'job_title': job_title,
        'seniority': seniority,
        'top_skills': top_skills,
        'matched_skills': matched_skills,
        'years_experience': years_exp,
        'job_priorities': job_profile.core_priorities or [],
        'positioning_angles': positioning_angles,
    }

    # Generate summary using LLM
    prompt = f"""Generate a professional resume summary (60-80 words) for a candidate targeting this role:

Job Title: {job_title}
Seniority: {seniority}

The candidate has {years_exp}+ years of experience with strong expertise in:
{', '.join(top_skills[:5])}

Key skills that match job requirements:
{', '.join(matched_skills)}

Job priorities to address:
{', '.join(job_profile.core_priorities[:3]) if job_profile.core_priorities else 'N/A'}

Positioning strategies to incorporate:
{', '.join(positioning_angles) if positioning_angles else 'N/A'}

Write a compelling summary that:
1. Emphasizes matched skills and relevant experience
2. Aligns with job seniority level
3. Addresses 1-2 key job priorities
4. Incorporates the positioning strategies subtly
5. Is concrete and achievement-focused (avoid generic phrases)
6. Is exactly 60-80 words

Summary:"""

    # For MockLLM, use template-based generation
    if llm.__class__.__name__ == 'MockLLM':
        summary = _generate_mock_summary(
            seniority=seniority,
            years_exp=years_exp,
            top_skills=top_skills,
            matched_skills=matched_skills,
            job_title=job_title,
        )
    else:
        summary = await llm.generate_text(prompt, max_tokens=200)

    # Post-process: remove banned phrases using word-boundary regex
    # Note: This is a basic cleanup for summaries. More rigorous enforcement
    # should be applied during cover letter generation (PRD Section 3.5)
    for phrase in BANNED_PHRASES:
        # Use word boundaries to avoid partial matches (e.g., "passionate" in "compassionate")
        pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
        summary = pattern.sub('', summary)

    # Clean up extra spaces and formatting
    summary = " ".join(summary.split())

    return summary.strip()


def _generate_mock_summary(
    seniority: str,
    years_exp: int,
    top_skills: List[str],
    matched_skills: List[str],
    job_title: str,
) -> str:
    """
    Generate mock summary using template for development/testing.

    Args:
        seniority: Seniority level
        years_exp: Years of experience
        top_skills: Top skills to highlight
        matched_skills: Matched skills
        job_title: Target job title

    Returns:
        Template-based summary
    """
    # Determine role type
    role_descriptor = "professional"
    if "director" in seniority.lower() or "vp" in seniority.lower():
        role_descriptor = "leader"
    elif "senior" in seniority.lower():
        role_descriptor = "specialist"

    # Build summary
    skills_str = ", ".join(matched_skills[:3]) if matched_skills else ", ".join(top_skills[:3])

    summary = (
        f"{role_descriptor.capitalize()} with {years_exp}+ years of experience "
        f"specializing in {skills_str}. Demonstrated expertise in delivering "
        f"impactful solutions through technical excellence and strategic execution. "
        f"Proven ability to drive results in complex environments requiring "
        f"{top_skills[0] if top_skills else 'technical expertise'}."
    )

    return summary


async def tailor_resume(
    job_profile_id: int,
    user_id: int,
    db: Session,
    max_bullets_per_role: int = 4,
    max_skills: int = 12,
    custom_instructions: Optional[str] = None,
    llm: Optional[BaseLLM] = None,
    enable_bullet_rewriting: bool = False,
    rewrite_strategy: Optional[str] = "both",
    enable_learning: bool = True,
    enable_pagination_aware: bool = False  # NEW: Sprint 8C.5
) -> TailoredResume:
    """
    Main orchestrator: Generate complete tailored resume for specific job.

    Workflow:
    1. Fetch job profile and user data
    2. Analyze skill gaps
    3. Select optimal bullets for each role
    4. Apply bullet rewriting if enabled (integrates JD keywords)
    5. Select and order skills
    6. Generate tailored summary
    7. Build comprehensive rationale
    8. Validate constraints

    Args:
        job_profile_id: ID of target job profile
        user_id: User ID
        db: Database session
        max_bullets_per_role: Maximum bullets per experience (2-8)
        max_skills: Maximum skills in skills section (5-20)
        custom_instructions: Optional user instructions for tailoring
        llm: Optional LLM instance (will use MockLLM if not provided)
        enable_bullet_rewriting: If True, rewrite bullets to include JD keywords
        rewrite_strategy: Strategy for rewriting - "keywords", "star_enrichment", or "both"
        enable_learning: If True, retrieve similar approved bullets for learning (Sprint 8B.1)
        enable_pagination_aware: If True, use space-aware bullet selection with value-per-line prioritization

    Returns:
        Complete tailored resume with rationale

    Raises:
        ValueError: If job profile or user not found, or invalid parameters
    """
    # Validate parameters FIRST (before any database queries)
    if not 2 <= max_bullets_per_role <= 8:
        raise ValueError("max_bullets_per_role must be between 2 and 8")
    if not 5 <= max_skills <= 20:
        raise ValueError("max_skills must be between 5 and 20")

    # Fetch job profile
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile:
        raise ValueError(f"Job profile {job_profile_id} not found")

    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Fetch user's experiences (ordered by order field, then by start_date desc)
    experiences = db.query(Experience).filter(
        Experience.user_id == user_id
    ).order_by(
        Experience.order.asc(),
        Experience.start_date.desc()
    ).all()

    if not experiences:
        raise ValueError(f"User {user_id} has no experiences")

    # Fetch all user's bullets
    all_bullets = db.query(Bullet).filter(
        Bullet.user_id == user_id,
        Bullet.retired == False
    ).all()

    # Add portfolio bullets for AI-heavy jobs
    portfolio_bullets = get_portfolio_bullets(user, job_profile, db)
    if portfolio_bullets:
        all_bullets = list(all_bullets) + portfolio_bullets  # Convert to list if needed
        logger.info(f"Added {len(portfolio_bullets)} portfolio bullets for AI-heavy job {job_profile.id}")

    # Initialize OpenAI client for bullet rewriting if enabled
    llm_client = None
    if enable_bullet_rewriting:
        import openai
        llm_client = openai.AsyncOpenAI()

    # Analyze skill gap
    skill_gap_result = await analyze_skill_gap(
        job_profile_id=job_profile_id,
        user_id=user_id,
        db=db,
    )

    # Sprint 8B.1: Retrieve similar approved bullets for learning
    similar_approved_bullets = []
    if enable_learning:
        try:
            from services.embeddings import create_embedding_service
            from services.vector_store import create_vector_store

            embedding_service = create_embedding_service(use_mock=False)
            vector_store = create_vector_store(use_mock=False)

            similar_approved_bullets = await retrieve_similar_bullets(
                job_profile=job_profile,
                embedding_service=embedding_service,
                vector_store=vector_store,
                user_id=user_id,
                limit=5,
                min_quality_score=0.70
            )

            if similar_approved_bullets:
                logger.info(f"Retrieved {len(similar_approved_bullets)} similar approved bullets for job {job_profile_id}")
        except Exception as e:
            logger.warning(f"Failed to retrieve similar approved bullets (continuing without): {e}")

    # Select bullets for each role
    selected_roles: List[SelectedRole] = []
    role_emphasis: Dict[int, str] = {}

    for experience in experiences:
        # Get bullets for this experience
        exp_bullets = [b for b in all_bullets if b.experience_id == experience.id]

        if not exp_bullets and not experience.engagements:
            # Skip experiences with no bullets and no engagements
            continue

        # Determine if this is a consulting role with engagements
        selected_engagements = []
        direct_bullets = []

        if experience.engagements:
            # This is a consulting role - select engagements and their bullets
            eng_list = select_engagements_for_experience(
                experience=experience,
                job_profile=job_profile,
                max_engagements=3
            )

            for eng in eng_list:
                # Get bullets for this engagement
                eng_bullets = [b for b in all_bullets if b.engagement_id == eng.id]

                if not eng_bullets:
                    continue

                # Select best bullets for this engagement
                selected_eng_bullets = select_bullets_for_role(
                    experience=experience,
                    bullets=eng_bullets,
                    job_profile=job_profile,
                    skill_gap_result=skill_gap_result,
                    max_bullets=3,  # Fewer bullets per engagement
                )

                if selected_eng_bullets:
                    selected_engagements.append(SelectedEngagement(
                        engagement_id=eng.id,
                        client=eng.client,
                        project_name=eng.project_name,
                        # Note: date_range_label omitted for cleaner engagement display
                        selected_bullets=selected_eng_bullets
                    ))

            # For consulting roles, bullets come from engagements, not directly
            direct_bullets = []
        else:
            # Non-consulting role - use direct bullets
            direct_bullets = select_bullets_for_role(
                experience=experience,
                bullets=exp_bullets,
                job_profile=job_profile,
                skill_gap_result=skill_gap_result,
                max_bullets=max_bullets_per_role,
            )

        # Skip if we have neither direct bullets nor engagements
        if not direct_bullets and not selected_engagements:
            continue

        # Build rationale for this role
        if direct_bullets:
            bullet_reasons = [sb.selection_reason for sb in direct_bullets]
            role_rationale = (
                f"Selected {len(direct_bullets)} bullets emphasizing: "
                f"{'; '.join(set([r.split(';')[0] for r in bullet_reasons]))}"
            )
        elif selected_engagements:
            total_bullets = sum(len(eng.selected_bullets) for eng in selected_engagements)
            role_rationale = (
                f"Selected {len(selected_engagements)} engagements with {total_bullets} total bullets "
                f"for consulting role"
            )
        else:
            role_rationale = "No bullets selected"

        # Determine role emphasis
        if experience.start_date and experience.end_date:
            months_ago = (datetime.now().date() - experience.end_date).days / 30
            if months_ago < 24:
                emphasis = "Recent relevant experience"
            else:
                emphasis = "Earlier career foundation"
        else:
            emphasis = "Current role (high priority)"

        role_emphasis[experience.id] = emphasis

        # Build selected role
        selected_roles.append(SelectedRole(
            experience_id=experience.id,
            job_title=experience.job_title,  # IMMUTABLE
            employer_name=experience.employer_name,  # IMMUTABLE
            location=experience.location,  # IMMUTABLE
            start_date=experience.start_date.isoformat(),
            end_date=experience.end_date.isoformat() if experience.end_date else None,
            employer_type=experience.employer_type,
            role_summary=experience.role_summary,  # "Focused on..." line
            selected_bullets=direct_bullets,
            selected_engagements=selected_engagements,
            bullet_selection_rationale=role_rationale,
        ))

    # Apply bullet rewriting if enabled
    if enable_bullet_rewriting and llm_client:
        # Build bullets_db lookup for all bullets
        all_bullet_ids = set()
        for role in selected_roles:
            for bullet in role.selected_bullets:
                all_bullet_ids.add(bullet.bullet_id)
            for eng in role.selected_engagements:
                for bullet in eng.selected_bullets:
                    all_bullet_ids.add(bullet.bullet_id)

        # Fetch actual Bullet objects for STAR notes and version history
        bullets_db_query = db.query(Bullet).filter(Bullet.id.in_(all_bullet_ids)).all()
        bullets_db = {b.id: b for b in bullets_db_query}

        # Build examples context from approved bullets (Sprint 8B.1)
        examples_context = ""
        if similar_approved_bullets:
            examples_context = format_examples_for_prompt(
                similar_outputs=similar_approved_bullets,
                max_examples=3,
                include_quality_score=True
            )

        # Rewrite bullets for each role
        for role in selected_roles:
            if role.selected_bullets:
                role.selected_bullets = await rewrite_bullets_for_job(
                    selected_bullets=role.selected_bullets,
                    job_profile=job_profile,
                    llm_client=llm_client,
                    db=db,
                    bullets_db=bullets_db,
                    strategy=rewrite_strategy or "both",
                    examples_context=examples_context
                )

            # Rewrite bullets within engagements
            for eng in role.selected_engagements:
                if eng.selected_bullets:
                    eng.selected_bullets = await rewrite_bullets_for_job(
                        selected_bullets=eng.selected_bullets,
                        job_profile=job_profile,
                        llm_client=llm_client,
                        db=db,
                        bullets_db=bullets_db,
                        strategy=rewrite_strategy or "both",
                        examples_context=examples_context
                    )

    # Select and order skills
    selected_skills = select_and_order_skills(
        user_bullets=all_bullets,
        job_profile=job_profile,
        skill_gap_result=skill_gap_result,
        max_skills=max_skills,
    )

    # Generate tailored summary using SummaryRewriteService (PRD 2.10)
    if llm is None:
        from services.llm.mock_llm import MockLLM
        llm = MockLLM()

    # Note: CompanyProfile integration will be added when Sprint 11-14 implements it
    # For now, company_profile is None - the service handles this gracefully
    # Sprint 8B.8: Pass context_notes (custom_instructions) to summary rewrite
    tailored_summary = await rewrite_summary_for_job(
        user=user,
        job_profile=job_profile,
        skill_gap_result=skill_gap_result,
        selected_skills=selected_skills,
        experiences=experiences,
        llm=llm,
        company_profile=None,  # TODO: Fetch from db when company enrichment is implemented
        max_words=60,  # PRD 2.10 default
        context_notes=custom_instructions,  # Sprint 8B.8: Thread context_notes
    )

    # ==========================================================================
    # SPRINT 8C.5: PAGINATION-AWARE BULLET ALLOCATION
    # ==========================================================================
    if enable_pagination_aware and selected_roles:
        pagination_service = PaginationService()
        page_simulator = PageSplitSimulator(pagination_service)

        # Estimate summary and skills lines
        summary_lines = pagination_service.estimate_summary_lines(tailored_summary) if tailored_summary else 0
        skills_lines = pagination_service.estimate_skills_lines([s.skill for s in selected_skills])

        # Build roles structure for simulation
        role_structures = []
        for role in selected_roles:
            bullets_info = []
            for bullet in role.selected_bullets:
                line_cost = pagination_service.estimate_bullet_lines(bullet.text)
                bullets_info.append({'text': bullet.text, 'lines': line_cost})

            role_structures.append({
                'experience_id': role.experience_id,
                'job_header_lines': pagination_service.get_job_header_lines(),
                'bullets': bullets_info
            })

        # Simulate page layout
        layout = page_simulator.simulate_page_layout(summary_lines, skills_lines, role_structures)

        # If layout overflows, apply condensation strategy
        if not layout.fits_in_budget:
            # Get condensation suggestions for older roles
            config = pagination_service._config
            min_bullets = config.get('min_bullets_per_role', 2)
            overflow_lines = layout.total_lines - pagination_service.get_total_budget()

            if config.get('condense_older_roles', True) and overflow_lines > 0:
                condensation_suggestions = page_simulator.suggest_condensation(
                    role_structures,
                    target_reduction_lines=overflow_lines,
                    min_bullets_per_role=min_bullets
                )

                # Apply condensation by trimming bullets from suggested roles
                for suggestion in condensation_suggestions:
                    role_idx = suggestion.get('role_index')
                    target_bullet_count = suggestion.get('suggested_bullets', 0)

                    # Validate suggestion values
                    if role_idx is None or not isinstance(role_idx, int):
                        continue
                    if target_bullet_count <= 0:
                        continue
                    if role_idx < 0 or role_idx >= len(selected_roles):
                        continue

                    role = selected_roles[role_idx]
                    if len(role.selected_bullets) > target_bullet_count:
                        # Keep highest-scoring bullets
                        role.selected_bullets = sorted(
                            role.selected_bullets,
                            key=lambda b: b.relevance_score,
                            reverse=True
                        )[:target_bullet_count]

                # Log condensation action
                logger.info(
                    f"Pagination-aware condensation applied: reduced {len(condensation_suggestions)} "
                    f"role(s) to fit 2-page budget"
                )

    # Build comprehensive rationale
    # Calculate total bullets across direct bullets and engagement bullets
    total_bullets = sum(len(r.selected_bullets) for r in selected_roles)
    total_bullets += sum(
        sum(len(eng.selected_bullets) for eng in r.selected_engagements)
        for r in selected_roles
    )

    # Extract candidate identity for rationale
    candidate_identity = 'Professional'
    if user.candidate_profile and user.candidate_profile.get('primary_identity'):
        candidate_identity = user.candidate_profile['primary_identity']

    rationale = TailoringRationale(
        summary_approach=(
            f"Rewritten summary positioning candidate as '{candidate_identity}', "
            f"emphasizing specializations aligned to job priorities: "
            f"{', '.join(job_profile.core_priorities[:3]) if job_profile.core_priorities else 'N/A'}. "
            f"Top skills highlighted: {', '.join([s.skill for s in selected_skills[:3]])}"
        ),
        bullet_selection_strategy=(
            f"Multi-factor scoring (40% tag matching, 30% relevance, 20% freshness, 10% diversity). "
            f"Sprint 8B.3: Added positioning alignment bonus and user advantage bonus. "
            f"Selected {total_bullets} total bullets "
            f"across {len(selected_roles)} roles, prioritizing matched skills: "
            f"{', '.join(skill_gap_result.bullet_selection_guidance.get('prioritize_tags', [])[:5])}. "
            f"Key positioning angles: {', '.join(skill_gap_result.key_positioning_angles[:2]) if skill_gap_result.key_positioning_angles else 'N/A'}"
        ),
        skills_ordering_logic=(
            f"Tier-based selection: Tier 1 (critical matches), Tier 2 (strong matches), "
            f"Tier 3 (must-have requirements), Tier 4 (transferable skills). "
            f"Selected {len(selected_skills)} skills with {len([s for s in selected_skills if s.match_type == 'direct_match'])} "
            f"direct matches"
        ),
        role_emphasis=role_emphasis,
        gaps_addressed=[
            f"{gap.skill} ({gap.importance}): {gap.positioning_strategy[:100]}..."
            for gap in skill_gap_result.skill_gaps[:3]
        ],
        strengths_highlighted=[
            f"{match.skill} (strength: {match.match_strength:.2f})"
            for match in sorted(skill_gap_result.matched_skills, key=lambda m: m.match_strength, reverse=True)[:5]
        ],
    )

    # Calculate match score (use skill gap score + adjustments)
    base_match_score = skill_gap_result.skill_match_score

    # Bonus for having enough bullets and skills (use total_bullets calculated earlier)
    content_bonus = 0.0
    if len(selected_roles) >= 2 and total_bullets >= 8:
        content_bonus += 5.0
    if len(selected_skills) >= max_skills * 0.8:
        content_bonus += 3.0

    match_score = min(base_match_score + content_bonus, 100.0)

    # Validate constraints
    constraints_validated = True
    for role in selected_roles:
        # Check immutable fields are preserved
        exp = next((e for e in experiences if e.id == role.experience_id), None)
        if exp:
            if role.job_title != exp.job_title:
                constraints_validated = False
            if role.employer_name != exp.employer_name:
                constraints_validated = False
            if role.location != exp.location:
                constraints_validated = False

        # Check bullet count constraint
        if len(role.selected_bullets) > max_bullets_per_role:
            constraints_validated = False

    # Check skills count constraint
    if len(selected_skills) > max_skills:
        constraints_validated = False

    # Build skill gap summary for response
    skill_gap_summary = {
        'skill_match_score': skill_gap_result.skill_match_score,
        'recommendation': skill_gap_result.recommendation,
        'confidence': skill_gap_result.confidence,
        'matched_skills_count': len(skill_gap_result.matched_skills),
        'skill_gaps_count': len(skill_gap_result.skill_gaps),
        'critical_gaps_count': len([g for g in skill_gap_result.skill_gaps if g.importance == 'critical']),
        'weak_signals_count': len(skill_gap_result.weak_signals),
        'key_positioning_angles': skill_gap_result.key_positioning_angles[:3],
        'top_matched_skills': [m.skill for m in skill_gap_result.matched_skills[:5]],
        'critical_gaps': [g.skill for g in skill_gap_result.skill_gaps if g.importance == 'critical'][:3],
    }

    # Build final response
    return TailoredResume(
        job_profile_id=job_profile_id,
        user_id=user_id,
        application_id=None,  # Not linked to application yet
        tailored_summary=tailored_summary,
        selected_roles=selected_roles,
        selected_skills=selected_skills,
        rationale=rationale,
        skill_gap_summary=skill_gap_summary,
        ats_score_estimate=None,  # TODO: Implement ATS scoring
        match_score=round(match_score, 1),
        generated_at=datetime.utcnow().isoformat(),
        constraints_validated=constraints_validated,
    )


async def tailor_resume_with_critic(
    job_profile_id: int,
    user_id: int,
    db: Session,
    max_bullets_per_role: int = 4,
    max_skills: int = 12,
    custom_instructions: Optional[str] = None,
    llm: Optional[BaseLLM] = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    strict_mode: bool = False,
) -> Tuple[TailoredResume, "ResumeCriticResult"]:
    """
    Generate tailored resume with critic-in-the-loop evaluation.

    Implements PRD 4.1-4.5 critic loop:
    1. Generate tailored resume
    2. Run resume critic evaluation
    3. If critic fails, adjust parameters and regenerate (up to max_iterations)
    4. Return best result with critic evaluation

    Adjustment strategy on failure:
    - Iteration 2: Expand bullet selection, prioritize metrics
    - Iteration 3: Relax constraints, focus on must-have requirements

    Args:
        job_profile_id: ID of target job profile
        user_id: User ID
        db: Database session
        max_bullets_per_role: Maximum bullets per experience (2-8)
        max_skills: Maximum skills in skills section (5-20)
        custom_instructions: Optional user instructions for tailoring
        llm: Optional LLM instance
        max_iterations: Maximum critic iterations (default 3)
        strict_mode: If True, treat warnings as errors

    Returns:
        Tuple of (TailoredResume, ResumeCriticResult)

    Raises:
        ValueError: If job profile or user not found
    """
    from schemas.critic import ResumeCriticResult
    from services.critic import evaluate_resume

    # Fetch job profile for critic
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile:
        raise ValueError(f"Job profile {job_profile_id} not found")

    best_resume: Optional[TailoredResume] = None
    best_critic_result: Optional[ResumeCriticResult] = None
    best_quality_score: float = 0.0

    for iteration in range(1, max_iterations + 1):
        # Adjust parameters based on iteration
        iter_max_bullets = max_bullets_per_role
        iter_max_skills = max_skills
        iter_instructions = custom_instructions

        if iteration == 2:
            # Expand bullet selection on second attempt
            iter_max_bullets = min(max_bullets_per_role + 1, 8)
            iter_instructions = (
                f"{custom_instructions or ''} "
                f"Focus on bullets with quantifiable metrics and strong action verbs. "
                f"Prioritize achievement statements."
            ).strip()

        elif iteration == 3:
            # Final attempt: maximize coverage
            iter_max_bullets = min(max_bullets_per_role + 2, 8)
            iter_max_skills = min(max_skills + 2, 20)
            iter_instructions = (
                f"{custom_instructions or ''} "
                f"Maximize coverage of must-have requirements. "
                f"Include all high-impact achievements with metrics."
            ).strip()

        # Generate tailored resume
        try:
            resume = await tailor_resume(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                max_bullets_per_role=iter_max_bullets,
                max_skills=iter_max_skills,
                custom_instructions=iter_instructions,
                llm=llm,
            )
        except ValueError as e:
            # Re-raise validation errors
            raise

        # Run critic evaluation
        resume_dict = resume.model_dump()
        critic_result = await evaluate_resume(
            resume_json=resume_dict,
            job_profile=job_profile,
            db=db,
            user_id=user_id,
            llm=llm,
            strict_mode=strict_mode,
            iteration=iteration,
        )

        # Track best result
        if critic_result.quality_score > best_quality_score:
            best_quality_score = critic_result.quality_score
            best_resume = resume
            best_critic_result = critic_result

        # If passed, return immediately
        if critic_result.passed:
            return resume, critic_result

        # Log iteration for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Resume critic iteration {iteration}/{max_iterations}: "
            f"passed={critic_result.passed}, "
            f"errors={critic_result.error_count}, "
            f"warnings={critic_result.warning_count}, "
            f"quality={critic_result.quality_score}"
        )

        # Check if we should continue
        if not critic_result.should_retry:
            break

    # Return best result (even if not passing)
    if best_resume is None or best_critic_result is None:
        # This shouldn't happen, but handle edge case
        raise ValueError("Failed to generate any resume")

    return best_resume, best_critic_result


async def log_critic_result(
    db: Session,
    application_id: Optional[int],
    critic_result: "ResumeCriticResult",
    resume_json: Dict,
) -> None:
    """
    Log critic evaluation result to database for tracking and analysis.

    Stores the critic result in the application's critic_scores field
    and creates a log entry for auditing.

    Args:
        db: Database session
        application_id: Application ID (if linked)
        critic_result: Critic evaluation result
        resume_json: Resume JSON that was evaluated
    """
    from db.models import Application, LogEntry

    if application_id:
        # Update application with critic scores
        application = db.query(Application).filter(
            Application.id == application_id
        ).first()

        if application:
            # Merge critic scores into existing scores
            existing_scores = application.critic_scores or {}
            existing_scores['resume'] = {
                'passed': critic_result.passed,
                'quality_score': critic_result.quality_score,
                'alignment_score': critic_result.alignment_score,
                'clarity_score': critic_result.clarity_score,
                'impact_score': critic_result.impact_score,
                'tone_score': critic_result.tone_score,
                'ats_overall': critic_result.ats_score.overall_score,
                'error_count': critic_result.error_count,
                'warning_count': critic_result.warning_count,
                'iteration': critic_result.iteration,
                'evaluated_at': critic_result.evaluated_at,
            }
            application.critic_scores = existing_scores
            application.ats_score = critic_result.ats_score.overall_score

            # Create log entry
            log_entry = LogEntry(
                user_id=application.user_id,
                application_id=application_id,
                action='resume_critic',
                details={
                    'passed': critic_result.passed,
                    'quality_score': critic_result.quality_score,
                    'iteration': critic_result.iteration,
                    'issues_count': len(critic_result.issues),
                    'summary': critic_result.evaluation_summary,
                },
            )
            db.add(log_entry)
            db.commit()


def get_critic_feedback_for_revision(
    critic_result: "ResumeCriticResult"
) -> Dict[str, Any]:
    """
    Extract actionable feedback from critic result for resume revision.

    Converts critic issues into structured guidance for the next
    tailoring iteration.

    Args:
        critic_result: Critic evaluation result

    Returns:
        Dict with revision guidance:
        - priority_fixes: List of blocking issues to fix
        - suggestions: List of non-blocking improvements
        - weak_areas: Areas needing attention
        - strong_areas: Areas performing well
    """
    priority_fixes = []
    suggestions = []
    weak_areas = []
    strong_areas = []

    # Categorize issues
    for issue in critic_result.issues:
        if issue.severity == 'error':
            priority_fixes.append({
                'type': issue.issue_type,
                'section': issue.section,
                'message': issue.message,
                'fix': issue.recommended_fix,
            })
        elif issue.severity == 'warning':
            suggestions.append({
                'type': issue.issue_type,
                'section': issue.section,
                'message': issue.message,
                'fix': issue.recommended_fix,
            })

    # Identify weak areas based on scores
    if critic_result.alignment_score < 70:
        weak_areas.append('JD alignment - missing key requirements')
    if critic_result.clarity_score < 70:
        weak_areas.append('Bullet clarity - restructure for conciseness')
    if critic_result.impact_score < 50:
        weak_areas.append('Impact orientation - add more metrics and achievements')
    if critic_result.tone_score < 80:
        weak_areas.append('Tone - adjust to be more professional/executive')

    # Identify strong areas
    if critic_result.alignment_score >= 85:
        strong_areas.append(f'Strong JD alignment ({critic_result.alignment_score})')
    if critic_result.clarity_score >= 85:
        strong_areas.append(f'Clear and concise bullets ({critic_result.clarity_score})')
    if critic_result.impact_score >= 70:
        strong_areas.append(f'Good impact orientation ({critic_result.impact_score})')
    if critic_result.ats_score.overall_score >= 80:
        strong_areas.append(f'Strong ATS score ({critic_result.ats_score.overall_score})')

    return {
        'priority_fixes': priority_fixes,
        'suggestions': suggestions[:5],  # Limit to top 5
        'weak_areas': weak_areas,
        'strong_areas': strong_areas,
        'metrics_coverage': f"{critic_result.bullets_with_metrics}/{critic_result.bullets_total} bullets with metrics",
        'weak_verb_count': critic_result.weak_verb_count,
    }
