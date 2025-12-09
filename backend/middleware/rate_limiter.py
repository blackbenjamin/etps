"""
Rate Limiting Middleware

Uses slowapi to implement rate limiting on API endpoints.
Configuration loaded from config.yaml.

SECURITY NOTE: The get_real_client_ip function does NOT trust X-Forwarded-For
headers by default to prevent rate limit bypass attacks. In production behind
a trusted proxy (Railway, CloudFlare, AWS ALB), configure TRUSTED_PROXIES.
"""

import logging
import os
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Trusted proxy IPs (configure via environment variable in production)
# Format: comma-separated IPs, e.g., "10.0.0.1,10.0.0.2"
TRUSTED_PROXIES = set(
    os.environ.get("TRUSTED_PROXY_IPS", "").split(",")
) if os.environ.get("TRUSTED_PROXY_IPS") else set()


def get_real_client_ip(request: Request) -> str:
    """
    Get the real client IP address securely.

    SECURITY: Only trusts X-Forwarded-For header when request comes from
    a known trusted proxy. Otherwise, uses the direct client IP to prevent
    rate limit bypass via header spoofing.

    In production behind Railway/CloudFlare/AWS:
    - Set TRUSTED_PROXY_IPS environment variable
    - The proxy will set X-Forwarded-For correctly

    Args:
        request: FastAPI request object

    Returns:
        Client IP address string
    """
    # Direct client IP (from socket connection)
    client_ip = request.client.host if request.client else "unknown"

    # Only trust X-Forwarded-For if request is from a trusted proxy
    if client_ip in TRUSTED_PROXIES:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client) from the chain
            # X-Forwarded-For format: "client, proxy1, proxy2"
            real_ip = forwarded_for.split(",")[0].strip()
            if real_ip:
                return real_ip

    return client_ip


# Initialize limiter with secure key function
limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=[]  # No global limits, set per-route
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Returns 429 status with Retry-After header.
    """
    # Extract retry-after value from exception
    retry_after = getattr(exc, 'retry_after', 60)

    logger.warning(
        f"Rate limit exceeded for {request.client.host} on {request.url.path}"
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": "Too many requests. Please try again later.",
            "retry_after": int(retry_after)
        },
        headers={
            "Retry-After": str(int(retry_after))
        }
    )
