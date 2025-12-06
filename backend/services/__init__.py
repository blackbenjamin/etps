"""
ETPS Business Logic Services

TODO: Implement the following services:
- resume_service: Resume tailoring, bullet selection, docx generation
- cover_letter_service: Cover letter generation and template matching
- job_profile_service: JD parsing, skill extraction, gap analysis
- company_service: Company intelligence gathering and profiling
- networking_service: Contact identification and outreach generation
- critic_service: Quality evaluation and ATS scoring
- embedding_service: Vector operations with Qdrant
"""

from .skill_gap import analyze_skill_gap, build_user_skill_profile
from .bullet_rewriter import (
    rewrite_bullet,
    rewrite_bullets_for_job,
    validate_rewrite,
    store_version_history,
)

__all__ = [
    'analyze_skill_gap',
    'build_user_skill_profile',
    'rewrite_bullet',
    'rewrite_bullets_for_job',
    'validate_rewrite',
    'store_version_history',
]
