"""
Cover Letter Generation Schemas

Pydantic v2 models for cover letter generation request/response.
"""

from datetime import datetime
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field, field_validator


class CoverLetterRequest(BaseModel):
    """Request for cover letter generation."""
    job_profile_id: int = Field(..., description="Target job profile ID", gt=0)
    user_id: int = Field(..., description="User ID", gt=0)
    company_profile_id: Optional[int] = Field(
        None, description="Company profile ID if available", gt=0
    )
    context_notes: Optional[str] = Field(
        None, description="User-provided context notes", max_length=2000
    )
    referral_name: Optional[str] = Field(
        None, description="Name of referrer if applicable", max_length=255
    )
    company_name: Optional[str] = Field(
        None, description="Override company name (if manually entered)", max_length=255
    )


class CoverLetterOutline(BaseModel):
    """Structure outline used for cover letter."""
    introduction: str = Field(
        ..., description="Opening hook and purpose statement"
    )
    value_proposition: str = Field(
        ..., description="Core skills/experience alignment with role"
    )
    alignment: str = Field(
        ..., description="Company/role-specific fit and culture alignment"
    )
    call_to_action: str = Field(
        ..., description="Closing statement and next steps"
    )


class BannedPhraseViolation(BaseModel):
    """Individual banned phrase violation."""
    phrase: str = Field(..., description="The banned phrase detected")
    severity: Literal["critical", "major", "minor"] = Field(
        ..., description="Severity level of the violation"
    )
    section: str = Field(
        ..., description="Section where phrase was found (greeting/body/closing)"
    )


class BannedPhraseCheck(BaseModel):
    """Results of banned phrase detection."""
    violations_found: int = Field(
        ..., description="Total number of banned phrases detected", ge=0
    )
    violations: List[BannedPhraseViolation] = Field(
        default_factory=list, description="List of specific violations"
    )
    overall_severity: Literal["none", "minor", "major", "critical"] = Field(
        ..., description="Highest severity level found"
    )
    passed: bool = Field(
        ..., description="True if no critical or major violations"
    )


class ToneComplianceResult(BaseModel):
    """Tone alignment assessment."""
    target_tone: str = Field(
        ..., description="Expected tone from job description"
    )
    detected_tone: str = Field(
        ..., description="Detected tone in generated cover letter"
    )
    compliance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Tone match score (0-1)"
    )
    compatible: bool = Field(
        ..., description="True if tones are compatible"
    )
    tone_notes: str = Field(
        ..., description="Explanation of tone assessment"
    )


class ATSKeywordCoverage(BaseModel):
    """ATS keyword coverage analysis."""
    total_keywords: int = Field(
        ..., description="Total ATS keywords from job", ge=0
    )
    keywords_covered: int = Field(
        ..., description="Keywords present in cover letter", ge=0
    )
    coverage_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Keyword coverage percentage"
    )
    missing_critical_keywords: List[str] = Field(
        default_factory=list,
        description="Critical must-have keywords not present"
    )
    covered_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords successfully included"
    )
    coverage_adequate: bool = Field(
        ..., description="True if coverage meets threshold (>= 60%)"
    )


class RequirementCoverage(BaseModel):
    """Coverage of a single job requirement."""
    requirement: str = Field(..., description="The job requirement text")
    covered: bool = Field(..., description="Whether this requirement is addressed")
    evidence: Optional[str] = Field(
        None, description="How the requirement is addressed in the cover letter"
    )


class CoverLetterRationale(BaseModel):
    """Rationale for generation decisions."""
    outline_strategy: str = Field(
        ..., description="Why this outline structure was chosen"
    )
    tone_choice: str = Field(
        ..., description="Why this tone was selected"
    )
    keyword_strategy: str = Field(
        ..., description="How keywords were incorporated"
    )
    customization_notes: str = Field(
        ..., description="Specific customizations made for this application"
    )
    structure_template: str = Field(
        default="standard",
        description="Template used: standard (300w), executive (250w), or ultra_tight (175w)"
    )


class CriticIssue(BaseModel):
    """Individual issue identified by the critic."""
    category: Literal["banned_phrase", "tone", "ats_coverage", "structure", "content"] = Field(
        ..., description="Category of the issue"
    )
    severity: Literal["critical", "major", "minor"] = Field(
        ..., description="Severity level"
    )
    description: str = Field(
        ..., description="Detailed description of the issue"
    )
    suggestion: Optional[str] = Field(
        None, description="Suggested fix for the issue"
    )
    section: Optional[str] = Field(
        None, description="Section of cover letter affected"
    )


class CoverLetterCriticResult(BaseModel):
    """Results from critic evaluation of a cover letter draft."""
    iteration: int = Field(
        ..., ge=1, description="Current iteration number (1-indexed)"
    )
    quality_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall quality score (0-100)"
    )
    passed: bool = Field(
        ..., description="True if quality score meets threshold and no critical issues"
    )
    should_retry: bool = Field(
        ..., description="True if iteration loop should continue with revision"
    )

    # Detailed analysis components
    banned_phrase_check: BannedPhraseCheck = Field(
        ..., description="Banned phrase analysis"
    )
    tone_compliance: ToneComplianceResult = Field(
        ..., description="Tone compliance assessment"
    )
    ats_keyword_coverage: ATSKeywordCoverage = Field(
        ..., description="ATS keyword coverage analysis"
    )

    # Aggregated issues for revision feedback
    issues: List[CriticIssue] = Field(
        default_factory=list, description="All issues identified in this iteration"
    )
    retry_reasons: List[str] = Field(
        default_factory=list, description="Specific reasons for requesting revision"
    )
    improvement_suggestions: List[str] = Field(
        default_factory=list, description="Actionable suggestions for improvement"
    )

    # Comparison with previous iteration (if applicable)
    score_delta: Optional[float] = Field(
        None, description="Change in quality score from previous iteration"
    )
    issues_resolved: List[str] = Field(
        default_factory=list, description="Issues from previous iteration that were fixed"
    )

    evaluated_at: str = Field(
        ..., description="ISO timestamp of evaluation"
    )

    @field_validator('quality_score')
    @classmethod
    def round_quality_score(cls, v: float) -> float:
        """Round quality score to 1 decimal place."""
        return round(v, 1)


class GeneratedCoverLetter(BaseModel):
    """Complete cover letter generation response."""
    job_profile_id: int = Field(..., description="Job profile ID")
    user_id: int = Field(..., description="User ID")
    company_profile_id: Optional[int] = Field(
        None, description="Company profile ID if used"
    )
    company_name: Optional[str] = Field(
        None, description="Company name if available"
    )
    job_title: str = Field(..., description="Target job title")
    draft_cover_letter: str = Field(
        ..., description="Full cover letter text"
    )
    outline: CoverLetterOutline = Field(
        ..., description="Structure outline used"
    )
    banned_phrase_check: BannedPhraseCheck = Field(
        ..., description="Banned phrase violation results"
    )
    tone_compliance: ToneComplianceResult = Field(
        ..., description="Tone alignment assessment"
    )
    ats_keyword_coverage: ATSKeywordCoverage = Field(
        ..., description="ATS keyword analysis"
    )
    rationale: CoverLetterRationale = Field(
        ..., description="Generation decisions explained"
    )
    generated_at: str = Field(
        ..., description="ISO timestamp of generation"
    )
    quality_score: float = Field(
        ..., ge=0.0, le=100.0,
        description="Overall quality score (0-100)"
    )

    # New fields from style guide integration
    requirements_covered: List[RequirementCoverage] = Field(
        default_factory=list,
        description="Top 2-3 job requirements and how they are addressed"
    )
    mission_alignment_summary: Optional[str] = Field(
        None,
        description="Summary of how the letter aligns with company mission/positioning"
    )
    ats_keywords_used: List[str] = Field(
        default_factory=list,
        description="ATS keywords successfully incorporated in the letter"
    )

    # Critic iteration tracking
    iterations_used: int = Field(
        default=1, ge=1,
        description="Number of critic iterations performed"
    )
    final_critic_result: Optional["CoverLetterCriticResult"] = Field(
        None, description="Final critic evaluation result"
    )
    iteration_history: List["CoverLetterCriticResult"] = Field(
        default_factory=list,
        description="History of all critic evaluations across iterations"
    )
    critic_passed: bool = Field(
        default=True,
        description="Whether the final draft passed critic evaluation"
    )

    @field_validator('quality_score')
    @classmethod
    def round_quality_score(cls, v: float) -> float:
        """Round quality score to 1 decimal place."""
        return round(v, 1)


# Forward references for self-referential models
GeneratedCoverLetter.model_rebuild()
