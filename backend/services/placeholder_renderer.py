"""
Placeholder Renderer for Networking Outputs

Replaces {{CONTACT_*}} placeholders with actual values from the database.
Used as the final rendering step before returning networking/outreach content to users.

This service ensures PII is only re-attached at the edge when generating
user-visible outputs, following the principle of keeping PII in a single
authoritative store (the database).
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from db.models import Contact
from utils.pii_sanitizer import restore_personal_identifiers, extract_placeholder_ids

logger = logging.getLogger(__name__)


async def render_networking_output(
    template_text: str,
    db: Session,
    user_id: int
) -> str:
    """
    Replace placeholders with actual contact information from database.

    Security: Validates that all contacts belong to the specified user.

    Args:
        template_text: Text with {{CONTACT_NAME_<id>}} placeholders
        db: Database session
        user_id: User ID for security validation

    Returns:
        Rendered text with real names/emails

    Raises:
        PermissionError: If any contact doesn't belong to the user
    """
    # Extract contact IDs from placeholders
    contact_ids = extract_placeholder_ids(template_text)

    if not contact_ids:
        return template_text

    # Fetch contacts from database
    contacts = db.query(Contact).filter(
        Contact.id.in_(contact_ids),
        Contact.user_id == user_id,
        Contact.deleted_at.is_(None)  # Exclude soft-deleted contacts
    ).all()

    # Validate all requested contacts belong to user
    found_ids = {c.id for c in contacts}
    missing_ids = set(contact_ids) - found_ids
    if missing_ids:
        # Log detailed info for debugging (server-side only)
        logger.warning(
            f"Contact access denied: user={user_id} attempted to access "
            f"{len(missing_ids)} unowned/missing contacts"
        )
        # Return generic error message to caller
        raise PermissionError("Access denied: Cannot render contacts")

    # Build contact map
    contact_map = {}
    for contact in contacts:
        contact_map[f"{{{{CONTACT_NAME_{contact.id}}}}}"] = contact.full_name
        contact_map[f"{{{{CONTACT_EMAIL_{contact.id}}}}}"] = contact.email or ""
        contact_map[f"{{{{CONTACT_LINKEDIN_{contact.id}}}}}"] = contact.linkedin_url or ""
        contact_map[f"{{{{CONTACT_TITLE_{contact.id}}}}}"] = contact.title or ""

    # Render placeholders
    return restore_personal_identifiers(template_text, contact_map)


def build_contact_context(contact: Contact) -> Dict[str, str]:
    """
    Build non-PII context for a contact for use in prompts.

    Returns structural metadata without personal identifiers.
    Use this when constructing LLM prompts that should not contain PII.

    Args:
        contact: Contact database object

    Returns:
        Dictionary with non-PII attributes for prompting
    """
    return {
        "contact_id": str(contact.id),
        "role_archetype": _infer_role_archetype(contact.title),
        "seniority_band": _infer_seniority_band(contact.title),
        "relationship_bucket": _get_relationship_bucket(contact.relationship_strength),
        "has_email": bool(contact.email),
        "has_linkedin": bool(contact.linkedin_url),
        "is_hiring_manager_candidate": contact.is_hiring_manager_candidate,
    }


def _infer_role_archetype(title: Optional[str]) -> str:
    """Infer role archetype from job title."""
    if not title:
        return "unknown"

    title_lower = title.lower()

    # Check in order of seniority (most senior first)
    # Use word boundaries to avoid false matches
    if "chief" in title_lower or any(title_lower.startswith(x) for x in ["cto", "cio", "cdo", "ceo", "cfo"]):
        return "c_level"
    if "vp" in title_lower or "vice president" in title_lower:
        return "vp"
    if "director" in title_lower or "head of" in title_lower:
        return "director"
    if "manager" in title_lower or "lead" in title_lower:
        return "manager"
    if "senior" in title_lower or "sr." in title_lower:
        return "senior_ic"

    return "ic"


def _infer_seniority_band(title: Optional[str]) -> str:
    """Infer seniority band from job title."""
    archetype = _infer_role_archetype(title)

    seniority_map = {
        "c_level": "executive",
        "vp": "executive",
        "director": "senior_leadership",
        "manager": "management",
        "senior_ic": "senior",
        "ic": "mid",
        "unknown": "unknown"
    }

    return seniority_map.get(archetype, "unknown")


def _get_relationship_bucket(strength: Optional[float]) -> str:
    """Convert relationship strength to bucket."""
    if strength is None:
        return "unknown"

    if strength >= 0.7:
        return "warm"
    if strength >= 0.4:
        return "lukewarm"

    return "cold"
