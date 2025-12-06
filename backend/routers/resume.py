"""
Resume Router

FastAPI endpoints for resume tailoring and generation.
Provides intelligent resume optimization based on job requirements.
"""

import logging
import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import JobProfile, User
from schemas.resume_tailor import TailorResumeRequest, TailoredResume, ResumeDocxRequest
from services.resume_tailor import tailor_resume
from services.docx_resume import create_resume_docx


logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/generate", response_model=TailoredResume, status_code=status.HTTP_200_OK)
async def generate_tailored_resume(
    request: TailorResumeRequest,
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
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )

        # Validate job profile exists
        job_profile = db.query(JobProfile).filter(JobProfile.id == request.job_profile_id).first()
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {request.job_profile_id} not found"
            )

        # Generate tailored resume using service
        tailored_resume = await tailor_resume(
            job_profile_id=request.job_profile_id,
            user_id=request.user_id,
            db=db,
            max_bullets_per_role=request.max_bullets_per_role,
            max_skills=request.max_skills,
            custom_instructions=request.custom_instructions,
        )

        return tailored_resume

    except ValueError as e:
        # Handle validation errors and not found errors
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors - sanitize error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the tailored resume"
        )


@router.post("/docx", status_code=status.HTTP_200_OK)
async def generate_resume_docx(request: ResumeDocxRequest) -> Response:
    """
    Generate a DOCX resume from a TailoredResume JSON.

    Takes a previously generated TailoredResume object and renders it as a
    professionally formatted Word document (.docx) matching the Benjamin Black
    resume template style.

    **Request Body:**
    - `tailored_resume` (TailoredResume, required): The tailored resume JSON
    - `user_name` (str, required): Full name for the resume header
    - `user_email` (str, required): Email address for the header
    - `user_phone` (str, optional): Phone number for the header
    - `user_linkedin` (str, optional): LinkedIn URL/handle for the header
    - `education` (list[EducationEntry], optional): Education entries to include

    **Document Format:**
    - Page: 8.5" x 11" with 0.9" top, 0.56" bottom, 0.5" left/right margins
    - Font: Georgia throughout
    - Header: Name (16pt bold centered), contact info (10.5pt centered)
    - Sections: Professional Experience, Technical Skills, Education
    - Bullets: Hanging indent style with bullet points

    **Returns:**
    - DOCX file as binary response with appropriate headers for download

    **Raises:**
    - `400 Bad Request`: Invalid request structure
    - `422 Unprocessable Entity`: Invalid content (e.g., empty resume)
    - `500 Internal Server Error`: DOCX generation failed
    """
    try:
        # Validate we have content to render
        if not request.tailored_resume.selected_roles:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TailoredResume must have at least one selected role"
            )

        # Convert education entries to dict format for service
        education_dicts = [
            {
                "institution": edu.institution,
                "location": edu.location,
                "degree": edu.degree,
                "details": edu.details
            }
            for edu in request.education
        ] if request.education else None

        # Generate DOCX
        docx_bytes = create_resume_docx(
            tailored_resume=request.tailored_resume,
            user_name=request.user_name,
            user_email=request.user_email,
            user_phone=request.user_phone,
            user_linkedin=request.user_linkedin,
            education=education_dicts
        )

        # Create filename from user name with robust sanitization
        safe_name = re.sub(r'[^\w\s-]', '', request.user_name, flags=re.UNICODE)
        safe_name = re.sub(r'[-\s]+', '_', safe_name).strip('_')
        safe_name = safe_name or "Resume"  # Fallback for empty/invalid names
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
        logger.warning(f"DOCX generation validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid resume content structure"
        )
    except Exception as e:
        logger.error(f"DOCX generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during DOCX generation"
        )
