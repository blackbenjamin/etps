"""
ETPS API Routers

TODO: Implement the following routers:
- networking: Contact and networking suggestion endpoints
"""

from routers.job import router as job_router
from routers.resume import router as resume_router
from routers.cover_letter import router as cover_letter_router
from routers.critic import router as critic_router
from routers.outputs import router as outputs_router
from routers.capability import router as capability_router
from routers.users import router as users_router
from routers.company import router as company_router

__all__ = [
    "job_router",
    "resume_router",
    "cover_letter_router",
    "critic_router",
    "outputs_router",
    "capability_router",
    "users_router",
    "company_router",
]
