"""
Company Profile Schemas

Pydantic schemas for company profile API requests and responses.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CompanyEnrichRequest(BaseModel):
    """Request to enrich a company profile."""

    company_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Company name to enrich"
    )
    jd_text: Optional[str] = Field(
        None,
        max_length=100000,
        description="Job description text for context"
    )
    website_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Company website URL to fetch"
    )
    user_id: int = Field(
        ...,
        description="User ID requesting the enrichment"
    )

    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        """Ensure company name is not just whitespace."""
        if not v.strip():
            raise ValueError("Company name cannot be empty")
        return v.strip()

    @field_validator('website_url')
    @classmethod
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """Basic URL validation."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not v.startswith(('http://', 'https://')):
            raise ValueError("Website URL must start with http:// or https://")
        return v


class CompanyProfileResponse(BaseModel):
    """Company profile data response."""

    id: int
    name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    size_band: Optional[str] = None
    headquarters: Optional[str] = None
    business_lines: Optional[str] = None
    known_initiatives: Optional[str] = None
    culture_signals: List[str] = Field(default_factory=list)
    data_ai_maturity: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class CompanyProfileUpdate(BaseModel):
    """Request to update a company profile."""

    website: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    size_band: Optional[str] = Field(None, max_length=50)
    headquarters: Optional[str] = Field(None, max_length=255)
    business_lines: Optional[str] = Field(None, max_length=2000)
    known_initiatives: Optional[str] = Field(None, max_length=2000)
    culture_signals: Optional[List[str]] = None
    data_ai_maturity: Optional[str] = Field(None, max_length=50)

    @field_validator('data_ai_maturity')
    @classmethod
    def validate_ai_maturity(cls, v: Optional[str]) -> Optional[str]:
        """Validate AI maturity is from allowed values."""
        if v is None:
            return None
        allowed = ['low', 'developing', 'advanced']
        if v not in allowed:
            raise ValueError(f"data_ai_maturity must be one of: {', '.join(allowed)}")
        return v

    @field_validator('culture_signals')
    @classmethod
    def validate_culture_signals(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and limit culture signals."""
        if v is None:
            return None
        # Limit to 5 signals
        return v[:5]


class CompanySearchResponse(BaseModel):
    """Response for company search."""

    companies: List[CompanyProfileResponse]
    total_count: int
