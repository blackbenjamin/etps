"""
Skills Formatter Schemas

Pydantic models for LLM-based skills categorization with validation guardrails.
Supports both generic categorization and role-adaptive 3-category formatting.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SkillCategory(BaseModel):
    """
    A single skill category with its skills.

    Represents a logical grouping of skills for display in the resume.
    """
    category_name: str = Field(
        ...,
        description="Category name (e.g., 'AI/ML', 'Programming Languages')",
        min_length=1,
        max_length=50
    )
    skills: List[str] = Field(
        default_factory=list,
        description="List of skills in this category"
    )


class SkillsFormatterResponse(BaseModel):
    """
    Response from the skills formatter service.

    Contains categorized skills with validation status.
    """
    categories: List[SkillCategory] = Field(
        default_factory=list,
        description="Categorized skills for display"
    )
    validation_passed: bool = Field(
        ...,
        description="Whether all returned skills passed validation (exist in allowed list)"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Skills that were rejected (not in allowed skills list)"
    )
    fallback_used: bool = Field(
        default=False,
        description="Whether fallback categorization was used (LLM failed)"
    )


# Predefined skill categories with domain-specific patterns
# Used as explicit categories for the LLM to choose from
SKILL_CATEGORIES = [
    "AI/ML",  # AI, machine learning, NLP, deep learning, LLMs
    "Programming Languages & Frameworks",  # Python, SQL, R, JavaScript, etc.
    "Data Engineering & Analytics",  # ETL, pipelines, data warehousing
    "Cloud & Infrastructure",  # AWS, Azure, GCP, Docker, Kubernetes
    "Governance & Strategy",  # Data governance, strategy, compliance
    "Visualization & BI",  # Tableau, Power BI, dashboards
    "Other Technical Skills",  # Catch-all for uncategorized
]


# ============================================================================
# Role-Adaptive 3-Category Formatting (Approach 3)
# ============================================================================

class AdaptiveSkillCategory(BaseModel):
    """
    A skill category with adaptive, job-specific naming.

    Used for the 3-category formatting that adapts category names
    to the specific job type (e.g., "Payments & FinTech" for a payments role).
    """
    category_name: str = Field(
        ...,
        description="Job-adaptive category name (e.g., 'Payments & FinTech', 'AI & Strategy')",
        min_length=3,
        max_length=40
    )
    skills: List[str] = Field(
        default_factory=list,
        description="Skills in this category, ordered by relevance"
    )
    relevance_rank: int = Field(
        ...,
        description="Rank order (1=most relevant to job, 3=least relevant)",
        ge=1,
        le=3
    )

    @field_validator('relevance_rank')
    @classmethod
    def validate_relevance_rank(cls, v: int) -> int:
        """Ensure relevance_rank is 1, 2, or 3."""
        if v not in (1, 2, 3):
            raise ValueError(f"relevance_rank must be 1, 2, or 3, got {v}")
        return v


class ThreeCategoryFormatterResponse(BaseModel):
    """
    LLM response for exactly 3 role-adaptive skill categories.

    This is the primary response format for the hybrid Approach 3,
    which generates smart category names based on job type.
    """
    categories: List[AdaptiveSkillCategory] = Field(
        ...,
        description="Exactly 3 skill categories ordered by job relevance"
    )
    job_title: str = Field(
        ...,
        description="The job title used for category naming"
    )
    validation_passed: bool = Field(
        ...,
        description="Whether all returned skills passed validation"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Skills that were rejected (not in allowed list)"
    )
    fallback_used: bool = Field(
        default=False,
        description="Whether fallback categorization was used"
    )

    @field_validator('categories')
    @classmethod
    def validate_three_categories(cls, v: List[AdaptiveSkillCategory]) -> List[AdaptiveSkillCategory]:
        """Ensure exactly 3 categories with unique relevance ranks."""
        if len(v) != 3:
            raise ValueError(f"Must have exactly 3 categories, got {len(v)}")

        ranks = sorted([cat.relevance_rank for cat in v])
        if ranks != [1, 2, 3]:
            raise ValueError(f"Categories must have relevance ranks 1, 2, 3, got {ranks}")

        return sorted(v, key=lambda c: c.relevance_rank)
