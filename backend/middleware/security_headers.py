"""
Security Headers Middleware

Adds security headers to all HTTP responses.
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers added:
    - Content-Security-Policy: Restrict resource loading
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - Referrer-Policy: Control referrer information
    - Strict-Transport-Security: Force HTTPS (production only)
    """

    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Content Security Policy - restrict resource loading
        # Allow self and specific trusted origins for API
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )

        # Prevent page from being displayed in iframe (clickjacking protection)
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS - only in production (requires HTTPS)
        if self.environment == "production":
            # Force HTTPS for 1 year, include subdomains
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


def add_security_headers(app, environment: str = "development"):
    """
    Add security headers middleware to FastAPI app.

    Args:
        app: FastAPI application instance
        environment: Environment name (development|staging|production)
    """
    app.add_middleware(SecurityHeadersMiddleware, environment=environment)
    logger.info(f"Security headers middleware enabled (environment: {environment})")
