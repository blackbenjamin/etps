"""
Approved Output Schemas

Pydantic v2 models for approved output approval and retrieval.
"""

from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ApproveOutputRequest(BaseModel):
    """Request to approve and store an output."""
    user_id: int = Field(..., description="User ID", gt=0)
    output_type: Literal[
        'resume_bullet',
        'cover_letter_paragraph',
        'professional_summary',
        'full_resume',
        'full_cover_letter'
    ] = Field(..., description="Type of output being approved")
    original_text: str = Field(
        ..., description="The approved output text", min_length=1, max_length=10000
    )
    application_id: Optional[int] = Field(
        None, description="Associated application ID if applicable", gt=0
    )
    job_profile_id: Optional[int] = Field(
        None, description="Associated job profile ID if applicable", gt=0
    )
    context_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Context metadata (job_title, requirements_snippet, tags, seniority)"
    )
    quality_score: Optional[float] = Field(
        None, description="Quality score (0.0-1.0)", ge=0.0, le=1.0
    )

    @field_validator('original_text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("original_text cannot be empty or whitespace only")
        return v


class ApproveOutputResponse(BaseModel):
    """Response after approving an output."""
    approved_output_id: int = Field(..., description="ID of the created approved output")
    user_id: int = Field(..., description="User ID")
    output_type: str = Field(..., description="Type of output")
    original_text: str = Field(..., description="The approved text")
    quality_score: Optional[float] = Field(None, description="Quality score")
    indexed: bool = Field(..., description="Whether output was indexed in vector store")
    created_at: str = Field(..., description="ISO timestamp of creation")

    @field_validator('quality_score')
    @classmethod
    def round_quality_score(cls, v: Optional[float]) -> Optional[float]:
        """Round quality score to 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v


class SimilarOutput(BaseModel):
    """A single similar approved output result."""
    output_id: int = Field(..., description="ID of the approved output")
    output_type: str = Field(..., description="Type of output")
    text: str = Field(..., description="The output text")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    quality_score: Optional[float] = Field(None, description="Quality score if available")
    created_at: Optional[str] = Field(None, description="ISO timestamp of creation")
    application_id: Optional[int] = Field(None, description="Associated application ID")

    @field_validator('similarity_score', 'quality_score')
    @classmethod
    def round_scores(cls, v: Optional[float]) -> Optional[float]:
        """Round scores to 2 decimal places."""
        if v is not None:
            return round(v, 2)
        return v


class SimilarOutputsResponse(BaseModel):
    """Response containing similar approved outputs."""
    query_text: str = Field(..., description="Query text used for search")
    user_id: int = Field(..., description="User ID")
    output_type: Optional[str] = Field(None, description="Output type filter if applied")
    results: List[SimilarOutput] = Field(
        default_factory=list, description="List of similar outputs"
    )
    total_found: int = Field(..., ge=0, description="Total number of results found")
    limit: int = Field(..., gt=0, description="Limit applied to results")
    min_quality_score: Optional[float] = Field(
        None, description="Minimum quality score filter if applied"
    )
