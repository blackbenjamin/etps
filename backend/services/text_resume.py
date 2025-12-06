"""
Plain Text Resume Generation Service

Generates ATS-friendly plain text resumes from TailoredResume JSON.
Uses ASCII-only characters with consistent formatting for maximum compatibility.
"""

import logging
from typing import Optional, List
from datetime import datetime

from schemas.resume_tailor import TailoredResume, SelectedRole, SelectedSkill, SelectedEngagement


logger = logging.getLogger(__name__)


def _format_date_range(start_date: str, end_date: Optional[str]) -> str:
    """Format date range for display (e.g., '9/2024 - Present')."""
    def format_date(date_str: str) -> str:
        if not date_str:
            return "Present"
        parts = date_str.split("-")
        if len(parts) >= 2:
            month = int(parts[1])
            year = parts[0]
            return f"{month}/{year}"
        return date_str

    start = format_date(start_date)
    end = format_date(end_date) if end_date else "Present"
    return f"{start} - {end}"


def _is_consulting_role(role: SelectedRole) -> bool:
    """
    Check if this role is a consulting role that should show engagements.
    """
    # Check employer_type first (v1.3.0)
    if role.employer_type == "independent_consulting":
        return True

    # Check if role has engagements (v1.3.0)
    if role.selected_engagements:
        return True

    # Fallback: name-based detection for legacy data
    employer_lower = role.employer_name.lower() if role.employer_name else ""
    return "benjamin black consulting" in employer_lower


def _group_skills_by_category(skills: List[SelectedSkill]) -> dict:
    """
    Group skills by category for display.
    """
    if not skills:
        return {}

    # Define category mappings based on common skill patterns
    category_patterns = {
        "AI/ML": ["ai", "ml", "machine learning", "deep learning", "nlp", "llm",
                  "rag", "vector", "embedding", "prompt", "neural", "transformer"],
        "Programming": ["python", "sql", "r ", "java", "scala", "spark", "pandas",
                       "numpy", "scikit", "tensorflow", "pytorch", "code", "script"],
        "Data": ["data", "etl", "pipeline", "warehouse", "lake", "hadoop", "kafka",
                "snowflake", "databricks", "dbt", "airflow", "analytics"],
        "Cloud & Infrastructure": ["aws", "azure", "gcp", "cloud", "docker",
                                   "kubernetes", "terraform", "devops", "ci/cd"],
        "Governance & Strategy": ["governance", "strategy", "compliance", "policy",
                                  "framework", "architecture", "leadership", "management"],
        "Visualization & BI": ["tableau", "power bi", "looker", "dashboard",
                              "visualization", "reporting", "qlik"],
    }

    categorized = {}
    uncategorized = []

    for skill in skills:
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

    # Add uncategorized skills to "Other" if any
    if uncategorized:
        categorized["Other"] = uncategorized

    return categorized


def create_resume_text(
    tailored_resume: TailoredResume,
    user_name: str,
    user_email: str,
    user_phone: Optional[str] = None,
    user_linkedin: Optional[str] = None,
    user_portfolio: Optional[str] = None,
    education: Optional[List[dict]] = None
) -> str:
    """
    Generate an ATS-friendly plain text resume from a TailoredResume object.

    Format specifications:
    - ASCII-only characters (use -, not bullets)
    - Section headers with === underlines
    - 2 blank lines between sections
    - Header: NAME (all caps), contact line with | separators
    - Sections: PROFESSIONAL SUMMARY, PROFESSIONAL EXPERIENCE, TECHNICAL SKILLS, EDUCATION
    - Skills grouped by category
    - Consulting engagements indented under parent role

    Args:
        tailored_resume: The TailoredResume JSON object with selected content
        user_name: Full name for the header
        user_email: Email address for the header
        user_phone: Phone number for the header (optional)
        user_linkedin: LinkedIn URL or handle for the header (optional)
        user_portfolio: Portfolio URL for the header (optional)
        education: List of education entries, each with:
            - institution: str
            - location: str (optional)
            - degree: str
            - details: list[str] (optional bullet points)

    Returns:
        str: The generated plain text resume

    Example:
        >>> resume = TailoredResume(...)
        >>> text = create_resume_text(
        ...     tailored_resume=resume,
        ...     user_name="Benjamin Black",
        ...     user_email="benjamin.black@sloan.mit.edu",
        ...     user_phone="617-504-5529",
        ...     user_linkedin="linkedin.com/in/benjaminblack"
        ... )
    """
    lines = []

    # === HEADER ===
    lines.append(user_name.upper())

    # Contact line with | separators
    contact_parts = [user_email]
    if user_phone:
        contact_parts.append(user_phone)
    if user_linkedin:
        contact_parts.append(user_linkedin)
    if user_portfolio:
        contact_parts.append(user_portfolio)

    contact_line = " | ".join(contact_parts)
    lines.append(contact_line)
    lines.append("")  # Blank line after header

    # === PROFESSIONAL SUMMARY ===
    if tailored_resume.tailored_summary:
        lines.append("PROFESSIONAL SUMMARY")
        lines.append("=" * len("PROFESSIONAL SUMMARY"))
        lines.append("")
        lines.append(tailored_resume.tailored_summary)
        lines.append("")
        lines.append("")  # 2 blank lines between sections

    # === PROFESSIONAL EXPERIENCE ===
    if tailored_resume.selected_roles:
        lines.append("PROFESSIONAL EXPERIENCE")
        lines.append("=" * len("PROFESSIONAL EXPERIENCE"))
        lines.append("")

        for role_idx, role in enumerate(tailored_resume.selected_roles):
            # Company and job title line
            date_range = _format_date_range(role.start_date, role.end_date)

            # Company name and location
            company_line = role.employer_name
            if role.location:
                company_line += f" ({role.location})"
            company_line += f" | {date_range}"
            lines.append(company_line)

            # Job title
            lines.append(role.job_title)
            lines.append("")

            # Check if consulting role with engagements
            if _is_consulting_role(role) and role.selected_engagements:
                # Add role summary if present
                if role.role_summary:
                    lines.append(role.role_summary)
                    lines.append("")

                # Add each engagement
                for engagement in role.selected_engagements:
                    # Engagement header
                    eng_header = f"  {engagement.client or 'Project'}"
                    if engagement.project_name:
                        eng_header += f" - {engagement.project_name}"
                    if engagement.date_range_label:
                        eng_header += f" ({engagement.date_range_label})"
                    lines.append(eng_header)

                    # Engagement bullets (indented)
                    for bullet in engagement.selected_bullets:
                        lines.append(f"    - {bullet.text}")
                    lines.append("")
            else:
                # Regular role bullets (not indented)
                for bullet in role.selected_bullets:
                    lines.append(f"- {bullet.text}")
                lines.append("")

            # Add blank line between roles (except last)
            if role_idx < len(tailored_resume.selected_roles) - 1:
                lines.append("")

        lines.append("")  # 2 blank lines between sections

    # === TECHNICAL SKILLS ===
    if tailored_resume.selected_skills:
        lines.append("TECHNICAL SKILLS")
        lines.append("=" * len("TECHNICAL SKILLS"))
        lines.append("")

        # Group skills by category
        grouped_skills = _group_skills_by_category(tailored_resume.selected_skills)

        for category, skill_list in grouped_skills.items():
            skills_text = ", ".join(skill_list)
            lines.append(f"{category}: {skills_text}")

        lines.append("")
        lines.append("")  # 2 blank lines between sections

    # === EDUCATION ===
    if education:
        lines.append("EDUCATION")
        lines.append("=" * len("EDUCATION"))
        lines.append("")

        for edu_entry in education:
            # Institution and location
            inst_line = edu_entry.get("institution", "")
            location = edu_entry.get("location")
            if location:
                inst_line += f" ({location})"
            lines.append(inst_line)

            # Degree
            degree = edu_entry.get("degree")
            if degree:
                lines.append(degree)

            # Details (if any)
            details = edu_entry.get("details", [])
            if details:
                for detail in details:
                    lines.append(f"- {detail}")

            lines.append("")

    # Join all lines with newlines
    resume_text = "\n".join(lines)

    logger.info(f"Generated plain text resume with {len(tailored_resume.selected_roles)} roles")
    return resume_text
