"""
Skill Gap Analysis Schemas

Pydantic models for skill-gap analysis requests and responses.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator


class UserSkillProfile(BaseModel):
    """
    User's skill profile for gap analysis.

    Can be provided explicitly or derived from user's resume data.
    """
    skills: List[str] = Field(default_factory=list, description="Technical and domain skills")
    capabilities: List[str] = Field(default_factory=list, description="High-level capabilities")
    bullet_tags: List[str] = Field(default_factory=list, description="Tags from resume bullets")
    seniority_levels: List[str] = Field(default_factory=list, description="Seniority levels from experience")
    relevance_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Skill relevance scores (0-1)"
    )


class SkillMatch(BaseModel):
    """
    A matched skill between user profile and job requirements.
    """
    skill: str = Field(..., description="The skill that matches")
    match_strength: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Strength of the match (0-1)"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Evidence from user's profile supporting this match"
    )


class SkillGap(BaseModel):
    """
    A skill gap between user profile and job requirements.
    """
    skill: str = Field(..., description="The missing or weak skill")
    importance: str = Field(
        ...,
        description="Importance level: 'critical', 'important', or 'nice-to-have'"
    )
    positioning_strategy: str = Field(
        ...,
        description="How to position/address this gap in application materials"
    )

    @field_validator('importance')
    @classmethod
    def validate_importance(cls, v: str) -> str:
        """Validate importance level."""
        allowed = ['critical', 'important', 'nice-to-have']
        if v.lower() not in allowed:
            raise ValueError(f"importance must be one of {allowed}")
        return v.lower()


class WeakSignal(BaseModel):
    """
    A skill where the user has weak evidence but could be strengthened.
    """
    skill: str = Field(..., description="The skill with weak signals")
    current_evidence: List[str] = Field(
        default_factory=list,
        description="Current weak evidence from user's profile"
    )
    strengthening_strategy: str = Field(
        ...,
        description="Strategy to strengthen this signal in application materials"
    )


class SkillGapRequest(BaseModel):
    """
    Request model for skill-gap analysis.
    """
    job_profile_id: int = Field(..., description="ID of the parsed job profile", gt=0)
    user_id: int = Field(..., description="User ID for analysis", gt=0)
    user_skill_profile: Optional[UserSkillProfile] = Field(
        None,
        description="Optional explicit user skill profile. If not provided, will be derived from user's data."
    )


class SkillGapResponse(BaseModel):
    """
    Response model for skill-gap analysis.

    Contains comprehensive analysis of skill matches, gaps, and positioning strategies.
    """
    job_profile_id: int = Field(..., description="ID of the analyzed job profile")
    user_id: int = Field(..., description="User ID for this analysis")

    # Overall assessment
    skill_match_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall skill match percentage (0-100)"
    )
    recommendation: str = Field(
        ...,
        description="Overall recommendation (e.g., 'strong_match', 'moderate_match', 'weak_match')"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the analysis (0-1)"
    )

    # Detailed analysis
    matched_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="Skills that match between user and job"
    )
    skill_gaps: List[SkillGap] = Field(
        default_factory=list,
        description="Skills missing or weak in user's profile"
    )
    weak_signals: List[WeakSignal] = Field(
        default_factory=list,
        description="Skills with weak evidence that could be strengthened"
    )

    # Positioning guidance
    key_positioning_angles: List[str] = Field(
        default_factory=list,
        description="3-5 key angles to position the user's experience for this role"
    )
    bullet_selection_guidance: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Guidance on which bullet types/tags to prioritize"
    )
    cover_letter_hooks: List[str] = Field(
        default_factory=list,
        description="Suggested hooks/themes for cover letter"
    )

    # Additional context
    user_advantages: List[str] = Field(
        default_factory=list,
        description="Unique advantages or differentiators the user brings"
    )
    potential_concerns: List[str] = Field(
        default_factory=list,
        description="Potential concerns hiring managers might have"
    )
    mitigation_strategies: Dict[str, str] = Field(
        default_factory=dict,
        description="Strategies to mitigate each potential concern"
    )

    # Metadata
    analysis_timestamp: str = Field(..., description="ISO timestamp of analysis")

    @field_validator('recommendation')
    @classmethod
    def validate_recommendation(cls, v: str) -> str:
        """Validate recommendation level."""
        allowed = ['strong_match', 'moderate_match', 'weak_match', 'stretch_role']
        if v.lower() not in allowed:
            raise ValueError(f"recommendation must be one of {allowed}")
        return v.lower()
