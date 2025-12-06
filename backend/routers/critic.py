"""
Critic Router

FastAPI endpoints for content evaluation and scoring.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import JobProfile
from schemas.critic import CriticEvaluateRequest, CriticResult
from services.critic import critic_pass


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/evaluate", response_model=CriticResult, status_code=status.HTTP_200_OK)
async def evaluate_content(
    request: CriticEvaluateRequest,
    db: Session = Depends(get_db)
) -> CriticResult:
    """
    Evaluate resume or cover letter content for quality and compliance.

    Performs comprehensive evaluation including:
    - Banned phrase detection with severity levels
    - Tone compliance checking against job description
    - Structure validation (required sections, word count)
    - ATS keyword scoring with detailed breakdown
    - Rule enforcement (immutability, constraints)

    Returns pass/fail decision with detailed issues and recommendations.

    **Request Body:**
    - `content_type`: "resume" or "cover_letter"
    - `job_profile_id`: Target job profile ID
    - `resume_json`: TailoredResume JSON (required if content_type="resume")
    - `cover_letter_json`: GeneratedCoverLetter JSON (required if content_type="cover_letter")
    - `strict_mode`: Treat warnings as failures (default: False)

    **Returns:**
    - `passed`: Overall pass/fail decision
    - `issues`: List of all issues found with severity and fixes
    - `ats_score`: Detailed ATS scoring breakdown
    - `structure_check`: Structure validation results
    - `quality_score`: Overall quality score (0-100)
    - `evaluation_summary`: Human-readable summary

    **Raises:**
    - `400 Bad Request`: Invalid request (missing content)
    - `404 Not Found`: Job profile not found
    - `422 Unprocessable Entity`: Invalid content structure
    - `500 Internal Server Error`: Unexpected error
    """
    try:
        # Validate content provided based on content_type
        if request.content_type == "resume":
            if not request.resume_json:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="resume_json required when content_type='resume'"
                )
            if request.cover_letter_json:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provide only resume_json when content_type='resume'"
                )
            content_json = request.resume_json

        elif request.content_type == "cover_letter":
            if not request.cover_letter_json:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="cover_letter_json required when content_type='cover_letter'"
                )
            if request.resume_json:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provide only cover_letter_json when content_type='cover_letter'"
                )
            content_json = request.cover_letter_json

        # Fetch job profile
        job_profile = db.query(JobProfile).filter(
            JobProfile.id == request.job_profile_id
        ).first()
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {request.job_profile_id} not found"
            )

        # Run critic evaluation
        result = await critic_pass(
            content_json=content_json,
            content_type=request.content_type,
            job_profile=job_profile,
            db=db,
            strict_mode=request.strict_mode
        )

        return result

    except HTTPException:
        raise
    except ValueError as e:
        # Log the actual error for debugging but return sanitized message
        logger.warning(f"Critic evaluation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid request content structure"
        )
    except Exception as e:
        logger.error(f"Critic evaluation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during evaluation"
        )
