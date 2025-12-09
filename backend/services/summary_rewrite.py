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
from datetime import datetime, date
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

    Uses career span (earliest start to latest end) rather than summing
    individual role durations, which would double-count overlapping roles.

    Args:
        experiences: List of Experience models

    Returns:
        Total years of professional experience
    """
    if not experiences:
        return 0

    today = datetime.now().date()

    # Find the earliest start date and latest end date
    earliest_start = None
    latest_end = None

    for exp in experiences:
        if exp.start_date:
            start = exp.start_date if isinstance(exp.start_date, date) else exp.start_date.date()
            if earliest_start is None or start < earliest_start:
                earliest_start = start

            end = exp.end_date if exp.end_date else today
            if isinstance(end, datetime):
                end = end.date()
            if latest_end is None or end > latest_end:
                latest_end = end

    if not earliest_start:
        return 0

    # Calculate span
    years = (latest_end.year - earliest_start.year)
    if latest_end.month < earliest_start.month:
        years -= 1

    return max(years, 0)


def _infer_identity_from_job_titles(experiences: Optional[List[Experience]]) -> str:
    """
    Infer a professional identity from the user's job titles.

    Analyzes recent job titles to determine the most representative identity.
    """
    if not experiences:
        return "Technology professional"

    # Get recent job titles (most recent first)
    titles = [exp.job_title.lower() for exp in experiences[:5] if exp.job_title]

    if not titles:
        return "Technology professional"

    # Priority keywords to look for
    identity_keywords = {
        "ai": "AI Strategy and Data leader",
        "data governance": "Data Governance and Strategy leader",
        "data strategy": "Data Strategy professional",
        "principal": "Principal Consultant with enterprise expertise",
        "director": "Director-level technology executive",
        "vp": "VP-level technology executive",
        "architect": "Enterprise Architect",
        "consultant": "Management Consultant",
        "analyst": "Senior Analyst",
        "manager": "Technology Manager",
        "lead": "Technical Lead",
        "engineer": "Senior Engineer",
    }

    # Check titles for keywords
    for title in titles:
        for keyword, identity in identity_keywords.items():
            if keyword in title:
                return identity

    # Default based on most recent title
    return f"{experiences[0].job_title.split(' - ')[0].strip()} professional"


def _extract_specializations_from_profile(
    candidate_profile: Optional[Dict],
    job_profile: JobProfile,
    selected_skills: List[SelectedSkill]
) -> List[str]:
    """
    Extract relevant specializations from candidate profile, aligning with job requirements.

    Uses linkedin_meta.top_skills if specializations not directly available.
    Prioritizes multi-word skills (more specific) over single-word skills.
    """
    specializations = []

    # First try direct specializations
    if candidate_profile and candidate_profile.get('specializations'):
        specializations = candidate_profile['specializations'][:5]

    # Fallback to linkedin_meta.top_skills
    if not specializations and candidate_profile:
        linkedin_meta = candidate_profile.get('linkedin_meta', {})
        top_skills = linkedin_meta.get('top_skills', [])
        if top_skills:
            # Get job-relevant skills from top_skills
            job_keywords = set()
            if job_profile.extracted_skills:
                job_keywords.update(s.lower() for s in job_profile.extracted_skills)
            if job_profile.core_priorities:
                for p in job_profile.core_priorities:
                    job_keywords.update(word.lower() for word in p.split())

            # Find top_skills that align with job requirements
            # Prioritize multi-word skills (more specific/strategic)
            aligned_skills = []
            for skill in top_skills[:50]:  # Check first 50
                skill_lower = skill.lower()
                # Skip very short single-word skills (e.g., "R", "SQL")
                if len(skill) <= 3 and ' ' not in skill:
                    continue
                if any(kw in skill_lower or skill_lower in kw for kw in job_keywords):
                    aligned_skills.append(skill)
                    if len(aligned_skills) >= 5:
                        break

            # Sort to prioritize multi-word skills (more strategic/specific)
            aligned_skills.sort(key=lambda s: (0 if ' ' in s else 1, -len(s)))

            # If no aligned skills, use high-value general skills
            if not aligned_skills:
                high_value = ["AI Strategy", "Data Strategy", "Data Governance",
                             "Machine Learning", "Cloud Computing", "Analytics",
                             "Data Architecture", "Enterprise Data", "Business Intelligence"]
                for skill in top_skills:
                    if skill in high_value:
                        aligned_skills.append(skill)
                        if len(aligned_skills) >= 3:
                            break

            specializations = aligned_skills[:3]

    # Final fallback to selected skills (prioritize multi-word)
    if not specializations:
        skill_list = [s.skill for s in selected_skills if len(s.skill) > 3][:3]
        specializations = skill_list if skill_list else [s.skill for s in selected_skills[:3]]

    return specializations


def _generate_mock_summary_v2(
    candidate_profile: Optional[Dict],
    job_profile: JobProfile,
    selected_skills: List[SelectedSkill],
    years_experience: int = 0,  # Kept for API compatibility but not used
    experiences: Optional[List[Experience]] = None,
) -> str:
    """
    Generate a template-based summary for MockLLM.

    Uses candidate_profile fields when available for more realistic output.
    NOTE: Does NOT mention years of experience to avoid age discrimination.

    Args:
        candidate_profile: User's candidate profile dict
        job_profile: Target job profile
        selected_skills: Selected skills for the resume
        years_experience: DEPRECATED - kept for compatibility but not used
        experiences: User's work experiences for identity inference

    Returns:
        Template-based summary
    """
    # Extract identity from profile or infer from job titles
    if candidate_profile and candidate_profile.get('primary_identity'):
        identity = candidate_profile['primary_identity']
    else:
        identity = _infer_identity_from_job_titles(experiences)

    # Extract specializations (uses linkedin_meta.top_skills as fallback)
    specializations = _extract_specializations_from_profile(
        candidate_profile, job_profile, selected_skills
    )

    # Get top skills from selected skills
    top_skills = [s.skill for s in selected_skills[:4]] if selected_skills else []

    # Get job priorities for alignment
    priorities = job_profile.core_priorities[:2] if job_profile.core_priorities else []

    # Get job title for context
    job_title = job_profile.job_title or "the role"

    # Build summary - aim for ~55 words
    # Use experience-depth language instead of years
    if specializations:
        spec_str = ", ".join(specializations[:2])
        summary = (
            f"{identity} with deep expertise in {spec_str}. "
        )
        if top_skills:
            summary += f"Proven track record leveraging {', '.join(top_skills[:3])} to drive strategic outcomes. "
    else:
        summary = (
            f"{identity} with extensive experience across enterprise environments. "
            f"Strong command of {', '.join(top_skills[:3]) if top_skills else 'technology strategy'}. "
        )

    # Add priority alignment specific to the job
    if priorities:
        priority_text = priorities[0].lower()
        # Clean up priority text
        if len(priority_text) > 50:
            priority_text = priority_text[:47] + "..."
        summary += f"Focused on {priority_text} to deliver measurable business impact."
    else:
        summary += f"Passionate about leveraging technology to drive business transformation."

    return summary


async def rewrite_summary_for_job(
    user: User,
    job_profile: JobProfile,
    skill_gap_result: SkillGapResponse,
    selected_skills: List[SelectedSkill],
    experiences: List[Experience],
    llm: BaseLLM,
    company_profile: Optional[Any] = None,
    max_words: int = 50,
    context_notes: Optional[str] = None,
    max_lines: Optional[int] = None,
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
        context_notes: Optional user-provided context notes for personalization (Sprint 8B.8)
        max_lines: Optional hint for target line count in rendered resume

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

    # If max_lines hint provided, calculate effective max_words
    if max_lines is not None:
        # Validate max_lines bounds (1-100 reasonable for resume summary)
        if max_lines < 1:
            logger.warning(f"Invalid max_lines={max_lines} (too small), ignoring")
        elif max_lines > 100:
            logger.warning(f"Invalid max_lines={max_lines} (too large), ignoring")
        else:
            chars_per_line = 75
            avg_word_length = 5
            # Ensure at least 1 word even for very short line limits
            effective_max_words = max(1, (max_lines * chars_per_line) // avg_word_length)
            max_words = min(max_words, effective_max_words)
            logger.info(f"Adjusted max_words to {max_words} based on max_lines={max_lines}")

    # Check if using MockLLM
    if llm.__class__.__name__ == 'MockLLM':
        summary = _generate_mock_summary_v2(
            candidate_profile=candidate_profile,
            job_profile=job_profile,
            selected_skills=selected_skills,
            years_experience=years_experience,
            experiences=experiences,
        )
    else:
        # Load and format prompt template
        try:
            template = load_summary_prompt_template()
        except FileNotFoundError:
            logger.warning("Summary prompt template not found, using inline prompt")
            template = _get_fallback_prompt_template()

        # Sprint 8B.8: Add context_notes to prompt variables
        prompt_vars = {
            'primary_identity': primary_identity,
            'specializations': ', '.join(specializations) if specializations else 'N/A',
            'job_title': job_profile.job_title or 'Target Role',
            'seniority': job_profile.seniority or 'Senior',
            'years_experience': years_experience,
            'top_skills': ', '.join(top_skills) if top_skills else 'N/A',
            'core_priorities': ', '.join(core_priorities[:3]) if core_priorities else 'N/A',
            'company_context': company_context,
        }

        # Add context_notes if provided
        if context_notes:
            prompt_vars['context_notes'] = context_notes[:500]  # Limit length
        else:
            prompt_vars['context_notes'] = 'Not provided'

        # Add max_lines hint if provided
        if max_lines is not None:
            prompt_vars['max_lines'] = max_lines
        else:
            prompt_vars['max_lines'] = 'Not specified'

        # Format prompt - use safe format to handle missing placeholders
        try:
            prompt = template.format(**prompt_vars)
        except KeyError as e:
            # Template doesn't have all placeholders, filter and append separately
            # Remove keys that may not be in the template
            safe_vars = {k: v for k, v in prompt_vars.items()
                        if k not in ('context_notes', 'max_lines')}
            prompt = template.format(**safe_vars)

            # Append context_notes if provided
            if context_notes:
                prompt += f"\n\nAdditional context from user: {context_notes[:500]}"

            # Append max_lines hint if provided
            if max_lines is not None:
                prompt += f"\n\nTarget line count: {max_lines} lines (approximately {max_words} words)"

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

    # 5. Validate line count if max_lines was specified
    if max_lines is not None:
        chars_per_line = 75
        estimated_lines = len(summary) / chars_per_line
        if estimated_lines > max_lines:
            logger.warning(
                f"Summary exceeds max_lines={max_lines} "
                f"(estimated {estimated_lines:.1f} lines). "
                f"Consider reducing max_words further."
            )

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
Top Skills: {top_skills}
Job Priorities: {core_priorities}
Company Context: {company_context}

Requirements:
- Lead with identity framing
- Emphasize specializations aligned to job priorities
- No banned phrases (passionate, proven track record, results-oriented, etc.)
- No em-dashes
- Executive, direct tone
- Do NOT mention years of experience (age discrimination concern)
- Use depth-of-experience language like "extensive background", "deep expertise", "proven expertise" instead

Return ONLY the summary text."""
