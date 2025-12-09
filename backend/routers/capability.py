"""
Capability Cluster Router (Sprint 11)

FastAPI endpoints for capability cluster analysis - a higher-level
view of job fit focusing on compound capabilities and strategic requirements.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import JobProfile, User
from schemas.capability import (
    CapabilityClusterRequest,
    CapabilityClusterResponse,
    CapabilityClusterAnalysis,
    CapabilitySelectionUpdate,
    AddUserSkillRequest,
    AddUserSkillResponse,
)
from services.skill_gap import get_cluster_analysis, get_combined_analysis, merge_analysis_scores
from services.evidence_mapper import add_skill_to_user_profile


router = APIRouter()


@router.get(
    "/job-profiles/{job_profile_id}/clusters",
    response_model=CapabilityClusterResponse,
    status_code=status.HTTP_200_OK
)
async def get_capability_clusters(
    job_profile_id: int,
    user_id: int = 1,
    force_refresh: bool = False,
    db: Session = Depends(get_db)
) -> CapabilityClusterResponse:
    """
    Get capability cluster analysis for a job profile.

    Extracts or retrieves cached capability clusters from the job description,
    then maps the user's bullets to those clusters to calculate match percentages.

    **Path Parameters:**
    - `job_profile_id` (int): ID of the job profile to analyze

    **Query Parameters:**
    - `user_id` (int, optional): User ID for evidence mapping (default: 1)
    - `force_refresh` (bool, optional): Bypass cache and re-extract clusters

    **Returns:**
    - Capability cluster analysis with match scores, gaps, and positioning

    **Raises:**
    - `404 Not Found`: Job profile not found
    - `500 Internal Server Error`: Analysis error
    """
    try:
        # Validate job profile exists
        job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {job_profile_id} not found"
            )

        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get cluster analysis
        analysis = await get_cluster_analysis(
            job_profile_id=job_profile_id,
            user_id=user_id,
            db=db,
            force_refresh=force_refresh,
            use_mock=True  # Use mock for now (no LLM API calls)
        )

        # Check if result was cached
        was_cached = (
            job_profile.capability_clusters is not None
            and not force_refresh
        )

        # Calculate cache expiry (24 hours from analysis timestamp)
        cache_expires_at = None
        if job_profile.capability_analysis_timestamp:
            from datetime import timedelta
            expiry = job_profile.capability_analysis_timestamp + timedelta(hours=24)
            cache_expires_at = expiry.isoformat()

        return CapabilityClusterResponse(
            analysis=analysis,
            cached=was_cached,
            cache_expires_at=cache_expires_at
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during cluster analysis: {str(e)}"
        )


@router.post(
    "/job-profiles/{job_profile_id}/clusters/analyze",
    response_model=CapabilityClusterResponse,
    status_code=status.HTTP_200_OK
)
async def analyze_capability_clusters(
    job_profile_id: int,
    request: CapabilityClusterRequest,
    db: Session = Depends(get_db)
) -> CapabilityClusterResponse:
    """
    Trigger capability cluster analysis for a job profile.

    Forces extraction of new clusters and evidence mapping even if cached.

    **Path Parameters:**
    - `job_profile_id` (int): ID of the job profile to analyze

    **Request Body:**
    - `job_profile_id` (int): Must match path parameter
    - `user_id` (int): User ID for evidence mapping
    - `force_refresh` (bool): Force re-extraction (default: False)

    **Returns:**
    - Fresh capability cluster analysis

    **Raises:**
    - `400 Bad Request`: Path/body job_profile_id mismatch
    - `404 Not Found`: Job profile or user not found
    """
    # Validate path matches body
    if request.job_profile_id != job_profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="job_profile_id in path must match request body"
        )

    try:
        # Validate job profile exists
        job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {job_profile_id} not found"
            )

        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )

        # Get cluster analysis (force refresh if requested)
        analysis = await get_cluster_analysis(
            job_profile_id=job_profile_id,
            user_id=request.user_id,
            db=db,
            force_refresh=request.force_refresh,
            use_mock=True
        )

        # Refresh job_profile to get updated timestamp
        db.refresh(job_profile)

        # Calculate cache expiry
        cache_expires_at = None
        if job_profile.capability_analysis_timestamp:
            from datetime import timedelta
            expiry = job_profile.capability_analysis_timestamp + timedelta(hours=24)
            cache_expires_at = expiry.isoformat()

        return CapabilityClusterResponse(
            analysis=analysis,
            cached=False,  # We just analyzed, so not cached
            cache_expires_at=cache_expires_at
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during cluster analysis: {str(e)}"
        )


@router.put(
    "/job-profiles/{job_profile_id}/clusters/selections",
    response_model=dict,
    status_code=status.HTTP_200_OK
)
async def update_cluster_selections(
    job_profile_id: int,
    request: CapabilitySelectionUpdate,
    db: Session = Depends(get_db)
) -> dict:
    """
    Update user selections for capability clusters.

    Allows users to select key skills from clusters for cover letter emphasis
    and store cluster expansion state for UI.

    **Path Parameters:**
    - `job_profile_id` (int): ID of the job profile

    **Request Body:**
    - `job_profile_id` (int): Must match path parameter
    - `key_skills` (List[KeySkillSelection]): Selected skills for emphasis (max 4)
    - `cluster_expansions` (dict, optional): UI state for cluster expansion

    **Returns:**
    - Updated selection with timestamp

    **Raises:**
    - `400 Bad Request`: Validation errors
    - `404 Not Found`: Job profile not found
    """
    # Validate path matches body
    if request.job_profile_id != job_profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="job_profile_id in path must match request body"
        )

    try:
        # Fetch job profile
        job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {job_profile_id} not found"
            )

        # Update key_skills (re-use existing field)
        job_profile.key_skills = [
            ks.skill_name for ks in request.key_skills if ks.selected
        ]

        # Store cluster-based key skills in capability_clusters metadata
        if job_profile.capability_clusters:
            # Add selections metadata to clusters
            clusters_data = job_profile.capability_clusters
            for cluster_data in clusters_data:
                cluster_name = cluster_data.get("name", "")
                # Update expansion state if provided
                if request.cluster_expansions and cluster_name in request.cluster_expansions:
                    cluster_data["is_expanded"] = request.cluster_expansions[cluster_name]

            job_profile.capability_clusters = clusters_data

        db.commit()
        db.refresh(job_profile)

        return {
            "job_profile_id": job_profile_id,
            "key_skills": job_profile.key_skills,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred updating selections: {str(e)}"
        )


@router.get(
    "/job-profiles/{job_profile_id}/combined-analysis",
    response_model=dict,
    status_code=status.HTTP_200_OK
)
async def get_combined_job_analysis(
    job_profile_id: int,
    user_id: int = 1,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get combined flat skill and cluster analysis for comprehensive job fit.

    Returns both the traditional skill gap analysis and the capability cluster
    analysis, along with a merged score.

    **Path Parameters:**
    - `job_profile_id` (int): ID of the job profile

    **Query Parameters:**
    - `user_id` (int, optional): User ID (default: 1)

    **Returns:**
    - Combined analysis with flat skills, clusters, and merged score

    **Raises:**
    - `404 Not Found`: Job profile not found
    """
    try:
        # Validate job profile exists
        job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {job_profile_id} not found"
            )

        # Get combined analysis
        flat_analysis, cluster_analysis = await get_combined_analysis(
            job_profile_id=job_profile_id,
            user_id=user_id,
            db=db,
            use_cache=True,
            use_mock_clusters=True
        )

        # Calculate merged score
        merged_score = merge_analysis_scores(flat_analysis, cluster_analysis)

        return {
            "job_profile_id": job_profile_id,
            "user_id": user_id,
            "flat_analysis": flat_analysis.model_dump(),
            "cluster_analysis": cluster_analysis.model_dump(),
            "merged_score": merged_score,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during combined analysis: {str(e)}"
        )


@router.post(
    "/job-profiles/{job_profile_id}/user-skills",
    response_model=AddUserSkillResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_user_skill(
    job_profile_id: int,
    request: AddUserSkillRequest,
    db: Session = Depends(get_db)
) -> AddUserSkillResponse:
    """
    Add a skill to user's profile by associating it with experiences/engagements/bullets.

    Skills are saved immediately to the database. Analysis is NOT automatically re-run.

    **Path Parameters:**
    - `job_profile_id` (int): ID of the job profile (for context validation)

    **Request Body:**
    - `skill_name` (str): Name of the skill to add (1-100 chars)
    - `user_id` (int): User ID (default: 1)
    - `evidence_mappings` (List[EvidenceMapping]): Where to add the skill (min 1)
        - `experience_id` (int): Experience to update
        - `engagement_id` (int, optional): Engagement within experience
        - `bullet_ids` (List[int], optional): Specific bullets to tag

    **Logic:**
    - If `bullet_ids` provided: Add skill to `Bullet.tags`
    - If no `bullet_ids` but `engagement_id`: Add to all bullets in engagement
    - If just `experience_id`: Add to `Experience.tools_and_technologies`

    **Returns:**
    - Skill name, user ID, number of entities updated, timestamp

    **Raises:**
    - `404 Not Found`: Job profile, experience, engagement, or bullet not found
    - `400 Bad Request`: Invalid request (empty skill name, empty mappings, etc.)
    """
    try:
        # Manual validation to return 400 instead of 422
        if not request.skill_name or len(request.skill_name) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="skill_name cannot be empty"
            )

        if len(request.skill_name) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="skill_name cannot exceed 100 characters"
            )

        if not request.evidence_mappings or len(request.evidence_mappings) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="evidence_mappings cannot be empty"
            )

        # Validate job profile exists
        job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        if not job_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job profile {job_profile_id} not found"
            )

        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )

        # Add skill to user profile
        entities_updated = add_skill_to_user_profile(
            skill_name=request.skill_name,
            user_id=request.user_id,
            evidence_mappings=request.evidence_mappings,
            db=db
        )

        # Return response
        return AddUserSkillResponse(
            skill_name=request.skill_name,
            user_id=request.user_id,
            entities_updated=entities_updated,
            added_at=datetime.now(timezone.utc).isoformat()
        )

    except HTTPException:
        raise
    except ValueError as e:
        # ValueError from service means entity not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred adding skill: {str(e)}"
        )
