"""
Job Router

FastAPI endpoints for job description parsing and skill-gap analysis.
Provides job profile creation and skill matching capabilities.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import JobProfile, User
from schemas.job_parser import JobParseRequest, JobParseResponse
from schemas.job_profile import SkillSelectionUpdate, SkillSelectionResponse, SelectedSkill
from schemas.skill_gap import SkillGapRequest, SkillGapResponse
from services.job_parser import parse_job_description
from services.skill_gap import analyze_skill_gap
from utils.text_processing import ExtractionFailedError


router = APIRouter()


@router.post("/parse", response_model=JobParseResponse, status_code=status.HTTP_201_CREATED)
async def parse_job_endpoint(
    request: JobParseRequest,
    db: Session = Depends(get_db)
) -> JobParseResponse:
    """
    Parse a job description and create a structured job profile.

    Accepts either raw job description text or a URL to fetch the description from.
    Extracts skills, requirements, responsibilities, and other structured information.

    **Request Body:**
    - `jd_text` (str, optional): Raw job description text
    - `jd_url` (str, optional): URL to fetch job description from
    - `user_id` (int, required): User ID to associate with the job profile

    **Note:** Must provide exactly one of `jd_text` or `jd_url`.

    **Returns:**
    - Structured job profile with extracted skills, requirements, and analysis

    **Raises:**
    - `400 Bad Request`: Invalid input (empty text, both fields provided, etc.)
    - `500 Internal Server Error`: Unexpected error during processing
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )

        # Parse job description using service
        job_profile: JobProfile = await parse_job_description(
            jd_text=request.jd_text,
            jd_url=request.jd_url,
            user_id=request.user_id,
            db=db
        )

        # Convert ORM model to response schema
        response = JobParseResponse(
            job_profile_id=job_profile.id,
            raw_jd_text=job_profile.raw_jd_text,
            jd_url=job_profile.jd_url,
            job_title=job_profile.job_title,
            company_name=job_profile.company_name,
            location=job_profile.location,
            seniority=job_profile.seniority,
            responsibilities=job_profile.responsibilities,
            requirements=job_profile.requirements,
            nice_to_haves=job_profile.nice_to_haves,
            extracted_skills=job_profile.extracted_skills or [],
            core_priorities=job_profile.core_priorities or [],
            must_have_capabilities=job_profile.must_have_capabilities or [],
            nice_to_have_capabilities=job_profile.nice_to_have_capabilities or [],
            tone_style=job_profile.tone_style,
            job_type_tags=job_profile.job_type_tags or [],
            created_at=job_profile.created_at.isoformat()
        )

        return response

    except HTTPException:
        raise
    except ExtractionFailedError as e:
        # Handle extraction quality failure - return user-friendly message
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "extraction_failed",
                "message": e.message,
                "score": e.quality.score,
                "issues": e.quality.issues,
                "suggestions": e.quality.suggestions
            }
        )
    except ValueError as e:
        # Handle validation errors (invalid input)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors - sanitize error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while parsing the job description"
        )


@router.post("/skill-gap", response_model=SkillGapResponse, status_code=status.HTTP_200_OK)
async def analyze_skill_gap_endpoint(
    request: SkillGapRequest,
    db: Session = Depends(get_db)
) -> SkillGapResponse:
    """
    Analyze skill gaps between a user's profile and a job's requirements.

    Computes matched skills, identifies gaps, detects weak signals, and generates
    positioning strategies for application materials.

    **Request Body:**
    - `job_profile_id` (int, required): ID of the parsed job profile
    - `user_id` (int, required): User ID for the analysis
    - `user_skill_profile` (UserSkillProfile, optional): Explicit skill profile.
      If not provided, will be derived from user's resume data.

    **Returns:**
    - Comprehensive skill gap analysis with match scores and positioning guidance

    **Raises:**
    - `404 Not Found`: Job profile not found or missing required data
    - `500 Internal Server Error`: Unexpected error during analysis
    """
    try:
        # Analyze skill gap using service
        analysis: SkillGapResponse = await analyze_skill_gap(
            job_profile_id=request.job_profile_id,
            user_id=request.user_id,
            db=db,
            user_skill_profile=request.user_skill_profile
        )

        return analysis

    except HTTPException:
        raise
    except ValueError as e:
        # Handle not found or validation errors
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors - sanitize error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while analyzing skill gap"
        )


@router.put("/job-profiles/{job_profile_id}/skills", response_model=SkillSelectionResponse)
async def update_skill_selection(
    job_profile_id: int,
    request: SkillSelectionUpdate,
    db: Session = Depends(get_db)
) -> SkillSelectionResponse:
    """
    Update user-curated skill selections for a job profile.

    Allows users to:
    - Reorder skills by priority
    - Select 3-4 "key skills" for cover letter emphasis
    - Remove irrelevant skills from the list

    **Path Parameters:**
    - `job_profile_id` (int): ID of the job profile to update

    **Request Body:**
    - `selected_skills` (List[SelectedSkill]): Ordered list of skills with metadata
    - `key_skills` (List[str]): 3-4 skills to emphasize (max 4)

    **Returns:**
    - Updated skill selection with timestamp

    **Raises:**
    - `404 Not Found`: Job profile not found
    - `422 Unprocessable Entity`: Invalid skill selection (validation errors)
    """
    try:
        # Fetch job profile
        job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {job_profile_id} not found"
            )

        # Convert selected_skills to dict format for JSON storage
        selected_skills_dict = [s.model_dump() for s in request.selected_skills]

        # Update job profile
        job_profile.selected_skills = selected_skills_dict
        job_profile.key_skills = request.key_skills

        db.commit()
        db.refresh(job_profile)

        # Build response
        return SkillSelectionResponse(
            job_profile_id=job_profile.id,
            selected_skills=request.selected_skills,
            key_skills=request.key_skills,
            updated_at=datetime.now(timezone.utc).isoformat()
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating skill selection"
        )


@router.get("/job-profiles/{job_profile_id}/skills", response_model=SkillSelectionResponse)
async def get_skill_selection(
    job_profile_id: int,
    db: Session = Depends(get_db)
) -> SkillSelectionResponse:
    """
    Get the current skill selection for a job profile.

    **Path Parameters:**
    - `job_profile_id` (int): ID of the job profile

    **Returns:**
    - Current skill selection or empty lists if not set

    **Raises:**
    - `404 Not Found`: Job profile not found
    """
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job profile {job_profile_id} not found"
        )

    # Convert stored dict format back to SelectedSkill objects
    selected_skills = []
    if job_profile.selected_skills:
        selected_skills = [SelectedSkill(**s) for s in job_profile.selected_skills]

    return SkillSelectionResponse(
        job_profile_id=job_profile.id,
        selected_skills=selected_skills,
        key_skills=job_profile.key_skills or [],
        updated_at=job_profile.updated_at.isoformat() if job_profile.updated_at else job_profile.created_at.isoformat()
    )
