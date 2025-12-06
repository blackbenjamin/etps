"""
PII (Personally Identifiable Information) Sanitizer Utility

Provides functions to:
- Replace personal identifiers (names, emails, LinkedIn URLs) with placeholders
- Restore original values from contact maps
- Extract placeholder IDs for reference tracking

This utility is used to protect sensitive user information while maintaining
the ability to restore original content when needed.
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple


# Company allowlist to avoid sanitizing company names
COMPANY_NAMES = {
    "Microsoft", "Apple", "Google", "Amazon", "Meta", "Tesla",
    "Goldman Sachs", "JPMorgan Chase", "Bank of America", "Morgan Stanley",
    "Amazon Web Services", "AWS", "Azure", "GCP", "Google Cloud",
    "IBM", "Oracle", "Salesforce", "Adobe", "Netflix", "Spotify",
    "Airbnb", "Uber", "LinkedIn", "Twitter", "Slack", "Discord",
    "Intel", "NVIDIA", "AMD", "Qualcomm", "Broadcom",
    "Verizon", "AT&T", "Comcast", "Charter Communications",
    "Pfizer", "Moderna", "Johnson & Johnson", "AstraZeneca",
    "McKinsey", "Bain & Company", "Boston Consulting Group", "Deloitte",
    "PwC", "EY", "KPMG", "Accenture",
    "Kubernetes", "Docker", "Python", "Java", "C++", "Rust", "Go",
    "React", "Angular", "Vue", "Node.js", "FastAPI", "Django",
    "PostgreSQL", "MongoDB", "Redis", "Cassandra", "Elasticsearch",
    "Machine Learning", "Natural Language Processing", "Deep Learning",
    "DevOps", "DevSecOps", "Site Reliability Engineering", "SRE",
    "Cloud Engineering"
}

# Technical terms that shouldn't be sanitized
TECHNICAL_TERMS = {
    "Python", "Java", "JavaScript", "TypeScript", "C++", "Rust", "Go", "Ruby",
    "AWS", "GCP", "Azure", "Kubernetes", "Docker", "React", "Vue", "Angular",
    "PostgreSQL", "MongoDB", "Redis", "SQL", "NoSQL", "REST", "GraphQL",
    "Machine Learning", "Deep Learning", "NLP", "AI", "Artificial Intelligence",
    "Leadership", "Management", "Strategy", "Development", "Engineering",
    "Frontend", "Backend", "Full Stack", "DevOps", "Cloud",
    "Cloud Engineering", "Site Reliability Engineering"
}

# Security constants for input validation
MAX_TEXT_LENGTH = 1_000_000  # 1MB limit to prevent ReDoS
MAX_NAME_PART_LENGTH = 50  # Max length for individual name parts
MAX_CONTACT_MAP_SIZE = 10_000  # Max number of contact map entries

# Pre-compiled regex patterns to prevent ReDoS and improve performance
# Using explicit length limits {0,50} to prevent catastrophic backtracking
NAME_PATTERN = re.compile(r'\b([A-Z][a-z]{0,50}(?:\s+[A-Z][a-z]{0,50}){1,3})\b')
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
LINKEDIN_HTTPS_PATTERN = re.compile(r'https?://(?:www\.)?linkedin\.com/in/[^\s]+')
LINKEDIN_PLAIN_PATTERN = re.compile(r'linkedin\.com/in/[^\s]+')


def sanitize_personal_identifiers(
    text: str,
    contact_map: Optional[Dict[str, int]] = None
) -> str:
    """
    Replace personal identifiers in text with placeholders.

    Replaces:
    - Person names (2-4 capitalized words) → {{CONTACT_NAME}} or {{CONTACT_NAME_<id>}}
    - Email addresses → {{CONTACT_EMAIL}}
    - LinkedIn URLs → {{CONTACT_LINKEDIN}}

    Preserves company names and technical terms from allowlists.

    Args:
        text: Input text to sanitize
        contact_map: Optional mapping of names to contact IDs
                    (e.g., {"Sarah Johnson": 1, "John Smith": 2})

    Returns:
        Text with PII replaced by placeholders

    Raises:
        ValueError: If input text exceeds maximum length or contact_map is invalid
        TypeError: If contact_map contains invalid types
    """
    # Input validation
    if not text:
        return text

    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"Input text exceeds maximum length of {MAX_TEXT_LENGTH}")

    if contact_map:
        if len(contact_map) > MAX_CONTACT_MAP_SIZE:
            raise ValueError(f"Contact map exceeds maximum size of {MAX_CONTACT_MAP_SIZE} entries")
        for name, contact_id in contact_map.items():
            if not isinstance(name, str) or not isinstance(contact_id, int):
                raise TypeError("contact_map must map str -> int")
            if contact_id <= 0:
                raise ValueError(f"Invalid contact_id: must be positive integer")

    sanitized = text

    # Remove LinkedIn URLs (using pre-compiled patterns)
    sanitized = LINKEDIN_HTTPS_PATTERN.sub('{{CONTACT_LINKEDIN}}', sanitized)
    sanitized = LINKEDIN_PLAIN_PATTERN.sub('{{CONTACT_LINKEDIN}}', sanitized)

    # Remove email addresses (using pre-compiled pattern)
    sanitized = EMAIL_PATTERN.sub('{{CONTACT_EMAIL}}', sanitized)

    # First, protect company names and technical terms by replacing them with markers
    # This prevents them from being matched as names
    # Use UUID-based markers to prevent collisions with input text
    protected_terms = {}
    unique_id = uuid.uuid4().hex
    for i, term in enumerate(sorted(list(COMPANY_NAMES) + list(TECHNICAL_TERMS))):
        marker = f"__PII_PROTECTED_{unique_id}_{i}__"
        protected_terms[marker] = term
        # Use word boundaries to match whole terms
        pattern = r'\b' + re.escape(term) + r'\b'
        sanitized = re.sub(pattern, marker, sanitized, flags=re.IGNORECASE)

    # Now remove person names (2-4 capitalized words)
    # Using pre-compiled pattern with explicit length limits to prevent ReDoS
    def replace_name(match):
        name = match.group(1)

        # Check if this is in the contact map
        if contact_map and name in contact_map:
            contact_id = contact_map[name]
            return f'{{{{CONTACT_NAME_{contact_id}}}}}'
        else:
            return '{{CONTACT_NAME}}'

    sanitized = NAME_PATTERN.sub(replace_name, sanitized)

    # Restore protected terms
    for marker, term in protected_terms.items():
        sanitized = sanitized.replace(marker, term)

    return sanitized


def restore_personal_identifiers(
    text: str,
    contact_map: Dict[str, str]
) -> str:
    """
    Restore original values from placeholder text using contact map.

    Args:
        text: Text containing placeholders (e.g., "{{CONTACT_NAME}}", "{{CONTACT_NAME_42}}")
        contact_map: Mapping of placeholders to original values
                    (e.g., {"{{CONTACT_NAME_1}}": "Sarah Johnson"})

    Returns:
        Text with placeholders replaced by original values from contact_map.
        If a placeholder is not in the map, it remains unchanged.
    """
    if not text or not contact_map:
        return text

    result = text
    for placeholder, value in contact_map.items():
        result = result.replace(placeholder, value)

    return result


def extract_placeholder_ids(text: str) -> List[int]:
    """
    Extract contact IDs from placeholders in text.

    Looks for patterns like {{CONTACT_NAME_123}} and extracts the numeric ID.

    Args:
        text: Text containing placeholders with IDs

    Returns:
        List of extracted IDs in order of appearance (may contain duplicates)
    """
    if not text:
        return []

    # Match {{CONTACT_*_<id>}} patterns
    pattern = r'\{\{CONTACT_\w+_(\d+)\}\}'
    matches = re.findall(pattern, text)

    return [int(match) for match in matches]


def sanitize_with_id_mapping(
    text: str,
    name_to_id: Dict[str, int]
) -> Tuple[str, Dict[str, str]]:
    """
    Sanitize text and create a restore map with IDs.

    Convenience function that combines sanitization with ID mapping
    and returns both the sanitized text and a restore map.

    Args:
        text: Input text to sanitize
        name_to_id: Mapping of names to contact IDs

    Returns:
        Tuple of (sanitized_text, restore_map)
        where restore_map maps placeholders to original names
    """
    sanitized = sanitize_personal_identifiers(text, name_to_id)

    # Create restore map: placeholder -> original name
    restore_map = {}
    for name, contact_id in name_to_id.items():
        placeholder = f'{{{{CONTACT_NAME_{contact_id}}}}}'
        restore_map[placeholder] = name

    return sanitized, restore_map
