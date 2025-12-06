"""
Critic Service Schemas

Pydantic models for critic evaluation requests and responses.
"""

from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field, field_validator


# Issue types including new style enforcement types
ISSUE_TYPES = Literal[
    "banned_phrase",
    "em_dash_violation",
    "tone_mismatch",
    "structure_violation",
    "ats_keyword_missing",
    "rule_violation",
    "word_count_violation",
    "requirement_coverage",
    # New style enforcement issue types
    "passive_voice_violation",
    "weak_verb_violation",
    "filler_word_violation",
    "cliche_violation",
    "sentence_length_violation",
    "paragraph_violation",
    "comma_overuse_violation",
    "emotional_opening_violation",
    "generic_statement_violation",
    "structure_gap_violation",
    "truthfulness",
    # Pagination issue types
    "pagination_overflow",
    "pagination_orphan",
    "pagination_check_error",
]


class CriticEvaluateRequest(BaseModel):
    """
    Request for critic evaluation.

    Can evaluate either a TailoredResume or GeneratedCoverLetter.
    """
    content_type: Literal["resume", "cover_letter"] = Field(
        ..., description="Type of content to evaluate"
    )
    job_profile_id: int = Field(..., description="Job profile ID", gt=0)

    # For resume evaluation
    resume_json: Optional[Dict] = Field(
        None, description="TailoredResume JSON (if content_type='resume')"
    )

    # For cover letter evaluation
    cover_letter_json: Optional[Dict] = Field(
        None, description="GeneratedCoverLetter JSON (if content_type='cover_letter')"
    )

    # Optional overrides
    strict_mode: bool = Field(
        default=False,
        description="If True, treat warnings as failures"
    )


class CriticIssue(BaseModel):
    """
    Individual issue found during critic evaluation.
    """
    issue_type: ISSUE_TYPES = Field(..., description="Type of issue")

    severity: Literal["error", "warning", "info"] = Field(
        ..., description="Severity level (error=blocking, warning=non-blocking)"
    )

    section: Optional[str] = Field(
        None, description="Section where issue was found"
    )

    message: str = Field(
        ..., description="Human-readable description of the issue"
    )

    original_text: Optional[str] = Field(
        None, description="Problematic text snippet (if applicable)"
    )

    recommended_fix: Optional[str] = Field(
        None, description="Suggested fix or improvement"
    )


class ATSScoreBreakdown(BaseModel):
    """
    Detailed breakdown of ATS scoring.
    """
    overall_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall ATS score (0-100)"
    )

    keyword_score: float = Field(
        ..., ge=0.0, le=100.0, description="Keyword match score"
    )

    format_score: float = Field(
        ..., ge=0.0, le=100.0, description="Format/structure score"
    )

    skills_score: float = Field(
        ..., ge=0.0, le=100.0, description="Skills section score"
    )

    total_keywords: int = Field(..., ge=0, description="Total keywords identified")
    keywords_matched: int = Field(..., ge=0, description="Keywords matched")
    keywords_missing: List[str] = Field(
        default_factory=list, description="Critical missing keywords"
    )

    @field_validator('overall_score', 'keyword_score', 'format_score', 'skills_score')
    @classmethod
    def round_scores(cls, v: float) -> float:
        """Round scores to 1 decimal place."""
        return round(v, 1)


class StructureCheckResult(BaseModel):
    """
    Results of structure/format checking.
    """
    has_required_sections: bool = Field(
        ..., description="Whether all required sections are present"
    )

    missing_sections: List[str] = Field(
        default_factory=list, description="Missing required sections"
    )

    word_count: int = Field(..., ge=0, description="Total word count")

    word_count_valid: bool = Field(
        ..., description="Whether word count is within acceptable range"
    )

    expected_range: str = Field(
        ..., description="Expected word count range"
    )


class CriticResult(BaseModel):
    """
    Complete critic evaluation result.

    Unified output for both resume and cover letter evaluations.
    """
    content_type: Literal["resume", "cover_letter"] = Field(
        ..., description="Type of content evaluated"
    )

    passed: bool = Field(
        ..., description="Overall pass/fail (False if any blocking issues)"
    )

    issues: List[CriticIssue] = Field(
        default_factory=list, description="All issues found"
    )

    error_count: int = Field(..., ge=0, description="Number of blocking errors")
    warning_count: int = Field(..., ge=0, description="Number of non-blocking warnings")
    info_count: int = Field(..., ge=0, description="Number of informational notes")

    ats_score: ATSScoreBreakdown = Field(
        ..., description="Detailed ATS scoring breakdown"
    )

    structure_check: StructureCheckResult = Field(
        ..., description="Structure/format validation results"
    )

    quality_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall quality score (0-100)"
    )

    evaluation_summary: str = Field(
        ..., description="Human-readable summary of evaluation"
    )

    evaluated_at: str = Field(
        ..., description="ISO timestamp of evaluation"
    )

    @field_validator('quality_score')
    @classmethod
    def round_quality_score(cls, v: float) -> float:
        """Round quality score to 1 decimal place."""
        return round(v, 1)


class RequirementCoverageScore(BaseModel):
    """Score for requirement coverage in cover letter evaluation."""
    total_requirements: int = Field(..., ge=0, description="Total top requirements identified")
    requirements_covered: int = Field(..., ge=0, description="Requirements addressed in letter")
    coverage_percentage: float = Field(..., ge=0.0, le=100.0, description="Coverage percentage")


class StyleScoreBreakdown(BaseModel):
    """
    Detailed breakdown of style enforcement scoring.

    The overall_style_score is a weighted average:
    - tone_score: 30%
    - structure_score: 30%
    - lexical_score: 20%
    - conciseness_score: 20%

    A score below 85 results in automatic failure.
    """
    tone_score: int = Field(
        ..., ge=0, le=100, description="Tone analysis score (executive, direct, concise)"
    )
    structure_score: int = Field(
        ..., ge=0, le=100, description="Structure validation score (4 required sections)"
    )
    lexical_score: int = Field(
        ..., ge=0, le=100, description="Lexical quality score (strong verbs, no filler)"
    )
    conciseness_score: int = Field(
        ..., ge=0, le=100, description="Conciseness score (sentence length, comma density)"
    )
    overall_style_score: int = Field(
        ..., ge=0, le=100, description="Overall style score (weighted average)"
    )

    # Detailed metrics
    passive_voice_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Rate of passive voice sentences (0-1)"
    )
    weak_verb_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Rate of weak verb usage (0-1)"
    )
    avg_sentence_length: float = Field(
        default=0.0, ge=0.0, description="Average words per sentence"
    )
    max_sentence_length: int = Field(
        default=0, ge=0, description="Maximum sentence length in words"
    )

    # Structure validation details
    has_value_opening: bool = Field(
        default=True, description="Opening paragraph is value-oriented"
    )
    has_jd_alignment: bool = Field(
        default=True, description="Addresses 2-3 top JD requirements"
    )
    has_company_connection: bool = Field(
        default=True, description="Meaningful company/mission connection"
    )
    has_impact_closing: bool = Field(
        default=True, description="Closing is impact-oriented"
    )


class ResumeCriticResult(BaseModel):
    """
    Critic result specifically for resume evaluation.

    Implements PRD 4.3 resume rubric:
    - Alignment to JD requirements
    - Clarity and conciseness of bullets
    - Impact orientation (achievements, metrics)
    - Tone (executive, direct, professional)
    - No hallucinations
    - ATS keyword coverage
    - Skills relevance
    - Proper action verbs
    """
    content_type: Literal["resume"] = Field(
        default="resume", description="Content type (always resume)"
    )

    passed: bool = Field(
        ..., description="Overall pass/fail (False if any blocking issues)"
    )

    issues: List[CriticIssue] = Field(
        default_factory=list, description="All issues found"
    )

    error_count: int = Field(..., ge=0, description="Number of blocking errors")
    warning_count: int = Field(..., ge=0, description="Number of non-blocking warnings")
    info_count: int = Field(..., ge=0, description="Number of informational notes")

    # Resume-specific scores
    alignment_score: float = Field(
        ..., ge=0.0, le=100.0, description="JD alignment score (0-100)"
    )
    clarity_score: float = Field(
        ..., ge=0.0, le=100.0, description="Clarity and conciseness score (0-100)"
    )
    impact_score: float = Field(
        ..., ge=0.0, le=100.0, description="Impact orientation score (0-100)"
    )
    tone_score: float = Field(
        ..., ge=0.0, le=100.0, description="Tone appropriateness score (0-100)"
    )

    ats_score: ATSScoreBreakdown = Field(
        ..., description="Detailed ATS scoring breakdown"
    )

    structure_check: StructureCheckResult = Field(
        ..., description="Structure/format validation results"
    )

    # Hallucination detection
    hallucination_check_passed: bool = Field(
        default=True, description="Whether content passes hallucination checks"
    )
    hallucination_issues: List[str] = Field(
        default_factory=list, description="Specific hallucination concerns found"
    )

    # Bullet quality metrics
    bullets_with_metrics: int = Field(
        default=0, ge=0, description="Number of bullets containing quantifiable metrics"
    )
    bullets_total: int = Field(
        default=0, ge=0, description="Total number of bullets"
    )
    weak_verb_count: int = Field(
        default=0, ge=0, description="Number of bullets with weak verbs"
    )

    quality_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall quality score (0-100)"
    )

    evaluation_summary: str = Field(
        ..., description="Human-readable summary of evaluation"
    )

    evaluated_at: str = Field(
        ..., description="ISO timestamp of evaluation"
    )

    iteration: int = Field(
        default=1, ge=1, description="Critic iteration number"
    )

    should_retry: bool = Field(
        default=False, description="Whether the resume should be regenerated"
    )

    @field_validator('quality_score', 'alignment_score', 'clarity_score', 'impact_score', 'tone_score')
    @classmethod
    def round_score(cls, v: float) -> float:
        """Round scores to 1 decimal place."""
        return round(v, 1)


class CoverLetterCriticResult(BaseModel):
    """
    Extended critic result specifically for cover letter evaluation.

    Includes requirement coverage checking per style guide Section 6.
    """
    content_type: Literal["cover_letter"] = Field(
        default="cover_letter", description="Content type (always cover_letter)"
    )

    passed: bool = Field(
        ..., description="Overall pass/fail (False if any blocking issues)"
    )

    issues: List[CriticIssue] = Field(
        default_factory=list, description="All issues found"
    )

    error_count: int = Field(..., ge=0, description="Number of blocking errors")
    warning_count: int = Field(..., ge=0, description="Number of non-blocking warnings")
    info_count: int = Field(..., ge=0, description="Number of informational notes")

    ats_score: ATSScoreBreakdown = Field(
        ..., description="Detailed ATS scoring breakdown"
    )

    structure_check: StructureCheckResult = Field(
        ..., description="Structure/format validation results"
    )

    requirement_coverage: RequirementCoverageScore = Field(
        ..., description="Requirement coverage assessment"
    )

    style_score: Optional[StyleScoreBreakdown] = Field(
        default=None, description="Detailed style enforcement scoring"
    )

    em_dash_count: int = Field(
        default=0, ge=0, description="Number of em-dashes found (should be 0)"
    )

    quality_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall quality score (0-100)"
    )

    evaluation_summary: str = Field(
        ..., description="Human-readable summary of evaluation"
    )

    evaluated_at: str = Field(
        ..., description="ISO timestamp of evaluation"
    )

    @field_validator('quality_score')
    @classmethod
    def round_quality_score(cls, v: float) -> float:
        """Round quality score to 1 decimal place."""
        return round(v, 1)
