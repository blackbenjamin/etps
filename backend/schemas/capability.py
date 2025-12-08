"""
Capability Cluster Schemas (Sprint 11)

Three-tier capability model for senior/strategic role matching:
- Tier 1: Capability Clusters (4-6 per role)
- Tier 2: Component Skills (3-8 per cluster)
- Tier 3: Evidence Skills (atomic, matchable)
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class EvidenceSkill(BaseModel):
    """
    Tier 3: Atomic, matchable skill.

    These are specific technologies, tools, or concrete skills that can be
    directly matched against resume content (e.g., "TensorFlow", "AWS", "Python").
    """
    name: str = Field(..., min_length=1, max_length=100, description="Skill name")
    category: str = Field(
        default="tech",
        description="Skill category: tech, domain, soft_skill, methodology"
    )
    matched: bool = Field(default=False, description="Whether user has this skill")
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence of match (0-1)"
    )
    evidence_bullet_ids: List[str] = Field(
        default_factory=list,
        description="IDs of resume bullets that demonstrate this skill"
    )


class ComponentSkill(BaseModel):
    """
    Tier 2: Component skill within a capability cluster.

    These represent sub-capabilities that together form a capability cluster
    (e.g., "roadmap creation", "stakeholder alignment" within "AI Strategy").
    """
    name: str = Field(..., min_length=1, max_length=200, description="Component skill name")
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Brief description of what this skill entails"
    )
    evidence_skills: List[EvidenceSkill] = Field(
        default_factory=list,
        description="Atomic skills that demonstrate this component"
    )
    required: bool = Field(
        default=True,
        description="Whether this is a must-have (True) or nice-to-have (False)"
    )
    matched: bool = Field(
        default=False,
        description="Whether user demonstrates this component skill"
    )
    match_strength: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Strength of match based on evidence (0-1)"
    )
    evidence_bullet_ids: List[str] = Field(
        default_factory=list,
        description="IDs of resume bullets that demonstrate this component"
    )


class CapabilityCluster(BaseModel):
    """
    Tier 1: High-level capability cluster.

    Represents a strategic capability area required for the role
    (e.g., "AI & Data Strategy", "Solution Architecture", "Client Advisory").
    """
    name: str = Field(..., min_length=1, max_length=100, description="Cluster name")
    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Description of what this capability entails"
    )
    component_skills: List[ComponentSkill] = Field(
        default_factory=list,
        description="Component skills that make up this cluster"
    )
    importance: str = Field(
        default="critical",
        description="Importance level: critical, important, nice-to-have"
    )
    match_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall match percentage for this cluster (0-100)"
    )
    user_evidence: List[str] = Field(
        default_factory=list,
        description="Bullet IDs that demonstrate capability in this cluster"
    )
    gaps: List[str] = Field(
        default_factory=list,
        description="Specific technologies/skills missing within this cluster"
    )
    positioning: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Positioning strategy for addressing gaps in this cluster"
    )
    is_expanded: bool = Field(
        default=True,
        description="UI state: whether cluster is expanded in view"
    )


class CapabilityClusterAnalysis(BaseModel):
    """
    Complete capability cluster analysis for a job profile.

    Contains all extracted clusters with match information, gaps,
    and positioning strategies.
    """
    job_profile_id: int = Field(..., description="Associated job profile ID")
    user_id: int = Field(default=1, description="User ID for the analysis")
    clusters: List[CapabilityCluster] = Field(
        default_factory=list,
        description="List of capability clusters for this role"
    )
    overall_match_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall match score across all clusters (0-100)"
    )
    recommendation: str = Field(
        default="moderate_match",
        description="Match recommendation: strong_match, moderate_match, stretch_role, weak_match"
    )
    positioning_summary: str = Field(
        default="",
        max_length=2000,
        description="Overall positioning strategy summary"
    )
    key_strengths: List[str] = Field(
        default_factory=list,
        description="Key strengths to emphasize (for cover letter)"
    )
    critical_gaps: List[str] = Field(
        default_factory=list,
        description="Critical gaps that must be addressed"
    )
    analysis_timestamp: Optional[str] = Field(
        default=None,
        description="ISO timestamp of when analysis was performed"
    )
    cache_key: Optional[str] = Field(
        default=None,
        description="Cache key for this analysis (SHA256 of JD text)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_profile_id": 123,
                "user_id": 1,
                "clusters": [
                    {
                        "name": "AI & Data Strategy",
                        "description": "Strategic leadership in AI/ML initiatives",
                        "importance": "critical",
                        "match_percentage": 85.0,
                        "component_skills": [
                            {
                                "name": "AI roadmap creation",
                                "required": True,
                                "matched": True,
                                "match_strength": 0.92
                            }
                        ],
                        "gaps": [],
                        "positioning": None
                    }
                ],
                "overall_match_score": 78.0,
                "recommendation": "strong_match",
                "positioning_summary": "Lead with AI strategy experience...",
                "key_strengths": ["AI/ML Strategy", "Cloud Architecture"],
                "critical_gaps": ["Digital Twins", "Transportation domain"]
            }
        }


# Request/Response schemas for API endpoints

class CapabilityClusterRequest(BaseModel):
    """Request to extract capability clusters from a job profile."""
    job_profile_id: int = Field(..., description="Job profile ID to analyze")
    user_id: int = Field(default=1, description="User ID for evidence mapping")
    force_refresh: bool = Field(
        default=False,
        description="Force re-extraction even if cached"
    )


class KeySkillSelection(BaseModel):
    """User-selected key skills for cover letter emphasis."""
    cluster_name: str = Field(..., description="Parent cluster name")
    skill_name: str = Field(..., description="Selected skill/component name")
    selected: bool = Field(default=True, description="Whether skill is selected")


class CapabilitySelectionUpdate(BaseModel):
    """Request to update capability cluster selections."""
    job_profile_id: int = Field(..., description="Job profile ID")
    key_skills: List[KeySkillSelection] = Field(
        default_factory=list,
        max_length=4,
        description="Selected key skills for cover letter (max 4)"
    )
    cluster_expansions: Optional[dict] = Field(
        default=None,
        description="UI state: {cluster_name: is_expanded}"
    )


class CapabilityClusterResponse(BaseModel):
    """Response containing capability cluster analysis."""
    analysis: CapabilityClusterAnalysis
    cached: bool = Field(
        default=False,
        description="Whether result was returned from cache"
    )
    cache_expires_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when cache expires"
    )
