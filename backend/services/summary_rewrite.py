"""
Summary Rewrite Service

Rewrites professional summaries to be tailored to specific jobs using:
- candidate_profile (identity, specializations, target_roles)
- job_profile (core_priorities, seniority, job_title)
- company_profile (mission, industry, AI maturity) when available

Implements PRD 2.10 Summary Rewrite Engine requirements.
"""

import logging
import os
import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from db.models import Experience, JobProfile, User
from schemas.resume_tailor import SelectedSkill
from schemas.skill_gap import SkillGapResponse
from services.cover_letter import BANNED_PHRASES, EM_DASH_PATTERN
from services.llm.base import BaseLLM

logger = logging.getLogger(__name__)

# Path to the prompt template
PROMPT_TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__), "llm", "prompts", "summary_rewrite.txt"
)


@lru_cache(maxsize=1)
def load_summary_prompt_template() -> str:
    """
    Load the summary rewrite prompt template from file.

    Cached to avoid repeated file reads.

    Returns:
        Template string with placeholders

    Raises:
        FileNotFoundError: If template file is missing
    """
    with open(PROMPT_TEMPLATE_PATH, "r") as f:
        return f.read()


def build_company_context(company_profile: Optional[Any]) -> str:
    """
    Build a concise company context string from company profile.

    Args:
        company_profile: CompanyProfile model or None

    Returns:
        1-2 sentence context string, or empty string if no profile
    """
    if company_profile is None:
        return "Not available"

    parts = []

    # Extract key fields if they exist
    if hasattr(company_profile, 'industry') and company_profile.industry:
        parts.append(f"Industry: {company_profile.industry}")

    if hasattr(company_profile, 'mission') and company_profile.mission:
        # Truncate long missions
        mission = company_profile.mission
        if len(mission) > 100:
            mission = mission[:97] + "..."
        parts.append(f"Mission: {mission}")

    if hasattr(company_profile, 'data_ai_maturity') and company_profile.data_ai_maturity:
        parts.append(f"Data/AI maturity: {company_profile.data_ai_maturity}")

    if not parts:
        return "Not available"

    return "; ".join(parts)


def remove_banned_phrases(text: str) -> str:
    """
    Remove banned phrases from text using word boundary matching.

    Args:
        text: Text to clean

    Returns:
        Text with banned phrases removed
    """
    result = text

    for phrase in BANNED_PHRASES.keys():
        # Use word boundaries to avoid partial matches
        pattern = re.compile(
            r'(?<![a-zA-Z])' + re.escape(phrase) + r'(?![a-zA-Z])',
            re.IGNORECASE
        )
        result = pattern.sub('', result)

    # Clean up extra spaces and formatting
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'\s+([.,!?])', r'\1', result)  # Remove space before punctuation

    return result.strip()


def remove_em_dashes(text: str) -> str:
    """
    Remove em-dashes from text, replacing with commas or spaces.

    Args:
        text: Text to clean

    Returns:
        Text with em-dashes removed
    """
    # Replace em-dash with comma-space
    result = re.sub(EM_DASH_PATTERN, ', ', text)
    # Clean up double commas or spaces
    result = re.sub(r',\s*,', ',', result)
    result = re.sub(r'\s+', ' ', result)
    return result.strip()


def truncate_to_word_limit(text: str, max_words: int) -> str:
    """
    Truncate text to word limit while preserving sentence integrity.

    Args:
        text: Text to truncate
        max_words: Maximum word count

    Returns:
        Truncated text
    """
    words = text.split()
    if len(words) <= max_words:
        return text

    # Try to end at a sentence boundary
    truncated_words = words[:max_words]
    truncated = ' '.join(truncated_words)

    # Look for last sentence ending
    for end_char in ['.', '!', '?']:
        last_end = truncated.rfind(end_char)
        if last_end > len(truncated) * 0.7:  # At least 70% of text
            return truncated[:last_end + 1]

    # If no good sentence boundary, just truncate and add period
    if not truncated.endswith('.'):
        truncated = truncated.rstrip('.,;:') + '.'

    return truncated


def calculate_years_experience(experiences: List[Experience]) -> int:
    """
    Calculate total years of experience from experience records.

    Args:
        experiences: List of Experience models

    Returns:
        Total years of experience
    """
    if not experiences:
        return 0

    total_years = 0
    today = datetime.now().date()

    for exp in experiences:
        if exp.start_date:
            end = exp.end_date if exp.end_date else today
            years = (end.year - exp.start_date.year)
            # Add partial year if month difference is significant
            if hasattr(exp.start_date, 'month') and hasattr(end, 'month'):
                months = (end.month - exp.start_date.month)
                if months < 0:
                    years -= 1
            total_years += max(years, 0)

    return total_years


def _generate_mock_summary_v2(
    candidate_profile: Optional[Dict],
    job_profile: JobProfile,
    selected_skills: List[SelectedSkill],
    years_experience: int,
) -> str:
    """
    Generate a template-based summary for MockLLM.

    Uses candidate_profile fields when available for more realistic output.

    Args:
        candidate_profile: User's candidate profile dict
        job_profile: Target job profile
        selected_skills: Selected skills for the resume
        years_experience: Calculated years of experience

    Returns:
        Template-based summary
    """
    # Extract identity from profile or use default
    if candidate_profile and candidate_profile.get('primary_identity'):
        identity = candidate_profile['primary_identity']
    else:
        identity = "Technology leader"

    # Extract specializations
    specializations = []
    if candidate_profile and candidate_profile.get('specializations'):
        specializations = candidate_profile['specializations'][:3]

    # Get top skills
    top_skills = [s.skill for s in selected_skills[:3]] if selected_skills else []

    # Get job priorities for alignment
    priorities = job_profile.core_priorities[:2] if job_profile.core_priorities else []

    # Build summary - aim for ~55 words
    if specializations:
        spec_str = " and ".join(specializations[:2])
        summary = (
            f"{identity} with {years_experience}+ years driving {spec_str}. "
            f"Demonstrated expertise in {', '.join(top_skills[:3]) if top_skills else 'strategic execution'}. "
        )
    else:
        summary = (
            f"{identity} with {years_experience}+ years of experience. "
            f"Deep expertise in {', '.join(top_skills[:3]) if top_skills else 'technology strategy'}. "
        )

    # Add priority alignment
    if priorities:
        summary += f"Track record of delivering results in {priorities[0].lower()}."
    else:
        summary += "Proven ability to deliver impactful solutions in complex environments."

    return summary


async def rewrite_summary_for_job(
    user: User,
    job_profile: JobProfile,
    skill_gap_result: SkillGapResponse,
    selected_skills: List[SelectedSkill],
    experiences: List[Experience],
    llm: BaseLLM,
    company_profile: Optional[Any] = None,
    max_words: int = 60,
) -> str:
    """
    Rewrite professional summary tailored to a specific job.

    Uses candidate_profile, job_profile.core_priorities, and optional
    company_profile to generate a targeted summary per PRD 2.10.

    Args:
        user: User model with candidate_profile
        job_profile: Target job profile
        skill_gap_result: Skill gap analysis results
        selected_skills: Skills selected for the resume
        experiences: User's work experiences
        llm: LLM instance for generation
        company_profile: Optional company profile for context
        max_words: Maximum word count (default 60 per PRD 2.10)

    Returns:
        Tailored professional summary (<=max_words)
    """
    # Extract candidate profile fields
    candidate_profile = user.candidate_profile or {}
    primary_identity = candidate_profile.get('primary_identity', 'Technology Professional')
    specializations = candidate_profile.get('specializations', [])
    target_roles = candidate_profile.get('target_roles', [])

    # Calculate years of experience
    years_experience = calculate_years_experience(experiences)
    if years_experience == 0:
        years_experience = 10  # Default for senior roles

    # Extract top skills
    top_skills = [s.skill for s in selected_skills[:5]] if selected_skills else []

    # Get job priorities
    core_priorities = job_profile.core_priorities or []

    # Build company context
    company_context = build_company_context(company_profile)

    # Check if using MockLLM
    if llm.__class__.__name__ == 'MockLLM':
        summary = _generate_mock_summary_v2(
            candidate_profile=candidate_profile,
            job_profile=job_profile,
            selected_skills=selected_skills,
            years_experience=years_experience,
        )
    else:
        # Load and format prompt template
        try:
            template = load_summary_prompt_template()
        except FileNotFoundError:
            logger.warning("Summary prompt template not found, using inline prompt")
            template = _get_fallback_prompt_template()

        prompt = template.format(
            primary_identity=primary_identity,
            specializations=', '.join(specializations) if specializations else 'N/A',
            job_title=job_profile.job_title or 'Target Role',
            seniority=job_profile.seniority or 'Senior',
            years_experience=years_experience,
            top_skills=', '.join(top_skills) if top_skills else 'N/A',
            core_priorities=', '.join(core_priorities[:3]) if core_priorities else 'N/A',
            company_context=company_context,
        )

        # Generate summary via LLM
        summary = await llm.generate_text(prompt, max_tokens=150)

    # Post-processing
    # 1. Remove banned phrases
    summary = remove_banned_phrases(summary)

    # 2. Remove em-dashes
    summary = remove_em_dashes(summary)

    # 3. Enforce word limit
    summary = truncate_to_word_limit(summary, max_words)

    # 4. Clean up formatting
    summary = ' '.join(summary.split())  # Normalize whitespace

    logger.info(
        f"Generated summary for job {job_profile.id}: "
        f"{len(summary.split())} words, identity={primary_identity}"
    )

    return summary


def _get_fallback_prompt_template() -> str:
    """Return inline fallback prompt if template file is missing."""
    return """Write a professional resume summary (50-60 words) for:

Candidate Identity: {primary_identity}
Specializations: {specializations}
Target Role: {job_title} ({seniority})
Years Experience: {years_experience}+
Top Skills: {top_skills}
Job Priorities: {core_priorities}
Company Context: {company_context}

Requirements:
- Lead with identity framing
- Emphasize specializations aligned to job priorities
- No banned phrases (passionate, proven track record, results-oriented, etc.)
- No em-dashes
- Executive, direct tone

Return ONLY the summary text."""
