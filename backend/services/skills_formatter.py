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
    # Define category patterns (same as original docx_resume.py)
    category_patterns = {
        "AI/ML": ["ai", "ml", "machine learning", "deep learning", "nlp", "llm",
                  "rag", "vector", "embedding", "prompt", "neural", "transformer",
                  "generative", "gpt", "claude", "artificial intelligence"],
        "Programming Languages & Frameworks": [
            "python", "sql", "r ", "java", "scala", "spark", "pandas",
            "numpy", "scikit", "tensorflow", "pytorch", "javascript", "typescript"
        ],
        "Data Engineering & Analytics": [
            "data", "etl", "pipeline", "warehouse", "lake", "hadoop", "kafka",
            "snowflake", "databricks", "dbt", "airflow", "analytics"
        ],
        "Cloud & Infrastructure": [
            "aws", "azure", "gcp", "cloud", "docker",
            "kubernetes", "terraform", "devops", "ci/cd"
        ],
        "Governance & Strategy": [
            "governance", "strategy", "compliance", "policy",
            "framework", "architecture", "leadership", "management"
        ],
        "Visualization & BI": [
            "tableau", "power bi", "looker", "dashboard",
            "visualization", "reporting", "qlik"
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
