"""
Portfolio Loader Service

Loads and provides access to user portfolio data from the JSON file.
Supports filtering, searching, and structured access patterns for
resume tailoring and skill-gap analysis services.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default portfolio path
DEFAULT_PORTFOLIO_PATH = Path(__file__).parent.parent.parent / "docs" / "user_portfolio.json"

# Cached portfolio data (simple in-memory cache)
_portfolio_cache: Optional[dict] = None
_cache_timestamp: Optional[datetime] = None
CACHE_TTL_SECONDS = 300  # 5 minutes


VALID_SENIORITY_LEVELS = {'director', 'senior_ic', 'mid_level'}
VALID_BULLET_TYPES = {'achievement', 'responsibility', 'metric_impact'}


def load_user_portfolio(portfolio_path: Optional[Path] = None, force_reload: bool = False) -> dict:
    """
    Load user portfolio from JSON file.

    Uses an in-memory cache with a 5-minute TTL to avoid repeated file reads.

    Args:
        portfolio_path: Optional custom path to portfolio JSON file.
                       Defaults to docs/user_portfolio.json.
        force_reload: If True, bypasses cache and reloads from disk.

    Returns:
        dict: Complete portfolio data including user, experiences,
              education, technical_skills, and metadata.

    Raises:
        FileNotFoundError: If portfolio JSON file doesn't exist.
        json.JSONDecodeError: If JSON is malformed.
        ValueError: If portfolio structure is invalid.

    Example:
        >>> portfolio = load_user_portfolio()
        >>> print(portfolio['user']['full_name'])
        'Benjamin Black'
    """
    global _portfolio_cache, _cache_timestamp

    path = portfolio_path or DEFAULT_PORTFOLIO_PATH

    # Check cache validity
    if not force_reload and _portfolio_cache is not None and _cache_timestamp is not None:
        age = (datetime.now() - _cache_timestamp).total_seconds()
        if age < CACHE_TTL_SECONDS:
            logger.debug(f"Returning cached portfolio (age: {age:.1f}s)")
            return _portfolio_cache

    # Load from disk
    if not path.exists():
        raise FileNotFoundError(
            f"Portfolio file not found at {path}. "
            f"Expected location: {DEFAULT_PORTFOLIO_PATH}"
        )

    logger.info(f"Loading portfolio from {path}")

    with open(path, 'r', encoding='utf-8') as f:
        portfolio = json.load(f)

    # Basic structure validation
    required_keys = ['user', 'experiences', 'education', 'technical_skills', 'metadata']
    for key in required_keys:
        if key not in portfolio:
            raise ValueError(
                f"Portfolio structure invalid: missing required key '{key}'. "
                f"Expected keys: {', '.join(required_keys)}"
            )

    # Validate bullet data
    _validate_bullets(portfolio)

    # Update cache
    _portfolio_cache = portfolio
    _cache_timestamp = datetime.now()

    return portfolio


def _validate_bullets(portfolio: dict) -> None:
    """Validate bullet data structure and enum values."""
    for exp in portfolio.get('experiences', []):
        # Direct bullets
        for bullet in exp.get('bullets', []):
            _validate_single_bullet(bullet, exp.get('id', 'unknown'))

        # Sub-engagement bullets
        for sub in exp.get('sub_engagements', []):
            for bullet in sub.get('bullets', []):
                _validate_single_bullet(bullet, f"{exp.get('id', 'unknown')}/{sub.get('id', 'unknown')}")


def _validate_single_bullet(bullet: dict, context: str) -> None:
    """Validate a single bullet's required fields and enum values."""
    bullet_id = bullet.get('id', 'unknown')

    # Check seniority_level
    seniority = bullet.get('seniority_level')
    if seniority not in VALID_SENIORITY_LEVELS:
        raise ValueError(
            f"Bullet {bullet_id} in {context}: invalid seniority_level '{seniority}'. "
            f"Valid values: {VALID_SENIORITY_LEVELS}"
        )

    # Check bullet_type
    bullet_type = bullet.get('bullet_type')
    if bullet_type not in VALID_BULLET_TYPES:
        raise ValueError(
            f"Bullet {bullet_id} in {context}: invalid bullet_type '{bullet_type}'. "
            f"Valid values: {VALID_BULLET_TYPES}"
        )

    # Check relevance_scores are valid floats in [0, 1]
    for category, score in bullet.get('relevance_scores', {}).items():
        if not isinstance(score, (int, float)) or not (0.0 <= score <= 1.0):
            raise ValueError(
                f"Bullet {bullet_id} in {context}: invalid relevance score "
                f"for '{category}': {score}. Must be float in [0.0, 1.0]"
            )


def get_all_bullets(include_sub_engagements: bool = True) -> list[dict]:
    """
    Get all bullets from all experiences.

    Args:
        include_sub_engagements: If True, includes bullets from
                                 sub-engagements (e.g., consulting clients).

    Returns:
        list[dict]: List of all bullet dictionaries with experience context.

    Example:
        >>> bullets = get_all_bullets()
        >>> print(len(bullets))  # Total bullet count
    """
    portfolio = load_user_portfolio()
    all_bullets = []

    for exp in portfolio.get('experiences', []):
        exp_context = {
            'experience_id': exp.get('id'),
            'employer_name': exp.get('employer_name'),
            'job_title': exp.get('job_title'),
            'start_date': exp.get('start_date'),
            'end_date': exp.get('end_date')
        }

        # Direct bullets
        for bullet in exp.get('bullets', []):
            all_bullets.append({**bullet, 'experience': exp_context})

        # Sub-engagement bullets
        if include_sub_engagements:
            for sub in exp.get('sub_engagements', []):
                sub_context = {
                    **exp_context,
                    'client_name': sub.get('client_name'),
                    'sub_start_date': sub.get('start_date'),
                    'sub_end_date': sub.get('end_date')
                }
                for bullet in sub.get('bullets', []):
                    all_bullets.append({**bullet, 'experience': sub_context})

    return all_bullets


def get_bullets_by_tags(
    tags: list[str],
    match_all: bool = False,
    min_relevance: Optional[float] = None,
    relevance_category: Optional[str] = None
) -> list[dict]:
    """
    Filter bullets by tags and optional relevance threshold.

    Args:
        tags: List of tags to filter by.
        match_all: If True, bullet must have ALL tags (AND logic).
                   If False, bullet must have ANY tag (OR logic).
        min_relevance: Minimum relevance score threshold (0.0-1.0).
        relevance_category: Category to check for min_relevance
                           (e.g., 'ai_governance', 'consulting').

    Returns:
        list[dict]: List of matching bullet dictionaries.

    Example:
        >>> bullets = get_bullets_by_tags(['data_governance', 'consulting'], min_relevance=0.8)
        >>> print(len(bullets))
    """
    all_bullets = get_all_bullets()
    matching = []

    for bullet in all_bullets:
        bullet_tags = set(bullet.get('tags', []))
        search_tags = set(tags)

        # Tag matching
        if match_all:
            if not search_tags.issubset(bullet_tags):
                continue
        else:
            if not search_tags.intersection(bullet_tags):
                continue

        # Relevance filtering
        if min_relevance is not None and relevance_category is not None:
            scores = bullet.get('relevance_scores', {})
            if scores.get(relevance_category, 0) < min_relevance:
                continue

        matching.append(bullet)

    return matching


def get_bullets_by_type(bullet_type: str) -> list[dict]:
    """
    Get bullets by type (achievement, responsibility, metric_impact).

    Args:
        bullet_type: One of 'achievement', 'responsibility', 'metric_impact'.

    Returns:
        list[dict]: List of matching bullet dictionaries.

    Example:
        >>> achievements = get_bullets_by_type('achievement')
        >>> metrics = get_bullets_by_type('metric_impact')
    """
    all_bullets = get_all_bullets()
    return [b for b in all_bullets if b.get('bullet_type') == bullet_type]


def get_bullets_by_seniority(seniority_level: str) -> list[dict]:
    """
    Get bullets by seniority level.

    Args:
        seniority_level: One of 'director', 'senior_ic', 'mid_level'.

    Returns:
        list[dict]: List of matching bullet dictionaries.
    """
    all_bullets = get_all_bullets()
    return [b for b in all_bullets if b.get('seniority_level') == seniority_level]


def get_experiences_by_date_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list[dict]:
    """
    Get experiences within a date range.

    Args:
        start_date: ISO date string (YYYY-MM or YYYY-MM-DD).
                   Experiences ending after this date are included.
        end_date: ISO date string (YYYY-MM or YYYY-MM-DD).
                 Experiences starting before this date are included.

    Returns:
        list[dict]: List of experience dictionaries within range.

    Example:
        >>> recent = get_experiences_by_date_range(start_date='2020-01')
        >>> older = get_experiences_by_date_range(end_date='2015-12')
    """
    portfolio = load_user_portfolio()
    matching = []

    def parse_date(date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        # Normalize to YYYY-MM format
        return date_str[:7] if len(date_str) >= 7 else date_str

    for exp in portfolio.get('experiences', []):
        exp_start = parse_date(exp.get('start_date'))
        exp_end = parse_date(exp.get('end_date'))

        # Handle ongoing roles (no end date)
        if exp_end is None:
            exp_end = datetime.now().strftime('%Y-%m')

        # Check range overlap
        if start_date and exp_end < start_date:
            continue
        if end_date and exp_start > end_date:
            continue

        matching.append(exp)

    return matching


def get_skills_by_category(category: str) -> list[str]:
    """
    Get skills from a specific category.

    Args:
        category: Skill category key from technical_skills.
                 One of: 'ai_ml', 'data', 'tech', 'bi', 'tools'.

    Returns:
        list[str]: List of skills in that category.

    Example:
        >>> ai_skills = get_skills_by_category('ai_ml')
        >>> print(ai_skills)
        ['RAG', 'vector search', 'embeddings', ...]
    """
    portfolio = load_user_portfolio()
    skills = portfolio.get('technical_skills', {})
    return skills.get(category, [])


def get_all_skills() -> dict[str, list[str]]:
    """
    Get all technical skills organized by category.

    Returns:
        dict[str, list[str]]: Dictionary of category -> skills list.
    """
    portfolio = load_user_portfolio()
    return portfolio.get('technical_skills', {})


def get_all_skill_names() -> list[str]:
    """
    Get flat list of all skill names across all categories.

    Returns:
        list[str]: Deduplicated list of all skill names.
    """
    skills = get_all_skills()
    all_names = []
    for category_skills in skills.values():
        all_names.extend(category_skills)
    return list(set(all_names))


def get_extracted_skills_from_bullets() -> list[str]:
    """
    Get all skills mentioned in bullet extracted_skills fields.

    Returns:
        list[str]: Deduplicated list of skills from bullets.
    """
    all_bullets = get_all_bullets()
    skills = set()
    for bullet in all_bullets:
        for skill in bullet.get('extracted_skills', []):
            skills.add(skill)
    return list(skills)


def search_bullets(query: str, top_k: int = 10) -> list[dict]:
    """
    Search bullets by text content (simple substring matching).

    For production use, this should be replaced with embedding-based
    semantic search via Qdrant or similar vector store.

    Args:
        query: Search query string.
        top_k: Maximum number of results to return.

    Returns:
        list[dict]: List of matching bullets, sorted by relevance.

    Example:
        >>> results = search_bullets('data governance', top_k=5)
    """
    all_bullets = get_all_bullets()
    query_lower = query.lower()
    query_terms = query_lower.split()

    scored = []
    for bullet in all_bullets:
        text_lower = bullet.get('text', '').lower()

        # Simple scoring: count query term occurrences
        score = 0
        for term in query_terms:
            if term in text_lower:
                score += 1

        # Boost for tag matches
        tags = [t.lower().replace('_', ' ') for t in bullet.get('tags', [])]
        for term in query_terms:
            if any(term in tag for tag in tags):
                score += 0.5

        if score > 0:
            scored.append((score, bullet))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    return [item[1] for item in scored[:top_k]]


def get_user_info() -> dict:
    """
    Get user contact and summary information.

    Returns:
        dict: User info including full_name, email, phone, linkedin, summary.
    """
    portfolio = load_user_portfolio()
    return portfolio.get('user', {})


def get_education() -> list[dict]:
    """
    Get education entries.

    Returns:
        list[dict]: List of education dictionaries.
    """
    portfolio = load_user_portfolio()
    return portfolio.get('education', [])


def get_portfolio_for_tailoring() -> dict:
    """
    Get portfolio data structured for resume tailoring service.

    Returns a flattened view optimized for bullet selection and matching.

    Returns:
        dict: Portfolio data with:
            - user: Contact info
            - all_bullets: Flattened list of all bullets with experience context
            - skills: All technical skills
            - education: Education entries
    """
    portfolio = load_user_portfolio()

    return {
        'user': portfolio.get('user', {}),
        'all_bullets': get_all_bullets(),
        'skills': get_all_skills(),
        'skill_names': get_all_skill_names(),
        'education': portfolio.get('education', []),
        'experiences': portfolio.get('experiences', [])
    }


def get_portfolio_for_skill_gap() -> dict:
    """
    Get portfolio data structured for skill-gap analysis service.

    Returns data optimized for comparing user skills against job requirements.

    Returns:
        dict: Portfolio data with:
            - skills_by_category: Skills organized by category
            - all_skill_names: Flat list of all skill names
            - extracted_skills: Skills mentioned in bullets
            - bullet_tags: Set of all unique tags across bullets
    """
    all_bullets = get_all_bullets()

    # Collect all unique tags
    all_tags = set()
    for bullet in all_bullets:
        all_tags.update(bullet.get('tags', []))

    return {
        'skills_by_category': get_all_skills(),
        'all_skill_names': get_all_skill_names(),
        'extracted_skills': get_extracted_skills_from_bullets(),
        'bullet_tags': list(all_tags),
        'capabilities': list(all_tags)  # Tags represent capabilities
    }


def clear_cache() -> None:
    """
    Clear the in-memory portfolio cache.

    Call this after modifying the portfolio JSON file to ensure
    fresh data is loaded on next access.
    """
    global _portfolio_cache, _cache_timestamp
    _portfolio_cache = None
    _cache_timestamp = None
    logger.info("Portfolio cache cleared")
