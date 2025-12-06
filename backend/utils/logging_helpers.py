"""
Logging helpers with PII sanitization.

Use these wrappers when logging user-generated content that may contain
personal information (names, emails, etc.).
"""
import logging
from utils.pii_sanitizer import sanitize_personal_identifiers


def safe_log_info(logger: logging.Logger, message: str, *args, **kwargs):
    """Log info message with PII sanitization."""
    try:
        sanitized_msg = sanitize_personal_identifiers(message)
    except Exception:
        # Fallback: redact entire message if sanitization fails
        sanitized_msg = "[message redacted - sanitization failed]"
    logger.info(sanitized_msg, *args, **kwargs)


def safe_log_debug(logger: logging.Logger, message: str, *args, **kwargs):
    """Log debug message with PII sanitization."""
    try:
        sanitized_msg = sanitize_personal_identifiers(message)
    except Exception:
        # Fallback: redact entire message if sanitization fails
        sanitized_msg = "[message redacted - sanitization failed]"
    logger.debug(sanitized_msg, *args, **kwargs)


def safe_log_warning(logger: logging.Logger, message: str, *args, **kwargs):
    """Log warning message with PII sanitization."""
    try:
        sanitized_msg = sanitize_personal_identifiers(message)
    except Exception:
        # Fallback: redact entire message if sanitization fails
        sanitized_msg = "[message redacted - sanitization failed]"
    logger.warning(sanitized_msg, *args, **kwargs)


def safe_log_error(logger: logging.Logger, message: str, *args, **kwargs):
    """Log error message with PII sanitization."""
    try:
        sanitized_msg = sanitize_personal_identifiers(message)
    except Exception:
        # Fallback: redact entire message if sanitization fails
        sanitized_msg = "[message redacted - sanitization failed]"
    logger.error(sanitized_msg, *args, **kwargs)
