"""
User Experience Schemas (Sprint 11D)

Schemas for retrieving user's work history with nested engagements and bullets.
Used by the "Report Unregistered Skills" feature to show evidence mapping UI.
"""

from typing import List, Optional
from datetime import date
from pydantic import BaseModel


class BulletSummary(BaseModel):
    """Summary of a bullet point."""
    id: int
    text: str
    tags: Optional[List[str]] = None


class EngagementSummary(BaseModel):
    """Summary of a consulting engagement within an experience."""
    id: int
    client: Optional[str] = None
    project_name: Optional[str] = None
    date_range_label: Optional[str] = None
    bullets: List[BulletSummary] = []


class ExperienceWithDetails(BaseModel):
    """
    Experience with nested engagements and bullets.

    For consulting roles (employer_type = 'independent_consulting'),
    bullets are nested under engagements.

    For non-consulting roles, bullets are attached directly to experience.
    """
    id: int
    job_title: str
    employer_name: str
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    employer_type: Optional[str] = None
    tools_and_technologies: Optional[List[str]] = None
    engagements: List[EngagementSummary] = []
    bullets: List[BulletSummary] = []  # Direct bullets (non-consulting)
