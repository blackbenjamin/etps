"""
URL Security Utilities

Centralized SSRF (Server-Side Request Forgery) prevention.
"""

import ipaddress
import logging
import socket
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SSRFError(Exception):
    """Raised when a URL is blocked due to SSRF protection."""
    pass


# Blocked IP ranges (private networks and metadata endpoints)
BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),       # Private network
    ipaddress.ip_network("172.16.0.0/12"),    # Private network
    ipaddress.ip_network("192.168.0.0/16"),   # Private network
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local (AWS metadata)
    ipaddress.ip_network("0.0.0.0/8"),        # "This" network
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 private
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
    ipaddress.ip_network("::/128"),           # IPv6 unspecified
    ipaddress.ip_network("ff00::/8"),         # IPv6 multicast
]

# Blocked hostnames (cloud metadata endpoints)
BLOCKED_HOSTNAMES = [
    "metadata.google.internal",
    "169.254.169.254",
    "localhost",
    "localhost.localdomain",
    "127.0.0.1",
    "::1",
]


def is_ip_blocked(ip_str: str) -> bool:
    """
    Check if an IP address is in a blocked range.

    Args:
        ip_str: IP address as string

    Returns:
        True if IP is blocked, False otherwise
    """
    try:
        ip_addr = ipaddress.ip_address(ip_str)
        for blocked_range in BLOCKED_IP_RANGES:
            if ip_addr in blocked_range:
                return True
        return False
    except ValueError:
        # Invalid IP address
        return False


def is_hostname_blocked(hostname: str) -> bool:
    """
    Check if a hostname is blocked.

    Args:
        hostname: Hostname to check

    Returns:
        True if hostname is blocked, False otherwise
    """
    hostname_lower = hostname.lower()
    for blocked in BLOCKED_HOSTNAMES:
        if hostname_lower == blocked or hostname_lower.endswith(f".{blocked}"):
            return True
    return False


def validate_url_safety(url: str) -> Optional[str]:
    """
    Validate that a URL is safe to fetch (SSRF prevention).

    Checks for:
    - Private IP addresses
    - Loopback addresses
    - Cloud metadata endpoints
    - Blocked hostnames

    Args:
        url: URL to validate

    Returns:
        None if URL is safe

    Raises:
        SSRFError: If URL is unsafe
        ValueError: If URL is malformed
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a hostname")

    # Check if hostname is blocked
    if is_hostname_blocked(hostname):
        raise SSRFError(
            f"Access to {hostname} is blocked (metadata endpoint or localhost)"
        )

    # Resolve hostname to IP and check if IP is blocked
    try:
        # Get all IP addresses for this hostname
        addr_info = socket.getaddrinfo(hostname, None)
        for info in addr_info:
            ip_str = info[4][0]
            if is_ip_blocked(ip_str):
                raise SSRFError(
                    f"Access to {hostname} is blocked (resolves to private/internal IP: {ip_str})"
                )
    except socket.gaierror as e:
        # DNS resolution failed
        raise ValueError(f"Cannot resolve hostname {hostname}: {e}")
    except SSRFError:
        # Re-raise SSRF errors
        raise
    except Exception as e:
        # Other network errors
        logger.warning(f"Error resolving hostname {hostname}: {e}")
        raise ValueError(f"Error validating URL: {e}")

    # URL is safe
    return None
