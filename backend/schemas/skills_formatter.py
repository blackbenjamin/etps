"""
Skills Formatter Schemas

Pydantic models for LLM-based skills categorization with validation guardrails.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


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
