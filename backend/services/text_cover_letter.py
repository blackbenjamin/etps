"""
Plain Text Cover Letter Generation Service

Generates ATS-friendly plain text cover letters from GeneratedCoverLetter JSON.
Uses business letter format with ASCII-only characters.
"""

import logging
from datetime import datetime
from typing import Optional

from schemas.cover_letter import GeneratedCoverLetter


logger = logging.getLogger(__name__)


def _format_date(date_str: Optional[str] = None) -> str:
    """
    Format date for cover letter (e.g., 'December 3, 2025').

    Uses platform-agnostic formatting.
    """
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str)
        except ValueError:
            dt = datetime.now()
    else:
        dt = datetime.now()
    # Platform-agnostic: strftime %d is zero-padded, so use day directly
    day = dt.day
    return f"{dt.strftime('%B')} {day}, {dt.year}"


def create_cover_letter_text(
    cover_letter: GeneratedCoverLetter,
    user_name: str,
    user_email: str,
    user_phone: Optional[str] = None,
    user_linkedin: Optional[str] = None,
    recipient_name: Optional[str] = None,
    company_name: Optional[str] = None,
    date_str: Optional[str] = None
) -> str:
    """
    Generate an ATS-friendly plain text cover letter from a GeneratedCoverLetter object.

    Format specifications:
    - Business letter format
    - Contact info header
    - Date and recipient
    - Body paragraphs
    - Signature

    Args:
        cover_letter: The GeneratedCoverLetter object with draft_cover_letter text
        user_name: Full name for the header
        user_email: Email address for the header
        user_phone: Phone number for the header (optional)
        user_linkedin: LinkedIn URL or handle for the header (optional)
        recipient_name: Name of recipient (default: "Hiring Team")
        company_name: Company name (uses cover_letter.company_name if not provided)
        date_str: ISO date string (default: current date)

    Returns:
        str: The generated plain text cover letter

    Example:
        >>> cl = GeneratedCoverLetter(...)
        >>> text = create_cover_letter_text(
        ...     cover_letter=cl,
        ...     user_name="Benjamin Black",
        ...     user_email="benjamin.black@sloan.mit.edu",
        ...     user_phone="617-504-5529",
        ...     user_linkedin="linkedin.com/in/benjaminblack"
        ... )
    """
    lines = []

    # === HEADER (Contact Info) ===
    lines.append(user_name)

    # Contact line with | separators
    contact_parts = [user_email]
    if user_phone:
        contact_parts.append(user_phone)
    if user_linkedin:
        contact_parts.append(user_linkedin)

    contact_line = " | ".join(contact_parts)
    lines.append(contact_line)
    lines.append("")  # Blank line after header

    # === DATE ===
    formatted_date = _format_date(date_str)
    lines.append(formatted_date)
    lines.append("")  # Blank line after date

    # === RECIPIENT ===
    recipient = recipient_name or "Hiring Team"
    lines.append(recipient)

    # Company name
    company = company_name or cover_letter.company_name
    if company:
        lines.append(company)

    lines.append("")  # Blank line after recipient

    # === GREETING ===
    greeting = f"Dear {recipient},"
    lines.append(greeting)
    lines.append("")  # Blank line after greeting

    # === BODY PARAGRAPHS ===
    body_text = cover_letter.draft_cover_letter

    # Validate non-empty body
    if not body_text or not body_text.strip():
        raise ValueError("Cover letter body text cannot be empty")

    # Split into paragraphs
    body_paragraphs = [p.strip() for p in body_text.split('\n\n') if p.strip()]

    # If no double-newlines, try single newlines
    if len(body_paragraphs) <= 1:
        body_paragraphs = [p.strip() for p in body_text.split('\n') if p.strip()]

    for para_text in body_paragraphs:
        lines.append(para_text)
        lines.append("")  # Blank line between paragraphs

    # === CLOSING ===
    lines.append("Sincerely,")
    lines.append("")
    lines.append(user_name)

    # Join all lines with newlines
    cover_letter_text = "\n".join(lines)

    logger.info(f"Generated plain text cover letter for {company or 'unknown company'}")
    return cover_letter_text
