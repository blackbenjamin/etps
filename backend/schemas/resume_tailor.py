"""
Resume Tailoring Schemas

Pydantic models for resume tailoring requests and responses.
"""

from typing import Optional, List, Dict, Literal, ClassVar
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class TailorResumeRequest(BaseModel):
    """
    Request model for resume tailoring.

    Generates a tailored resume by selecting and optimizing content from the user's
    master resume to align with a specific job profile.
    """
    job_profile_id: int = Field(
        ...,
        description="ID of the parsed job profile to tailor resume for",
        gt=0
    )
    user_id: int = Field(
        ...,
        description="User ID for resume tailoring",
        gt=0
    )
    template_id: Optional[int] = Field(
        None,
        description="Specific template ID to use for formatting"
    )
    max_bullets_per_role: int = Field(
        default=4,
        ge=2,
        le=8,
        description="Maximum number of bullets to select per role"
    )
    max_skills: int = Field(
        default=12,
        ge=5,
        le=20,
        description="Maximum number of skills to include in skills section"
    )
    custom_instructions: Optional[str] = Field(
        None,
        description="User-provided custom instructions for tailoring"
    )


class SelectedBullet(BaseModel):
    """
    A selected bullet point for a role in the tailored resume.

    May be the original bullet or a rewritten version optimized for the target job.
    v1.3.0: Added engagement_id for bullets belonging to engagements.
    """
    bullet_id: int = Field(
        ...,
        description="ID of the original bullet from master resume"
    )
    text: str = Field(
        ...,
        description="The bullet text (original or rewritten)"
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relevance score for this bullet to the target job (0-1)"
    )
    was_rewritten: bool = Field(
        ...,
        description="Whether this bullet was rewritten for better alignment"
    )
    original_text: Optional[str] = Field(
        None,
        description="Original bullet text if was_rewritten is True"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags associated with this bullet"
    )
    selection_reason: str = Field(
        ...,
        description="Why this bullet was selected for the tailored resume"
    )
    engagement_id: Optional[int] = Field(
        None,
        description="ID of the engagement this bullet belongs to (for consulting roles)"
    )


class SelectedEngagement(BaseModel):
    """
    A selected engagement within a consulting role (v1.3.0).

    Represents client work within a consulting period, with its own bullets.
    """
    engagement_id: int = Field(
        ...,
        description="ID of the engagement from master resume"
    )
    client: Optional[str] = Field(
        None,
        description="Client company name (e.g., 'Edward Jones')"
    )
    project_name: Optional[str] = Field(
        None,
        description="Project name or focus area (e.g., 'Enterprise Data Strategy')"
    )
    date_range_label: Optional[str] = Field(
        None,
        description="Display label for date range (e.g., '2/2023-11/2023')"
    )
    selected_bullets: List[SelectedBullet] = Field(
        default_factory=list,
        description="Selected bullets for this engagement"
    )


class SelectedRole(BaseModel):
    """
    A selected role/experience for the tailored resume.

    Contains immutable role metadata and selected bullets optimized for the target job.
    v1.3.0: Added engagements for consulting roles and employer_type field.
    """
    experience_id: int = Field(
        ...,
        description="ID of the experience record from master resume"
    )
    job_title: str = Field(
        ...,
        description="Job title (IMMUTABLE - copied from master resume)"
    )
    employer_name: str = Field(
        ...,
        description="Employer/company name (IMMUTABLE - copied from master resume)"
    )
    location: Optional[str] = Field(
        None,
        description="Job location (IMMUTABLE - copied from master resume)"
    )
    start_date: str = Field(
        ...,
        description="Start date in ISO format (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        None,
        description="End date in ISO format (YYYY-MM-DD) or null if current role"
    )
    employer_type: Optional[str] = Field(
        None,
        description="Type of employer: independent_consulting, full_time, contract"
    )
    role_summary: Optional[str] = Field(
        None,
        description="Brief role summary (for consulting roles)"
    )
    selected_bullets: List[SelectedBullet] = Field(
        default_factory=list,
        description="Selected and optimized bullets for this role (non-consulting roles)"
    )
    selected_engagements: List[SelectedEngagement] = Field(
        default_factory=list,
        description="Selected engagements with bullets (for consulting roles)"
    )
    bullet_selection_rationale: str = Field(
        ...,
        description="Overall rationale for bullet selection for this role"
    )


class SelectedSkill(BaseModel):
    """
    A selected skill for the tailored resume skills section.

    Prioritized and ordered based on relevance to the target job.
    """
    skill: str = Field(
        ...,
        description="The skill name"
    )
    priority_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Priority score for this skill (0-1)"
    )
    match_type: Literal["direct_match", "adjacent_skill", "transferable"] = Field(
        ...,
        description="Type of match: direct_match (exact), adjacent_skill (related), transferable (applicable)"
    )
    source: str = Field(
        ...,
        description="Source of this skill (e.g., 'job_requirements', 'user_master_resume')"
    )


class TailoringRationale(BaseModel):
    """
    Comprehensive rationale explaining the tailoring decisions.

    Provides transparency into why specific content was selected and how it aligns
    with the target job requirements.
    """
    summary_approach: str = Field(
        ...,
        description="Approach taken for crafting the tailored summary"
    )
    bullet_selection_strategy: str = Field(
        ...,
        description="Overall strategy for selecting bullets across all roles"
    )
    skills_ordering_logic: str = Field(
        ...,
        description="Logic used for ordering and prioritizing skills"
    )
    role_emphasis: Dict[int, str] = Field(
        default_factory=dict,
        description="Map of experience_id to emphasis reason for each role"
    )
    gaps_addressed: List[str] = Field(
        default_factory=list,
        description="List of skill gaps that were addressed or mitigated"
    )
    strengths_highlighted: List[str] = Field(
        default_factory=list,
        description="Key strengths that were emphasized in the tailoring"
    )


class TailoredResume(BaseModel):
    """
    Response model for tailored resume.

    Contains the complete tailored resume with selected and optimized content,
    along with metadata about the tailoring process and quality scores.
    """
    job_profile_id: int = Field(
        ...,
        description="ID of the job profile this resume was tailored for"
    )
    user_id: int = Field(
        ...,
        description="User ID for this tailored resume"
    )
    application_id: Optional[int] = Field(
        None,
        description="ID of the associated job application if one exists"
    )
    tailored_summary: str = Field(
        ...,
        description="Tailored professional summary optimized for the target job"
    )
    selected_roles: List[SelectedRole] = Field(
        default_factory=list,
        description="Selected roles with optimized bullets"
    )
    selected_skills: List[SelectedSkill] = Field(
        default_factory=list,
        description="Prioritized skills list for the skills section"
    )
    rationale: TailoringRationale = Field(
        ...,
        description="Comprehensive rationale for tailoring decisions"
    )
    ats_score_estimate: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Estimated ATS compatibility score (0-100)"
    )
    match_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall match score between tailored resume and job requirements (0-100)"
    )
    generated_at: str = Field(
        ...,
        description="ISO timestamp of when this tailored resume was generated"
    )
    constraints_validated: bool = Field(
        ...,
        description="Whether the tailored resume meets all specified constraints (e.g., bullet counts)"
    )

    @field_validator('match_score')
    @classmethod
    def validate_match_score(cls, v: float) -> float:
        """Validate that match_score is within valid range."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("match_score must be between 0 and 100")
        return v

    @field_validator('ats_score_estimate')
    @classmethod
    def validate_ats_score(cls, v: Optional[float]) -> Optional[float]:
        """Validate that ats_score_estimate is within valid range if provided."""
        if v is not None and not 0.0 <= v <= 100.0:
            raise ValueError("ats_score_estimate must be between 0 and 100")
        return v


class EducationEntry(BaseModel):
    """Education entry for DOCX resume generation."""
    institution: str = Field(..., description="Name of the educational institution")
    location: Optional[str] = Field(None, description="Location of the institution")
    degree: str = Field(..., description="Degree or certification earned")
    details: List[str] = Field(
        default_factory=list,
        description="Additional details or achievements (bullet points)"
    )


class ResumeDocxRequest(BaseModel):
    """
    Request model for DOCX resume generation.

    Takes a TailoredResume JSON and user contact info to generate a formatted DOCX.
    Validates that personal information is real (not placeholder data).
    """
    tailored_resume: TailoredResume = Field(
        ...,
        description="The tailored resume JSON object to render as DOCX"
    )
    user_name: str = Field(
        ...,
        min_length=2,
        description="Full name for the resume header (must be real, not placeholder)"
    )
    user_email: EmailStr = Field(
        ...,
        description="Email address for the resume header (must be real, not placeholder)"
    )
    user_phone: Optional[str] = Field(
        None,
        description="Phone number for the resume header"
    )
    user_linkedin: Optional[str] = Field(
        None,
        description="LinkedIn URL or handle for the resume header"
    )
    education: List[EducationEntry] = Field(
        default_factory=list,
        description="List of education entries to include"
    )

    # Placeholder names to reject
    PLACEHOLDER_NAMES: ClassVar[set] = {
        "test user", "test", "user", "john doe", "jane doe",
        "sample user", "example user", "placeholder", "name",
        "first last", "your name", "full name", "n/a", "na",
        "tbd", "todo", "xxx", "abc", "test test",
    }

    # Placeholder email domains to reject
    PLACEHOLDER_EMAIL_DOMAINS: ClassVar[set] = {
        "example.com", "example.org", "example.net",
        "test.com", "test.org", "test.net",
        "placeholder.com", "fake.com", "sample.com",
        "domain.com", "email.com", "mail.com",
        "yourmail.com", "youremail.com",
    }

    @model_validator(mode="after")
    def validate_personal_info(self) -> "ResumeDocxRequest":
        """Validate that personal information is real, not placeholder data."""
        errors = []

        # Check for placeholder names
        name_lower = self.user_name.lower().strip()
        if name_lower in self.PLACEHOLDER_NAMES:
            errors.append(f"'{self.user_name}' appears to be a placeholder name. Please provide your real name.")

        # Check name has at least first and last name (2 parts)
        name_parts = [p for p in self.user_name.split() if p.strip()]
        if len(name_parts) < 2:
            errors.append("Please provide your full name (first and last name).")

        # Check for placeholder email domains
        email_domain = self.user_email.split("@")[-1].lower()
        if email_domain in self.PLACEHOLDER_EMAIL_DOMAINS:
            errors.append(f"Email domain '{email_domain}' appears to be a placeholder. Please provide your real email address.")

        # Require at least one contact method (phone or LinkedIn)
        if not self.user_phone and not self.user_linkedin:
            errors.append("Please provide at least one contact method: phone number or LinkedIn URL.")

        if errors:
            raise ValueError(" | ".join(errors))

        return self
