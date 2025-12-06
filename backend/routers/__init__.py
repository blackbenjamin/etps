"""
ETPS API Routers

TODO: Implement the following routers:
- company: Company intelligence endpoints
- networking: Contact and networking suggestion endpoints
"""

from routers.job import router as job_router
from routers.resume import router as resume_router
from routers.cover_letter import router as cover_letter_router
from routers.critic import router as critic_router

__all__ = ["job_router", "resume_router", "cover_letter_router", "critic_router"]
