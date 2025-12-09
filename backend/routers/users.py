"""
Users Router (Sprint 11D)

Endpoints for retrieving user profile data, including work history
with nested engagements and bullets.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import User, Experience, Engagement, Bullet
from schemas.users import ExperienceWithDetails, EngagementSummary, BulletSummary


router = APIRouter()


@router.get(
    "/{user_id}/experiences",
    response_model=List[ExperienceWithDetails]
)
async def get_user_experiences(
    user_id: int,
    db: Session = Depends(get_db)
) -> List[ExperienceWithDetails]:
    """
    Get all experiences for a user with engagements and bullets.

    Returns work history with nested structure:
    - For consulting roles: experiences contain engagements, which contain bullets
    - For non-consulting roles: experiences contain bullets directly

    **Path Parameters:**
    - `user_id` (int): User ID

    **Returns:**
    - List of experiences with nested engagements and bullets

    **Raises:**
    - `404 Not Found`: User not found
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get all experiences for user, ordered by order field
        experiences = db.query(Experience).filter(
            Experience.user_id == user_id
        ).order_by(Experience.order).all()

        result = []
        for exp in experiences:
            # Get engagements for this experience
            engagements = db.query(Engagement).filter(
                Engagement.experience_id == exp.id
            ).order_by(Engagement.order).all()

            engagement_summaries = []
            for eng in engagements:
                # Get bullets for this engagement
                eng_bullets = db.query(Bullet).filter(
                    Bullet.engagement_id == eng.id,
                    Bullet.retired == False
                ).order_by(Bullet.order).all()

                bullet_summaries = [
                    BulletSummary(
                        id=b.id,
                        text=b.text,
                        tags=b.tags
                    ) for b in eng_bullets
                ]

                engagement_summaries.append(
                    EngagementSummary(
                        id=eng.id,
                        client=eng.client,
                        project_name=eng.project_name,
                        date_range_label=eng.date_range_label,
                        bullets=bullet_summaries
                    )
                )

            # Get direct bullets (non-engagement bullets) for this experience
            direct_bullets = db.query(Bullet).filter(
                Bullet.experience_id == exp.id,
                Bullet.engagement_id == None,
                Bullet.retired == False
            ).order_by(Bullet.order).all()

            direct_bullet_summaries = [
                BulletSummary(
                    id=b.id,
                    text=b.text,
                    tags=b.tags
                ) for b in direct_bullets
            ]

            # Build experience response
            result.append(
                ExperienceWithDetails(
                    id=exp.id,
                    job_title=exp.job_title,
                    employer_name=exp.employer_name,
                    location=exp.location,
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    employer_type=exp.employer_type,
                    tools_and_technologies=exp.tools_and_technologies,
                    engagements=engagement_summaries,
                    bullets=direct_bullet_summaries
                )
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred retrieving experiences: {str(e)}"
        )
