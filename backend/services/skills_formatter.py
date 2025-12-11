"""
Skills Formatter Service

LLM-powered skills categorization with validation guardrails.
Prevents hallucinations by enforcing skills must exist in the allowed list
(user's master resume OR job description requirements).
"""

import json
import logging
from typing import List, Optional, Set

from db.models import JobProfile
from schemas.resume_tailor import SelectedSkill
from schemas.skills_formatter import (
    SkillCategory,
    SkillsFormatterResponse,
    SKILL_CATEGORIES,
    AdaptiveSkillCategory,
    ThreeCategoryFormatterResponse,
)
from services.llm.base import BaseLLM


logger = logging.getLogger(__name__)


def _normalize_skill_for_comparison(skill: str) -> str:
    """Normalize a skill string for comparison (lowercase, stripped)."""
    return skill.lower().strip()


def _build_allowed_skills_set(
    selected_skills: List[SelectedSkill],
    job_profile: Optional[JobProfile] = None
) -> Set[str]:
    """
    Build the set of allowed skills from selected skills and job profile.

    Only skills in this set can appear in the formatted output.

    Args:
        selected_skills: Skills selected for the resume
        job_profile: Optional job profile for additional allowed skills

    Returns:
        Set of normalized skill names that are allowed
    """
    allowed = set()

    # Add all selected skills
    for skill in selected_skills:
        allowed.add(_normalize_skill_for_comparison(skill.skill))

    # Add job profile skills if available
    if job_profile:
        if job_profile.extracted_skills:
            for skill in job_profile.extracted_skills:
                allowed.add(_normalize_skill_for_comparison(skill))
        if job_profile.must_have_capabilities:
            for skill in job_profile.must_have_capabilities:
                allowed.add(_normalize_skill_for_comparison(skill))

    return allowed


def _validate_llm_response(
    categories: List[SkillCategory],
    allowed_skills: Set[str]
) -> tuple[List[SkillCategory], List[str]]:
    """
    Validate LLM response and remove any hallucinated skills.

    Args:
        categories: Categories returned by LLM
        allowed_skills: Set of allowed skill names (normalized)

    Returns:
        Tuple of (validated categories, list of rejected skills)
    """
    validated_categories = []
    rejected_skills = []

    for category in categories:
        valid_skills = []
        for skill in category.skills:
            normalized = _normalize_skill_for_comparison(skill)
            if normalized in allowed_skills:
                valid_skills.append(skill)
            else:
                rejected_skills.append(skill)
                logger.warning(f"Rejected hallucinated skill: '{skill}'")

        # Only include category if it has valid skills
        if valid_skills:
            validated_categories.append(SkillCategory(
                category_name=category.category_name,
                skills=valid_skills
            ))

    return validated_categories, rejected_skills


def _fallback_categorization(
    selected_skills: List[SelectedSkill]
) -> List[SkillCategory]:
    """
    Fallback to simple keyword-based categorization.

    Used when LLM fails or returns invalid response.

    Args:
        selected_skills: Skills to categorize

    Returns:
        List of categorized skills using keyword matching
    """
    # Define category patterns - expanded to cover more domains
    category_patterns = {
        "AI/ML": ["ai", "ml", "machine learning", "deep learning", "nlp", "llm",
                  "rag", "vector", "embedding", "prompt", "neural", "transformer",
                  "generative", "gpt", "claude", "artificial intelligence", "copilot"],
        "Programming Languages & Frameworks": [
            "python", "sql", "r ", "java", "scala", "spark", "pandas",
            "numpy", "scikit", "tensorflow", "pytorch", "javascript", "typescript",
            "api", "integration"
        ],
        "Data Engineering & Analytics": [
            "data", "etl", "pipeline", "warehouse", "lake", "hadoop", "kafka",
            "snowflake", "databricks", "dbt", "airflow", "analytics", "segment"
        ],
        "Cloud & Infrastructure": [
            "aws", "azure", "gcp", "cloud", "docker",
            "kubernetes", "terraform", "devops", "ci/cd"
        ],
        "Payments & FinTech": [
            "payment", "fintech", "ach", "card", "pci", "nacha", "fraud",
            "billing", "wallet", "transaction", "merchant"
        ],
        "Governance & Strategy": [
            "governance", "strategy", "compliance", "policy", "risk",
            "framework", "architecture", "leadership", "management",
            "digital transformation", "transformation"
        ],
        "Business & Consulting": [
            "consulting", "business development", "use case", "marketing",
            "problem solving", "critical thinking", "workshop", "presentation",
            "stakeholder", "executive"
        ],
        "Visualization & BI": [
            "tableau", "power bi", "looker", "dashboard",
            "visualization", "reporting", "qlik", "miro", "visio"
        ],
    }

    categorized: dict[str, list[str]] = {}
    uncategorized: list[str] = []

    for skill in selected_skills:
        skill_lower = skill.skill.lower()
        matched = False

        for category, patterns in category_patterns.items():
            if any(pattern in skill_lower for pattern in patterns):
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(skill.skill)
                matched = True
                break

        if not matched:
            uncategorized.append(skill.skill)

    # Convert to SkillCategory objects
    result = []
    for category_name, skills in categorized.items():
        result.append(SkillCategory(
            category_name=category_name,
            skills=skills
        ))

    # Add uncategorized skills to "Other Technical Skills" if any
    if uncategorized:
        result.append(SkillCategory(
            category_name="Other Technical Skills",
            skills=uncategorized
        ))

    return result


async def format_skills_with_llm(
    selected_skills: List[SelectedSkill],
    llm: BaseLLM,
    job_profile: Optional[JobProfile] = None,
    job_title: Optional[str] = None
) -> SkillsFormatterResponse:
    """
    Format skills using LLM with validation guardrails.

    The LLM categorizes skills into logical groups, but all output
    is validated against the allowed skills list to prevent hallucinations.

    Args:
        selected_skills: Skills selected for the resume
        llm: LLM instance for categorization
        job_profile: Optional job profile for context and allowed skills
        job_title: Optional job title for context

    Returns:
        SkillsFormatterResponse with categorized and validated skills
    """
    if not selected_skills:
        return SkillsFormatterResponse(
            categories=[],
            validation_passed=True,
            validation_errors=[],
            fallback_used=False
        )

    # Build allowed skills set
    allowed_skills = _build_allowed_skills_set(selected_skills, job_profile)

    # Extract skill names for the prompt
    skill_names = [s.skill for s in selected_skills]

    # Build the prompt
    prompt = _build_categorization_prompt(
        skills=skill_names,
        job_title=job_title,
        categories=SKILL_CATEGORIES
    )

    try:
        # Call LLM
        response = await llm.generate_json(
            prompt=prompt,
            system_prompt=(
                "You are a resume skills formatter. Your job is to categorize "
                "skills into logical groups. You MUST only use skills from the "
                "provided list - do not invent or add any new skills. "
                "Return valid JSON only."
            )
        )

        # Parse LLM response
        categories = _parse_llm_response(response)

        if not categories:
            # LLM returned empty or invalid response, use fallback
            logger.warning("LLM returned empty/invalid response, using fallback")
            return SkillsFormatterResponse(
                categories=_fallback_categorization(selected_skills),
                validation_passed=True,
                validation_errors=[],
                fallback_used=True
            )

        # Validate response
        validated_categories, rejected_skills = _validate_llm_response(
            categories, allowed_skills
        )

        # Check if any skills were rejected
        validation_passed = len(rejected_skills) == 0

        if not validation_passed:
            logger.warning(
                f"LLM returned {len(rejected_skills)} invalid skills: {rejected_skills}"
            )

        # If all skills were rejected or no valid categories remain, use fallback
        if not validated_categories:
            logger.warning("All LLM categories were invalid, using fallback")
            return SkillsFormatterResponse(
                categories=_fallback_categorization(selected_skills),
                validation_passed=True,
                validation_errors=rejected_skills,
                fallback_used=True
            )

        return SkillsFormatterResponse(
            categories=validated_categories,
            validation_passed=validation_passed,
            validation_errors=rejected_skills,
            fallback_used=False
        )

    except Exception as e:
        logger.error(f"LLM skills formatting failed: {e}", exc_info=True)
        # Fall back to simple categorization
        return SkillsFormatterResponse(
            categories=_fallback_categorization(selected_skills),
            validation_passed=True,
            validation_errors=[],
            fallback_used=True
        )


def _build_categorization_prompt(
    skills: List[str],
    job_title: Optional[str],
    categories: List[str]
) -> str:
    """Build the prompt for LLM skills categorization."""
    skills_list = ", ".join(skills)
    categories_list = "\n".join(f"- {cat}" for cat in categories)

    job_context = f" for a {job_title} position" if job_title else ""

    return f"""Categorize the following skills{job_context}.

SKILLS TO CATEGORIZE:
{skills_list}

AVAILABLE CATEGORIES (use only these):
{categories_list}

RULES:
1. ONLY use skills from the list above - do not add or invent any new skills
2. Each skill should appear in exactly one category
3. Choose the most appropriate category for each skill
4. If a skill doesn't fit well into any category, put it in "Other Technical Skills"
5. Only include categories that have skills assigned to them

Return a JSON object with this structure:
{{
  "categories": [
    {{
      "category_name": "AI/ML",
      "skills": ["skill1", "skill2"]
    }},
    {{
      "category_name": "Programming Languages & Frameworks",
      "skills": ["skill3"]
    }}
  ]
}}

Return ONLY the JSON object, no other text."""


def _parse_llm_response(response: dict) -> List[SkillCategory]:
    """
    Parse LLM response into SkillCategory objects.

    Args:
        response: Raw response from LLM (should be dict with 'categories' key)

    Returns:
        List of SkillCategory objects
    """
    if not response:
        return []

    # Handle string response (shouldn't happen with generate_json but be safe)
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return []

    # Extract categories
    categories_data = response.get("categories", [])
    if not isinstance(categories_data, list):
        logger.error(f"Expected categories to be a list, got {type(categories_data)}")
        return []

    categories = []
    for cat_data in categories_data:
        if not isinstance(cat_data, dict):
            continue

        category_name = cat_data.get("category_name", "")
        skills = cat_data.get("skills", [])

        if not category_name or not isinstance(skills, list):
            continue

        # Filter out non-string skills
        valid_skills = [s for s in skills if isinstance(s, str) and s.strip()]

        if valid_skills:
            categories.append(SkillCategory(
                category_name=category_name,
                skills=valid_skills
            ))

    return categories


def format_skills_sync(
    selected_skills: List[SelectedSkill],
    job_profile: Optional[JobProfile] = None
) -> dict[str, list[str]]:
    """
    Synchronous fallback for skills formatting (no LLM).

    Used when async is not available or as a simple fallback.

    Args:
        selected_skills: Skills to categorize
        job_profile: Optional job profile (unused in fallback)

    Returns:
        Dict mapping category names to skill lists
    """
    categories = _fallback_categorization(selected_skills)
    return {cat.category_name: cat.skills for cat in categories}


# ============================================================================
# Role-Adaptive 3-Category Formatting (Approach 3)
# ============================================================================

def _build_three_category_prompt(
    skills: List[str],
    job_title: str
) -> str:
    """Build the prompt for 3-category adaptive formatting."""
    skills_list = ", ".join(skills)

    return f"""Format skills for a resume targeting the "{job_title}" position.

SKILLS TO CATEGORIZE:
{skills_list}

TASK: Organize these skills into EXACTLY 3 categories with smart, role-specific names.

REQUIREMENTS:
1. Create EXACTLY 3 category names that are:
   - Specific to the "{job_title}" role (not generic names like "Technical Skills")
   - Professional and concise (15-35 characters ideal, e.g., "Payments & FinTech", "AI & Strategy")
   - Descriptive of the skills grouped within them

2. Assign each skill to the most appropriate category
   - Each skill must appear in exactly ONE category
   - Use ONLY skills from the provided list - do NOT add or invent any skills

3. Order categories by relevance to "{job_title}":
   - relevance_rank=1: Most critical domain-specific skills for this role
   - relevance_rank=2: Supporting technical skills
   - relevance_rank=3: General/transferable professional skills

EXAMPLES:
- For "Senior Payments Engineer": "Payments & FinTech", "Cloud & Infrastructure", "Business & Tools"
- For "Data Scientist": "AI & Machine Learning", "Data Engineering", "Programming & Tools"
- For "Solution Consultant": "Industry Expertise", "Technical Skills", "Business Development"

Return ONLY a JSON object:
{{
  "categories": [
    {{"category_name": "Category Name Here", "skills": ["skill1", "skill2"], "relevance_rank": 1}},
    {{"category_name": "Second Category", "skills": ["skill3", "skill4"], "relevance_rank": 2}},
    {{"category_name": "Third Category", "skills": ["skill5"], "relevance_rank": 3}}
  ]
}}"""


def _fallback_three_categories(
    selected_skills: List[SelectedSkill],
    job_title: str
) -> ThreeCategoryFormatterResponse:
    """
    Fallback to simple 3-category grouping when LLM fails.

    Groups skills into:
    1. Domain/Role-Specific (based on job title keywords)
    2. Core Technical Skills
    3. General Professional Skills
    """
    job_lower = job_title.lower()

    # Determine domain category name based on job title
    if any(kw in job_lower for kw in ["payment", "fintech", "financial", "banking"]):
        domain_name = "Payments & FinTech"
        domain_keywords = ["payment", "fintech", "ach", "card", "pci", "nacha", "fraud", "billing"]
    elif any(kw in job_lower for kw in ["data", "scientist", "analytics", "ml", "ai"]):
        domain_name = "AI & Data Science"
        domain_keywords = ["ai", "ml", "machine learning", "data", "analytics", "nlp", "llm"]
    elif any(kw in job_lower for kw in ["consult", "solution", "architect"]):
        domain_name = "Industry Expertise"
        domain_keywords = ["consulting", "solution", "architecture", "strategy", "digital"]
    elif any(kw in job_lower for kw in ["engineer", "developer", "software"]):
        domain_name = "Software Engineering"
        domain_keywords = ["python", "java", "api", "cloud", "aws", "azure", "docker"]
    else:
        domain_name = "Core Expertise"
        domain_keywords = []

    # Technical skills keywords
    tech_keywords = [
        "python", "sql", "java", "cloud", "aws", "azure", "gcp", "docker",
        "kubernetes", "api", "data", "tableau", "power bi", "etl"
    ]

    # Categorize skills
    domain_skills = []
    tech_skills = []
    general_skills = []

    for skill in selected_skills:
        skill_lower = skill.skill.lower()
        if any(kw in skill_lower for kw in domain_keywords):
            domain_skills.append(skill.skill)
        elif any(kw in skill_lower for kw in tech_keywords):
            tech_skills.append(skill.skill)
        else:
            general_skills.append(skill.skill)

    # Ensure all categories have at least some skills by redistributing
    all_skills = [s.skill for s in selected_skills]
    if not domain_skills and all_skills:
        # Take first third of skills
        split = len(all_skills) // 3
        domain_skills = all_skills[:split] if split > 0 else all_skills[:1]
        remaining = all_skills[split:] if split > 0 else all_skills[1:]
        tech_skills = remaining[:len(remaining)//2]
        general_skills = remaining[len(remaining)//2:]

    # Handle edge cases
    if not tech_skills:
        tech_skills = ["Technical Skills"][:0]  # Empty list
    if not general_skills:
        general_skills = []

    categories = [
        AdaptiveSkillCategory(
            category_name=domain_name,
            skills=domain_skills if domain_skills else ["—"],
            relevance_rank=1
        ),
        AdaptiveSkillCategory(
            category_name="Technical Skills",
            skills=tech_skills if tech_skills else domain_skills[-1:] if domain_skills else ["—"],
            relevance_rank=2
        ),
        AdaptiveSkillCategory(
            category_name="Business & Tools",
            skills=general_skills if general_skills else ["—"],
            relevance_rank=3
        ),
    ]

    # Remove placeholder categories with only "—"
    final_categories = []
    remaining_skills = []
    for cat in categories:
        if cat.skills == ["—"]:
            remaining_skills.extend([])
        else:
            final_categories.append(cat)

    # Ensure exactly 3 categories by redistributing if needed
    if len(final_categories) < 3:
        # Simple redistribution - split the largest category
        while len(final_categories) < 3:
            largest = max(final_categories, key=lambda c: len(c.skills))
            if len(largest.skills) > 1:
                split_point = len(largest.skills) // 2
                new_skills = largest.skills[split_point:]
                largest.skills = largest.skills[:split_point]
                new_rank = max(c.relevance_rank for c in final_categories) + 1
                if new_rank > 3:
                    new_rank = 3
                final_categories.append(AdaptiveSkillCategory(
                    category_name=f"Additional Skills",
                    skills=new_skills,
                    relevance_rank=new_rank
                ))
            else:
                # Can't split further, add empty category
                final_categories.append(AdaptiveSkillCategory(
                    category_name="Other Skills",
                    skills=["—"],
                    relevance_rank=3
                ))

    # Ensure ranks are 1, 2, 3
    for i, cat in enumerate(final_categories[:3]):
        cat.relevance_rank = i + 1

    return ThreeCategoryFormatterResponse(
        categories=final_categories[:3],
        job_title=job_title,
        validation_passed=True,
        validation_errors=[],
        fallback_used=True
    )


def _parse_three_category_response(
    response: dict,
    allowed_skills: Set[str]
) -> tuple[List[AdaptiveSkillCategory], List[str]]:
    """
    Parse and validate LLM response for 3-category formatting.

    Returns:
        Tuple of (validated categories, rejected skills)
    """
    if not response:
        return [], []

    categories_data = response.get("categories", [])
    if not isinstance(categories_data, list):
        return [], []

    validated_categories = []
    rejected_skills = []

    for cat_data in categories_data:
        if not isinstance(cat_data, dict):
            continue

        category_name = cat_data.get("category_name", "")
        skills = cat_data.get("skills", [])
        relevance_rank = cat_data.get("relevance_rank", 1)

        if not category_name or not isinstance(skills, list):
            continue

        # Validate skills against allowed list
        valid_skills = []
        for skill in skills:
            if isinstance(skill, str) and skill.strip():
                normalized = _normalize_skill_for_comparison(skill)
                if normalized in allowed_skills:
                    valid_skills.append(skill)
                else:
                    rejected_skills.append(skill)
                    logger.warning(f"Rejected skill not in allowed list: '{skill}'")

        if valid_skills:
            # Ensure relevance_rank is valid
            rank = relevance_rank if isinstance(relevance_rank, int) and 1 <= relevance_rank <= 3 else 1

            validated_categories.append(AdaptiveSkillCategory(
                category_name=category_name[:40],  # Truncate if too long
                skills=valid_skills,
                relevance_rank=rank
            ))

    return validated_categories, rejected_skills


async def format_skills_three_categories(
    selected_skills: List[SelectedSkill],
    llm: BaseLLM,
    job_title: str,
    job_profile: Optional[JobProfile] = None
) -> ThreeCategoryFormatterResponse:
    """
    Format skills into exactly 3 role-adaptive categories using LLM.

    This is the primary function for Approach 3 (Hybrid) formatting.
    Generates smart category names based on the job title/type.

    Args:
        selected_skills: Skills selected for the resume
        llm: LLM instance for categorization
        job_title: Job title for context (e.g., "Senior Data Scientist")
        job_profile: Optional job profile for validation

    Returns:
        ThreeCategoryFormatterResponse with exactly 3 categories ordered by relevance
    """
    if not selected_skills:
        return ThreeCategoryFormatterResponse(
            categories=[
                AdaptiveSkillCategory(category_name="Skills", skills=[], relevance_rank=1),
                AdaptiveSkillCategory(category_name="Technical", skills=[], relevance_rank=2),
                AdaptiveSkillCategory(category_name="Tools", skills=[], relevance_rank=3),
            ],
            job_title=job_title,
            validation_passed=True,
            validation_errors=[],
            fallback_used=True
        )

    # Build allowed skills set for validation
    allowed_skills = _build_allowed_skills_set(selected_skills, job_profile)

    # Extract skill names for the prompt
    skill_names = [s.skill for s in selected_skills]

    # Build the prompt
    prompt = _build_three_category_prompt(skill_names, job_title)

    try:
        # Call LLM
        logger.info(f"Formatting {len(skill_names)} skills for job: {job_title}")
        response = await llm.generate_json(
            prompt=prompt,
            system_prompt=(
                "You are a professional resume skills formatter. Create exactly 3 skill "
                "categories with smart, role-specific names. Only use skills from the "
                "provided list - never add or invent new skills. Return valid JSON only."
            )
        )

        # Parse and validate response
        validated_categories, rejected_skills = _parse_three_category_response(
            response, allowed_skills
        )

        # Check if we got valid 3 categories
        if len(validated_categories) != 3:
            logger.warning(
                f"LLM returned {len(validated_categories)} categories instead of 3, using fallback"
            )
            return _fallback_three_categories(selected_skills, job_title)

        # Ensure unique relevance ranks 1, 2, 3
        ranks = sorted([cat.relevance_rank for cat in validated_categories])
        if ranks != [1, 2, 3]:
            # Fix ranks by assigning based on order
            for i, cat in enumerate(validated_categories):
                cat.relevance_rank = i + 1

        # Sort by relevance
        validated_categories.sort(key=lambda c: c.relevance_rank)

        validation_passed = len(rejected_skills) == 0

        if not validation_passed:
            logger.warning(
                f"LLM returned {len(rejected_skills)} invalid skills: {rejected_skills}"
            )

        logger.info(
            f"Skills formatted into 3 categories: "
            f"{[c.category_name for c in validated_categories]}"
        )

        return ThreeCategoryFormatterResponse(
            categories=validated_categories,
            job_title=job_title,
            validation_passed=validation_passed,
            validation_errors=rejected_skills,
            fallback_used=False
        )

    except Exception as e:
        logger.error(f"LLM 3-category formatting failed: {e}", exc_info=True)
        return _fallback_three_categories(selected_skills, job_title)
