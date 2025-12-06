"""
Job Parser Schemas

Pydantic models for job description parsing requests and responses.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict


class JobParseRequest(BaseModel):
    """
    Request model for job description parsing.

    Must provide either jd_text or jd_url, but not both.
    """
    jd_text: Optional[str] = Field(None, description="Raw job description text")
    jd_url: Optional[str] = Field(None, description="URL to fetch job description from")
    user_id: int = Field(..., description="User ID for associating the job profile", gt=0)

    @field_validator('jd_text')
    @classmethod
    def validate_jd_text(cls, v: Optional[str]) -> Optional[str]:
        """Validate that jd_text is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("jd_text cannot be empty")
        return v

    @field_validator('jd_url')
    @classmethod
    def validate_jd_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that jd_url is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("jd_url cannot be empty")
        return v

    def model_post_init(self, __context) -> None:
        """Validate that exactly one of jd_text or jd_url is provided."""
        if self.jd_text is None and self.jd_url is None:
            raise ValueError("Must provide either jd_text or jd_url")
        if self.jd_text is not None and self.jd_url is not None:
            raise ValueError("Cannot provide both jd_text and jd_url")


class JobParseResponse(BaseModel):
    """
    Response model for parsed job description.

    Contains all extracted and analyzed information from the job description.
    """
    job_profile_id: int = Field(..., description="ID of the created job profile")
    raw_jd_text: str = Field(..., description="Original job description text")
    jd_url: Optional[str] = Field(None, description="Source URL if fetched from web")

    # Basic job information
    job_title: str = Field(..., description="Extracted job title")
    company_name: Optional[str] = Field(None, description="Company name if identified")
    location: Optional[str] = Field(None, description="Job location")
    seniority: Optional[str] = Field(None, description="Seniority level (e.g., 'senior', 'director')")

    # Structured content
    responsibilities: Optional[str] = Field(None, description="Key responsibilities section")
    requirements: Optional[str] = Field(None, description="Required qualifications")
    nice_to_haves: Optional[str] = Field(None, description="Preferred qualifications")

    # Extracted skills and capabilities
    extracted_skills: List[str] = Field(default_factory=list, description="List of technical and domain skills")
    core_priorities: List[str] = Field(default_factory=list, description="3-5 core themes/priorities from JD")
    must_have_capabilities: List[str] = Field(default_factory=list, description="Critical capabilities required")
    nice_to_have_capabilities: List[str] = Field(default_factory=list, description="Preferred capabilities")

    # Analysis metadata
    tone_style: Optional[str] = Field(None, description="Detected tone/style of the JD")
    job_type_tags: List[str] = Field(default_factory=list, description="Categorization tags (e.g., 'ai_governance', 'consulting')")

    # Timestamps
    created_at: str = Field(..., description="ISO timestamp of creation")


class JobProfileDTO(BaseModel):
    """
    Data Transfer Object for JobProfile ORM model.

    Used for converting SQLAlchemy models to Pydantic for API responses.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company_id: Optional[int] = None
    raw_jd_text: str
    jd_url: Optional[str] = None
    job_title: str
    location: Optional[str] = None
    seniority: Optional[str] = None
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    nice_to_haves: Optional[str] = None
    extracted_skills: Optional[List[str]] = None
    core_priorities: Optional[List[str]] = None
    must_have_capabilities: Optional[List[str]] = None
    nice_to_have_capabilities: Optional[List[str]] = None
    skill_gap_analysis: Optional[Dict] = None
    tone_style: Optional[str] = None
    job_type_tags: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    created_at: str
    updated_at: Optional[str] = None
