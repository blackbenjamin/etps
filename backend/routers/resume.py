"""
Resume Router

FastAPI endpoints for resume tailoring and generation.
Provides intelligent resume optimization based on job requirements.
"""

import logging
import re
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response, PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import JobProfile, User, Bullet
from schemas.resume_tailor import TailorResumeRequest, TailoredResume, ResumeDocxRequest
from services.resume_tailor import tailor_resume
from services.docx_resume import create_resume_docx, create_resume_docx_async
from services.text_resume import create_resume_text
from services.llm import create_llm
from middleware import limiter


logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/generate", response_model=TailoredResume, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def generate_tailored_resume(
    request: Request,
    body: TailorResumeRequest,
    db: Session = Depends(get_db)
) -> TailoredResume:
    """
    Generate a tailored resume optimized for a specific job profile.

    Intelligently selects and optimizes resume content (bullets, skills, summary)
    to maximize alignment with job requirements. Uses multi-factor scoring to
    select the most relevant bullets, orders skills by priority, and generates
    a customized professional summary.

    **Request Body:**
    - `job_profile_id` (int, required): ID of the parsed job profile to tailor for
    - `user_id` (int, required): User ID for resume tailoring
    - `template_id` (int, optional): Specific template ID for formatting
    - `max_bullets_per_role` (int, default=4): Maximum bullets per role (2-8)
    - `max_skills` (int, default=12): Maximum skills in skills section (5-20)
    - `custom_instructions` (str, optional): User-provided tailoring instructions

    **Tailoring Strategy:**
    - **Bullet Selection**: Multi-factor scoring (40% tag matching, 30% relevance,
      20% usage/freshness, 10% type diversity)
    - **Skills Ordering**: Tier-based approach prioritizing critical matched skills,
      strong matches, must-have requirements, and transferable skills
    - **Summary Generation**: LLM-generated summary emphasizing matched skills and
      job priorities, avoiding generic phrases

    **Returns:**
    - Complete tailored resume with selected roles, bullets, skills, and summary
    - Comprehensive rationale explaining all tailoring decisions
    - Match score indicating alignment with job requirements
    - Validation status for all constraints

    **Raises:**
    - `404 Not Found`: User or job profile not found
    - `500 Internal Server Error`: Unexpected error during generation
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == body.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {body.user_id} not found"
            )

        # Validate job profile exists
        job_profile = db.query(JobProfile).filter(JobProfile.id == body.job_profile_id).first()
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {body.job_profile_id} not found"
            )

        # Generate tailored resume using service with real LLM if available
        llm = create_llm()  # Uses Claude if ANTHROPIC_API_KEY is set, else MockLLM
        tailored_resume = await tailor_resume(
            job_profile_id=body.job_profile_id,
            user_id=body.user_id,
            db=db,
            max_bullets_per_role=body.max_bullets_per_role,
            max_skills=body.max_skills,
            custom_instructions=body.custom_instructions,
            llm=llm,
        )

        return tailored_resume

    except HTTPException:
        raise
    except ValueError as e:
        # Handle validation errors and not found errors
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors - sanitize error message
        logger.error(f"Resume generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the tailored resume"
        )


@router.post("/docx", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def generate_resume_docx(
    request: Request,
    body: ResumeDocxRequest,
    format: Literal["docx", "text", "json"] = Query(
        default="docx",
        description="Output format: docx (Word document), text (plain text), json (TailoredResume JSON)"
    ),
    db: Session = Depends(get_db)
):
    """
    Generate a resume from a TailoredResume JSON in the specified format.

    Takes a previously generated TailoredResume object and renders it in one of three formats:
    - DOCX: Professionally formatted Word document (.docx) matching the Benjamin Black template
    - Text: ATS-friendly plain text with ASCII-only characters
    - JSON: Returns the TailoredResume JSON object directly

    **Request Body:**
    - `tailored_resume` (TailoredResume, required): The tailored resume JSON
    - `user_name` (str, required): Full name for the resume header
    - `user_email` (str, required): Email address for the header
    - `user_phone` (str, optional): Phone number for the header
    - `user_linkedin` (str, optional): LinkedIn URL/handle for the header
    - `user_portfolio` (str, optional): Portfolio/GitHub URL for the resume header
    - `education` (list[EducationEntry], optional): Education entries to include

    **Query Parameters:**
    - `format` (str, optional): Output format - "docx" (default), "text", or "json"

    **DOCX Format:**
    - Page: 8.5" x 11" with 0.9" top, 0.56" bottom, 0.5" left/right margins
    - Font: Georgia throughout
    - Header: Name (16pt bold centered), contact info (10.5pt centered)
    - Sections: Professional Experience, Technical Skills, Education
    - Bullets: Hanging indent style with bullet points

    **Text Format:**
    - ASCII-only characters (use -, not bullets)
    - Section headers with === underlines
    - 2 blank lines between sections
    - Header: NAME (all caps), contact line with | separators

    **JSON Format:**
    - Returns the TailoredResume object as JSON

    **Returns:**
    - DOCX file (format=docx): Binary response with download headers
    - Plain text (format=text): Text response with .txt download headers
    - JSON (format=json): JSON response with TailoredResume object

    **Raises:**
    - `400 Bad Request`: Invalid request structure
    - `422 Unprocessable Entity`: Invalid content (e.g., empty resume)
    - `500 Internal Server Error`: Generation failed
    """
    try:
        # Validate we have content to render
        if not body.tailored_resume.selected_roles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TailoredResume must have at least one selected role"
            )

        # Convert education entries to dict format for services
        education_dicts = [
            {
                "institution": edu.institution,
                "location": edu.location,
                "degree": edu.degree,
                "details": edu.details
            }
            for edu in body.education
        ] if body.education else None

        # Create filename base from user name with robust sanitization
        safe_name = re.sub(r'[^\w\s-]', '', body.user_name, flags=re.UNICODE)
        safe_name = re.sub(r'[-\s]+', '_', safe_name).strip('_')
        safe_name = safe_name or "Resume"  # Fallback for empty/invalid names

        # Handle format selection
        if format == "json":
            # Return TailoredResume as JSON
            return JSONResponse(
                content=body.tailored_resume.model_dump(),
                headers={
                    "Content-Disposition": f'attachment; filename="{safe_name}_Resume.json"'
                }
            )

        elif format == "text":
            # Generate plain text resume
            text_content = create_resume_text(
                tailored_resume=body.tailored_resume,
                user_name=body.user_name,
                user_email=body.user_email,
                user_phone=body.user_phone,
                user_linkedin=body.user_linkedin,
                user_portfolio=body.user_portfolio,
                education=education_dicts
            )

            filename = f"{safe_name}_Resume.txt"
            return PlainTextResponse(
                content=text_content,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )

        else:  # format == "docx" (default)
            # Create LLM for skills categorization
            llm = create_llm()

            # Get target job title from request, job profile, or use fallback
            job_title = body.job_title
            if not job_title:
                # Try to get from job profile in database
                job_profile = db.query(JobProfile).filter(
                    JobProfile.id == body.tailored_resume.job_profile_id
                ).first()
                if job_profile:
                    job_title = job_profile.job_title
            if not job_title:
                job_title = "Professional"

            # Generate DOCX with LLM-powered skills categorization
            docx_bytes = await create_resume_docx_async(
                tailored_resume=body.tailored_resume,
                user_name=body.user_name,
                user_email=body.user_email,
                user_phone=body.user_phone,
                user_linkedin=body.user_linkedin,
                user_portfolio=body.user_portfolio,
                education=education_dicts,
                llm=llm,
                job_title=job_title
            )

            filename = f"{safe_name}_Resume.docx"
            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Resume generation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid resume content structure"
        )
    except Exception as e:
        logger.error(f"Resume generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during resume generation"
        )


@router.get("/bullets/{bullet_id}/versions", status_code=status.HTTP_200_OK)
@limiter.limit("60/minute")
async def get_bullet_versions(
    request: Request,
    bullet_id: int,
    db: Session = Depends(get_db)
):
    """
    Get version history for a specific bullet.

    Returns the bullet's version_history JSON which contains the original text
    and any rewritten variants created during resume tailoring.

    **Path Parameters:**
    - `bullet_id` (int, required): ID of the bullet

    **Returns:**
    - JSON object with:
        - `bullet_id`: The bullet ID
        - `current_text`: Current canonical text of the bullet
        - `version_history`: List of historical versions (if available)
        - `created_at`: When the bullet was created
        - `updated_at`: When the bullet was last updated

    **Raises:**
    - `400 Bad Request`: Invalid bullet_id
    - `404 Not Found`: Bullet not found
    - `500 Internal Server Error`: Unexpected error
    """
    try:
        # Validate bullet_id is positive
        if bullet_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bullet_id: must be a positive integer"
            )

        # Query for the bullet
        bullet = db.query(Bullet).filter(Bullet.id == bullet_id).first()

        if not bullet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bullet {bullet_id} not found"
            )

        # Build response
        response = {
            "bullet_id": bullet.id,
            "current_text": bullet.text,
            "version_history": bullet.version_history or [],
            "created_at": bullet.created_at.isoformat() if bullet.created_at else None,
            "updated_at": bullet.updated_at.isoformat() if bullet.updated_at else None,
            "usage_count": bullet.usage_count,
            "last_used_at": bullet.last_used_at.isoformat() if bullet.last_used_at else None
        }

        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve bullet versions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving bullet versions"
        )
