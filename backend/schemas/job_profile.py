"""
Job Profile Schemas

Pydantic models for job profile API requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SelectedSkill(BaseModel):
    """A single skill in the user's selection."""
    skill: str = Field(..., min_length=1, max_length=100)
    match_pct: float = Field(..., ge=0.0, le=100.0)
    included: bool = True
    order: int = Field(..., ge=0)


class SkillSelectionUpdate(BaseModel):
    """Request to update skill selections for a job profile."""
    selected_skills: List[SelectedSkill] = Field(..., max_length=50)
    key_skills: List[str] = Field(default_factory=list, description="Max 4 key skills for cover letter")

    @field_validator('key_skills')
    @classmethod
    def validate_key_skills(cls, v: List[str]) -> List[str]:
        if len(v) > 4:
            raise ValueError("Maximum 4 key skills allowed")
        for skill in v:
            if len(skill) > 100:
                raise ValueError(f"Skill name too long: {skill}")
        return v

    @field_validator('selected_skills')
    @classmethod
    def validate_order_uniqueness(cls, v: List[SelectedSkill]) -> List[SelectedSkill]:
        orders = [s.order for s in v]
        if len(orders) != len(set(orders)):
            raise ValueError("Order values must be unique")
        return v


class SkillSelectionResponse(BaseModel):
    """Response after updating skill selection."""
    job_profile_id: int
    selected_skills: List[SelectedSkill]
    key_skills: List[str]
    updated_at: str


class SkillWithMatch(BaseModel):
    """Skill with match percentage for initial display."""
    skill: str
    match_pct: float
    source: str = "extracted"  # "extracted", "matched", "weak_signal"
