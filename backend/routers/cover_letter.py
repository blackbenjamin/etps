"""
Cover Letter Router

FastAPI endpoints for cover letter generation with critic integration.
"""

import logging
import re
from typing import Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, Response, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import JobProfile, User
from schemas.cover_letter import CoverLetterRequest, GeneratedCoverLetter
from schemas.critic import CoverLetterCriticResult
from services.cover_letter import generate_cover_letter
from services.critic import evaluate_cover_letter
from services.docx_cover_letter import create_cover_letter_docx
from services.text_cover_letter import create_cover_letter_text


logger = logging.getLogger(__name__)
router = APIRouter()


class CoverLetterWithCriticResponse(BaseModel):
    """Response with generated cover letter and critic evaluation."""
    cover_letter: GeneratedCoverLetter = Field(..., description="Generated cover letter")
    critic_result: CoverLetterCriticResult = Field(..., description="Critic evaluation result")
    accepted: bool = Field(..., description="True if critic passed (no blocking issues)")


class CoverLetterDocxRejectedResponse(BaseModel):
    """Response when cover letter DOCX generation is rejected by critic."""
    accepted: bool = Field(default=False, description="Always False for rejected responses")
    critic_result: CoverLetterCriticResult = Field(..., description="Critic evaluation with issues")
    cover_letter: GeneratedCoverLetter = Field(..., description="Generated cover letter (for review)")
    message: str = Field(
        default="Cover letter failed critic evaluation. Review issues and regenerate.",
        description="Human-readable rejection message"
    )


@router.post("/generate", response_model=GeneratedCoverLetter, status_code=status.HTTP_200_OK)
async def generate_cover_letter_endpoint(
    request: CoverLetterRequest,
    db: Session = Depends(get_db)
) -> GeneratedCoverLetter:
    """
    Generate tailored cover letter for job application.

    Creates a personalized cover letter with:
    - Tone aligned to job description style
    - ATS keyword optimization
    - Banned phrase avoidance (including em-dashes per style guide)
    - Company-specific customization (if company profile provided)
    - Requirement coverage tracking (top 2-3 JD requirements)

    **Request Body:**
    - `job_profile_id` (int, required): Target job profile ID
    - `user_id` (int, required): User ID
    - `company_profile_id` (int, optional): Company profile for customization
    - `context_notes` (str, optional): User-provided context notes
    - `referral_name` (str, optional): Name of referrer if applicable

    **Returns:**
    - Complete cover letter draft
    - Structured outline used (intro/value/alignment/close)
    - Banned phrase check results with violations
    - Tone compliance assessment with score
    - ATS keyword coverage analysis
    - Requirement coverage (top 2-3 JD requirements addressed)
    - Mission alignment summary (if company profile provided)
    - Rationale explaining generation decisions
    - Overall quality score (0-100)

    **Raises:**
    - `404 Not Found`: User, job profile, or company profile not found
    - `500 Internal Server Error`: Unexpected error during generation
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )

        # Generate cover letter
        cover_letter = await generate_cover_letter(
            job_profile_id=request.job_profile_id,
            user_id=request.user_id,
            db=db,
            company_profile_id=request.company_profile_id,
            context_notes=request.context_notes,
            referral_name=request.referral_name,
        )

        return cover_letter

    except ValueError as e:
        error_msg = str(e)
        # 404 only for "not found" errors
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            # Other validation errors (e.g., missing required data)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg
            )
    except Exception as e:
        # Log the exception for debugging
        logger.error(f"Cover letter generation failed: {str(e)}", exc_info=True)
        # Handle unexpected errors - sanitize error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the cover letter"
        )


@router.post(
    "/generate-with-critic",
    response_model=CoverLetterWithCriticResponse,
    status_code=status.HTTP_200_OK
)
async def generate_cover_letter_with_critic_endpoint(
    request: CoverLetterRequest,
    strict_mode: bool = Query(
        default=False,
        description="If True, treat warnings as blocking issues"
    ),
    db: Session = Depends(get_db)
) -> CoverLetterWithCriticResponse:
    """
    Generate cover letter with critic evaluation.

    Generates a cover letter and runs it through the critic for evaluation.
    Returns both the generated letter and critic feedback.

    **Critic checks:**
    - Em-dash detection (banned punctuation per style guide)
    - Banned phrase detection
    - Tone compliance
    - Structure validation
    - ATS keyword coverage
    - Requirement coverage (top 2-3 JD requirements)
    - Word count validation

    **Request Body:**
    - `job_profile_id` (int, required): Target job profile ID
    - `user_id` (int, required): User ID
    - `company_profile_id` (int, optional): Company profile for customization
    - `context_notes` (str, optional): User-provided context notes
    - `referral_name` (str, optional): Name of referrer if applicable

    **Query Parameters:**
    - `strict_mode` (bool, optional): If True, warnings become blocking issues

    **Returns:**
    - `cover_letter`: Generated cover letter with all analysis
    - `critic_result`: Detailed critic evaluation including:
        - Pass/fail status
        - All issues found with severity levels
        - ATS score breakdown
        - Structure check results
        - Requirement coverage score
        - Em-dash count
        - Quality score
    - `accepted`: True if critic passed (letter acceptable)

    **Raises:**
    - `404 Not Found`: User, job profile, or company profile not found
    - `500 Internal Server Error`: Unexpected error during generation
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )

        # Generate cover letter
        cover_letter = await generate_cover_letter(
            job_profile_id=request.job_profile_id,
            user_id=request.user_id,
            db=db,
            company_profile_id=request.company_profile_id,
            context_notes=request.context_notes,
            referral_name=request.referral_name,
        )

        # Get job profile for critic evaluation
        job_profile = db.query(JobProfile).filter(
            JobProfile.id == request.job_profile_id
        ).first()

        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {request.job_profile_id} not found"
            )

        # Run critic evaluation
        critic_result = await evaluate_cover_letter(
            cover_letter_json=cover_letter.model_dump(),
            job_profile=job_profile,
            db=db,
            strict_mode=strict_mode
        )

        return CoverLetterWithCriticResponse(
            cover_letter=cover_letter,
            critic_result=critic_result,
            accepted=critic_result.passed
        )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg
            )
    except Exception as e:
        logger.error(f"Cover letter generation with critic failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the cover letter"
        )


def _sanitize_filename(name: str) -> str:
    """Sanitize a string for use in a filename.

    Handles:
    - Invalid filesystem characters
    - Leading/trailing dots and spaces
    - Empty or whitespace-only strings
    - Length limits (accounting for .docx extension)
    """
    if not name or not name.strip():
        return "document"

    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    # Limit length (leave room for path prefixes and .docx extension)
    sanitized = sanitized[:45]

    # Fallback if all characters were removed
    return sanitized or "document"


@router.post(
    "/docx",
    response_model=None,  # Return type varies (Response or JSON)
    responses={
        200: {
            "content": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}},
            "description": "DOCX file bytes when critic passes"
        },
        422: {
            "model": CoverLetterDocxRejectedResponse,
            "description": "JSON response with critic issues when evaluation fails"
        }
    },
    status_code=status.HTTP_200_OK
)
async def generate_cover_letter_docx_endpoint(
    request: CoverLetterRequest,
    recipient_name: Optional[str] = Query(
        default=None,
        description="Recipient name (default: 'Hiring Team')"
    ),
    strict_mode: bool = Query(
        default=False,
        description="If True, treat warnings as blocking issues"
    ),
    format: Literal["docx", "text", "json"] = Query(
        default="docx",
        description="Output format: docx (Word document), text (plain text), json (GeneratedCoverLetter JSON)"
    ),
    db: Session = Depends(get_db)
):
    """
    Generate cover letter with critic validation in the specified format.

    Generates a cover letter, runs it through the critic, and if it passes,
    returns the letter in one of three formats:
    - DOCX: Professionally formatted Word document (.docx) matching Benjamin Black's template
    - Text: ATS-friendly plain text with business letter format
    - JSON: Returns the GeneratedCoverLetter JSON object directly

    **Workflow:**
    1. Generate cover letter JSON (with style guide compliance)
    2. Run critic evaluation (em-dash, banned phrases, tone, structure)
    3. If critic passes: Return in requested format
    4. If critic fails: Return JSON with issues for review (422 status)

    **DOCX Template formatting:**
    - Georgia font throughout
    - Centered header (name 16pt bold, contact 10.5pt)
    - Right-aligned date (11pt)
    - Left-aligned recipient and body
    - Proper spacing between sections
    - Signature block at end

    **Text Format:**
    - Business letter format
    - Contact info header
    - Date and recipient
    - Body paragraphs
    - Signature

    **Request Body:**
    - `job_profile_id` (int, required): Target job profile ID
    - `user_id` (int, required): User ID
    - `company_profile_id` (int, optional): Company profile for customization
    - `context_notes` (str, optional): User-provided context notes
    - `referral_name` (str, optional): Name of referrer if applicable

    **Query Parameters:**
    - `recipient_name` (str, optional): Name for greeting (default: "Hiring Team")
    - `strict_mode` (bool, optional): If True, warnings become blocking issues
    - `format` (str, optional): Output format - "docx" (default), "text", or "json"

    **Returns (200 OK):**
    - DOCX file (format=docx): Binary response with download headers
    - Plain text (format=text): Text response with .txt download headers
    - JSON (format=json): JSON response with GeneratedCoverLetter object

    **Returns (422 Unprocessable Entity):**
    - JSON with critic issues, cover letter, and rejection message

    **Raises:**
    - `404 Not Found`: User, job profile, or company profile not found
    - `500 Internal Server Error`: Unexpected error during generation
    """
    try:
        # Validate user exists and get user details
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )

        # Generate cover letter
        cover_letter = await generate_cover_letter(
            job_profile_id=request.job_profile_id,
            user_id=request.user_id,
            db=db,
            company_profile_id=request.company_profile_id,
            context_notes=request.context_notes,
            referral_name=request.referral_name,
        )

        # Get job profile for critic evaluation
        job_profile = db.query(JobProfile).filter(
            JobProfile.id == request.job_profile_id
        ).first()

        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {request.job_profile_id} not found"
            )

        # Run critic evaluation
        critic_result = await evaluate_cover_letter(
            cover_letter_json=cover_letter.model_dump(),
            job_profile=job_profile,
            db=db,
            strict_mode=strict_mode
        )

        # If critic fails, return JSON with issues (422 status)
        if not critic_result.passed:
            rejection_response = CoverLetterDocxRejectedResponse(
                accepted=False,
                critic_result=critic_result,
                cover_letter=cover_letter,
                message=(
                    f"Cover letter failed critic evaluation with {critic_result.error_count} error(s) "
                    f"and {critic_result.warning_count} warning(s). Review issues and regenerate."
                )
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=rejection_response.model_dump()
            )

        # Build filename base
        company_part = _sanitize_filename(cover_letter.company_name) if cover_letter.company_name else "Unknown"
        job_part = _sanitize_filename(cover_letter.job_title) if cover_letter.job_title else "Position"

        # Handle format selection
        if format == "json":
            # Return GeneratedCoverLetter as JSON
            filename = f"Cover_Letter_{company_part}_{job_part}.json"
            return JSONResponse(
                content=cover_letter.model_dump(),
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )

        elif format == "text":
            # Generate plain text cover letter
            text_content = create_cover_letter_text(
                cover_letter=cover_letter,
                user_name=user.full_name,
                user_email=user.email,
                user_phone=getattr(user, 'phone', None),
                user_linkedin=getattr(user, 'linkedin_url', None),
                recipient_name=recipient_name,
                company_name=cover_letter.company_name
            )

            filename = f"Cover_Letter_{company_part}_{job_part}.txt"
            return PlainTextResponse(
                content=text_content,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )

        else:  # format == "docx" (default)
            # Generate DOCX
            docx_bytes = create_cover_letter_docx(
                cover_letter=cover_letter,
                user_name=user.full_name,
                user_email=user.email,
                user_phone=getattr(user, 'phone', None),
                user_linkedin=getattr(user, 'linkedin_url', None),
                recipient_name=recipient_name
            )

            filename = f"Cover_Letter_{company_part}_{job_part}.docx"
            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg
            )
    except Exception as e:
        logger.error(f"Cover letter DOCX generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the cover letter DOCX"
        )
