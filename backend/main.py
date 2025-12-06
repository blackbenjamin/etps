"""
Enterprise-Grade Talent Positioning System (ETPS) - Backend
An AI-Orchestrated Resume, Cover Letter, and Networking Intelligence Platform

This is the main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import job_router, resume_router, cover_letter_router, critic_router

app = FastAPI(
    title="ETPS API",
    description="Enterprise-Grade Talent Positioning System API",
    version="0.1.0",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


# Register routers
app.include_router(job_router, prefix="/api/v1/job", tags=["job"])
app.include_router(resume_router, prefix="/api/v1/resume", tags=["resume"])
app.include_router(cover_letter_router, prefix="/api/v1/cover-letter", tags=["cover_letter"])
app.include_router(critic_router, prefix="/api/v1/critic", tags=["critic"])

# TODO: Include additional routers when implemented
# app.include_router(company.router, prefix="/api/v1/company", tags=["company"])
# app.include_router(networking.router, prefix="/api/v1/networking", tags=["networking"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
