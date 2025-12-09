"""
Company Router

FastAPI endpoints for company profile enrichment and management.
Provides company intelligence for tailoring resumes and cover letters.
"""

import logging
from datetime import timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from db.database import get_db
from db.models import CompanyProfile, User
from schemas.company import (
    CompanyEnrichRequest,
    CompanyProfileResponse,
    CompanyProfileUpdate,
    CompanySearchResponse,
)
from services.company_enrichment import (
    enrich_company_profile,
    get_company_profile,
    search_company_profiles,
)


router = APIRouter()


def _profile_to_response(profile: CompanyProfile) -> CompanyProfileResponse:
    """Convert ORM model to response schema."""
    return CompanyProfileResponse(
        id=profile.id,
        name=profile.name,
        website=profile.website,
        industry=profile.industry,
        size_band=profile.size_band,
        headquarters=profile.headquarters,
        business_lines=profile.business_lines,
        known_initiatives=profile.known_initiatives,
        culture_signals=profile.culture_signals or [],
        data_ai_maturity=profile.data_ai_maturity,
        created_at=profile.created_at.isoformat() if profile.created_at else None,
        updated_at=profile.updated_at.isoformat() if profile.updated_at else None,
    )


@router.post("/enrich", response_model=CompanyProfileResponse, status_code=status.HTTP_201_CREATED)
async def enrich_company_endpoint(
    request: CompanyEnrichRequest,
    db: Session = Depends(get_db)
) -> CompanyProfileResponse:
    """
    Enrich a company profile with industry, culture, and AI maturity data.

    Creates a new company profile or updates an existing one with enrichment data.
    Can optionally fetch data from the company's website.

    **Request Body:**
    - `company_name` (str, required): Company name to enrich
    - `jd_text` (str, optional): Job description for additional context
    - `website_url` (str, optional): Company website to fetch and analyze
    - `user_id` (int, required): User ID for association

    **Returns:**
    - Enriched company profile with industry, culture signals, and AI maturity

    **Raises:**
    - `404 Not Found`: User not found
    - `400 Bad Request`: Invalid input
    - `500 Internal Server Error`: Enrichment failed
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )

        # Enrich company profile
        profile = await enrich_company_profile(
            company_name=request.company_name,
            jd_text=request.jd_text,
            website_url=request.website_url,
            user_id=request.user_id,
            db=db,
        )

        return _profile_to_response(profile)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in enrich_company_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while enriching company profile"
        )


@router.get("/{company_id}", response_model=CompanyProfileResponse)
async def get_company_endpoint(
    company_id: int,
    db: Session = Depends(get_db)
) -> CompanyProfileResponse:
    """
    Get a company profile by ID.

    **Path Parameters:**
    - `company_id` (int): Company profile ID

    **Returns:**
    - Company profile data

    **Raises:**
    - `404 Not Found`: Company profile not found
    """
    profile = await get_company_profile(company_id, db)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company profile {company_id} not found"
        )

    return _profile_to_response(profile)


@router.get("/search/", response_model=CompanySearchResponse)
async def search_companies_endpoint(
    name: str = Query(..., min_length=1, description="Company name to search"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    db: Session = Depends(get_db)
) -> CompanySearchResponse:
    """
    Search company profiles by name.

    **Query Parameters:**
    - `name` (str, required): Search query
    - `limit` (int, optional): Maximum results (default: 10, max: 50)

    **Returns:**
    - List of matching company profiles
    """
    profiles = await search_company_profiles(name, db, limit)

    return CompanySearchResponse(
        companies=[_profile_to_response(p) for p in profiles],
        total_count=len(profiles),
    )


@router.put("/{company_id}", response_model=CompanyProfileResponse)
async def update_company_endpoint(
    company_id: int,
    request: CompanyProfileUpdate,
    db: Session = Depends(get_db)
) -> CompanyProfileResponse:
    """
    Update a company profile.

    Allows manual updates to company profile fields. Only provided fields
    are updated; omitted fields are not changed.

    **Path Parameters:**
    - `company_id` (int): Company profile ID

    **Request Body:**
    - Any CompanyProfileUpdate fields to update

    **Returns:**
    - Updated company profile

    **Raises:**
    - `404 Not Found`: Company profile not found
    - `422 Unprocessable Entity`: Invalid field values
    """
    profile = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company profile {company_id} not found"
        )

    # Update only provided fields
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(profile, field):
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return _profile_to_response(profile)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_endpoint(
    company_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a company profile.

    **Path Parameters:**
    - `company_id` (int): Company profile ID

    **Raises:**
    - `404 Not Found`: Company profile not found
    """
    profile = db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company profile {company_id} not found"
        )

    db.delete(profile)
    db.commit()
