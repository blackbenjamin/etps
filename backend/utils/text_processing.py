"""
Text Processing Utilities

Functions for fetching, cleaning, and extracting content from job descriptions.
"""

import re
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ExtractionQuality:
    """Results of job description extraction quality validation."""
    is_valid: bool
    score: int  # 0-100
    issues: List[str]
    suggestions: List[str]

    @property
    def error_message(self) -> Optional[str]:
        """Generate user-friendly error message if extraction failed."""
        if self.is_valid:
            return None

        msg_parts = ["Unable to automatically extract job description from this URL."]

        if self.issues:
            msg_parts.append(f"Issues detected: {'; '.join(self.issues)}")

        if self.suggestions:
            msg_parts.append(self.suggestions[0])  # Primary suggestion

        return " ".join(msg_parts)


def validate_extraction_quality(
    text: str,
    source_url: Optional[str] = None
) -> ExtractionQuality:
    """
    Validate the quality of extracted job description content.

    Checks for:
    - Minimum content length
    - Presence of job-related keywords
    - Absence of error indicators (login walls, JS-only content)
    - Ratio of meaningful content vs boilerplate

    Args:
        text: Extracted text content
        source_url: Original URL (for context-specific validation)

    Returns:
        ExtractionQuality with validation results
    """
    issues = []
    suggestions = []
    score = 100

    # Check 1: Minimum length
    if len(text) < 200:
        issues.append("Content too short")
        score -= 40
    elif len(text) < 500:
        issues.append("Limited content extracted")
        score -= 20

    # Check 2: Job-related keywords
    job_keywords = [
        'responsibilities', 'requirements', 'qualifications', 'experience',
        'skills', 'duties', 'role', 'position', 'job', 'work', 'team',
        'salary', 'benefits', 'apply', 'candidate', 'years'
    ]
    text_lower = text.lower()
    keyword_count = sum(1 for kw in job_keywords if kw in text_lower)

    if keyword_count < 2:
        issues.append("Missing job-related content")
        score -= 30
    elif keyword_count < 4:
        score -= 10

    # Check 3: Error indicators
    error_indicators = [
        ('please enable javascript', 'JavaScript required'),
        ('sign in to continue', 'Login wall detected'),
        ('log in to view', 'Login wall detected'),
        ('access denied', 'Access denied'),
        ('page not found', 'Page not found'),
        ('404', 'Page not found'),
        ('captcha', 'CAPTCHA required'),
        ('robot', 'Bot detection'),
        ('cookies must be enabled', 'Cookies required'),
    ]

    for indicator, issue in error_indicators:
        if indicator in text_lower:
            issues.append(issue)
            score -= 25

    # Check 4: Boilerplate ratio (EEO, legal content)
    boilerplate_patterns = [
        r'equal\s+opportunity\s+employer',
        r'eeo\s+statement',
        r'we\s+are\s+an\s+equal',
        r'voluntary\s+self[- ]?identification',
        r'protected\s+characteristic',
        r'cookie\s+policy',
        r'privacy\s+policy',
        r'terms\s+of\s+(service|use)',
    ]

    boilerplate_matches = sum(
        1 for pattern in boilerplate_patterns
        if re.search(pattern, text_lower)
    )

    # If most of the content is boilerplate
    if boilerplate_matches >= 3 and len(text) < 1000:
        issues.append("Content mostly legal/EEO boilerplate")
        score -= 30

    # Check 5: Skills extraction potential
    skill_indicators = [
        r'\d+\+?\s*years?\s*(of\s+)?experience',
        r'proficien(t|cy)\s+in',
        r'experience\s+with',
        r'knowledge\s+of',
        r'familiar(ity)?\s+with',
        r'degree\s+in',
        r'bachelor|master|phd',
    ]

    skill_count = sum(
        1 for pattern in skill_indicators
        if re.search(pattern, text_lower)
    )

    if skill_count == 0:
        issues.append("No skill requirements detected")
        score -= 15

    # Generate suggestions based on issues
    if score < 60:
        suggestions.append(
            "Please copy and paste the full job description text directly instead of using the URL."
        )

    # Determine validity
    is_valid = score >= 50 and len(issues) <= 2

    return ExtractionQuality(
        is_valid=is_valid,
        score=max(0, score),
        issues=issues,
        suggestions=suggestions
    )


class ExtractionFailedError(Exception):
    """Raised when job description extraction fails quality validation."""

    def __init__(self, message: str, quality: ExtractionQuality):
        self.message = message
        self.quality = quality
        super().__init__(message)


def fetch_url_content(url: str, timeout: int = 10, validate: bool = True) -> str:
    """
    Fetch HTML content from a URL and extract clean text.

    Args:
        url: The URL to fetch content from
        timeout: Request timeout in seconds (default: 10)
        validate: Whether to validate extraction quality (default: True)

    Returns:
        Cleaned text content from the URL

    Raises:
        requests.RequestException: If the request fails
        ValueError: If the URL is invalid or empty
        ExtractionFailedError: If extraction quality is too low
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    original_url = url  # Keep for error messages

    # Add schema if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Normalize job board URLs to get job description page (not apply page)
    url = _normalize_job_url(url)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()

    # Parse HTML and extract text
    soup = BeautifulSoup(response.content, 'html.parser')

    # For JS-rendered pages (Lever, etc.), try to extract from meta tags first
    is_js_rendered = 'jobs.lever.co' in url or 'greenhouse.io' in url
    if is_js_rendered:
        meta_text = _extract_meta_description(soup)
        if meta_text and len(meta_text) > 200:
            text = clean_text(meta_text)
            # Validate and potentially fail for JS-rendered pages
            if validate:
                quality = validate_extraction_quality(text, original_url)
                if not quality.is_valid:
                    logger.warning(
                        f"Extraction quality check failed for {original_url}: "
                        f"score={quality.score}, issues={quality.issues}"
                    )
                    raise ExtractionFailedError(
                        quality.error_message or "Failed to extract job description",
                        quality
                    )
            return text

    # Remove script and style elements (but keep meta for potential later use)
    for script in soup(["script", "style", "link"]):
        script.decompose()

    # Remove EEO/legal boilerplate sections
    _remove_boilerplate_sections(soup)

    # Get text content
    text = soup.get_text(separator='\n')

    # Clean the text and remove EEO content
    text = clean_text(text)
    text = _filter_eeo_content(text)

    # If we got very little content, fall back to meta description
    if len(text) < 200:
        meta_text = _extract_meta_description(BeautifulSoup(response.content, 'html.parser'))
        if meta_text:
            text = clean_text(meta_text)

    # Validate extraction quality
    if validate:
        quality = validate_extraction_quality(text, original_url)
        if not quality.is_valid:
            logger.warning(
                f"Extraction quality check failed for {original_url}: "
                f"score={quality.score}, issues={quality.issues}"
            )
            raise ExtractionFailedError(
                quality.error_message or "Failed to extract job description",
                quality
            )

    return text


def _normalize_job_url(url: str) -> str:
    """
    Normalize job board URLs to get the job description page.

    Handles:
    - Lever: Remove /apply suffix
    - Greenhouse: Remove /applications/new suffix
    - Workday: Keep as-is (requires different handling)

    Args:
        url: The job posting URL

    Returns:
        Normalized URL pointing to job description
    """
    # Lever: remove /apply or /apply/ suffix
    if 'jobs.lever.co' in url:
        url = re.sub(r'/apply/?$', '', url)

    # Greenhouse: remove application path
    if 'greenhouse.io' in url:
        url = re.sub(r'/applications/new/?$', '', url)

    return url


def parse_workday_url(url: str) -> dict:
    """
    Extract job metadata from Workday URL structure.

    Workday URLs follow patterns like:
    - company.wd1.myworkdayjobs.com/site/job/LOCATION/Job-Title_ID
    - company.wd5.myworkdayjobs.com/en-US/External/job/City/Job-Title_ID

    Args:
        url: Workday job URL

    Returns:
        Dict with company_name, job_title, location (any found)
    """
    result = {
        'company_name': None,
        'job_title': None,
        'location': None,
    }

    if 'myworkdayjobs.com' not in url:
        return result

    try:
        from urllib.parse import urlparse, unquote
        parsed = urlparse(url)

        # Extract company from subdomain (e.g., "statestreet" from statestreet.wd1.myworkdayjobs.com)
        hostname = parsed.hostname or ''
        if hostname:
            company_part = hostname.split('.')[0]
            if company_part and company_part not in ['www', 'jobs']:
                # Convert to title case and handle common patterns
                result['company_name'] = company_part.replace('-', ' ').title()

        # Parse the path: /site/job/LOCATION/Job-Title_ID or /en-US/External/job/City/Job-Title_ID
        path_parts = [p for p in parsed.path.split('/') if p]

        # Find "job" in path and extract what follows
        if 'job' in path_parts:
            job_idx = path_parts.index('job')
            remaining = path_parts[job_idx + 1:]

            if len(remaining) >= 2:
                # Pattern: /job/LOCATION/Job-Title_ID
                location_part = remaining[0]
                title_part = remaining[1]

                # Location is usually uppercase city/region
                if location_part.isupper() or location_part[0].isupper():
                    result['location'] = unquote(location_part).replace('-', ' ').title()

                # Title: strip ID suffix and convert dashes to spaces
                if '_' in title_part:
                    title_part = title_part.rsplit('_', 1)[0]  # Remove _R-123456 suffix
                result['job_title'] = unquote(title_part).replace('--', ' - ').replace('-', ' ')

            elif len(remaining) == 1:
                # Just title/ID
                title_part = remaining[0]
                if '_' in title_part:
                    title_part = title_part.rsplit('_', 1)[0]
                result['job_title'] = unquote(title_part).replace('--', ' - ').replace('-', ' ')

    except Exception as e:
        logger.warning(f"Failed to parse Workday URL {url}: {e}")

    return result


def _extract_meta_description(soup: BeautifulSoup) -> str:
    """
    Extract job description from meta tags (used by JS-rendered pages like Lever).

    Lever and similar platforms store the full job description in Open Graph
    and Twitter Card meta tags, which are available even without JS rendering.

    Note: Meta tags typically contain only a summary. For full job details,
    users should paste the complete job description text.

    Args:
        soup: BeautifulSoup parsed HTML

    Returns:
        Job description from meta tags, or empty string if not found
    """
    meta_content = []

    # Get title from <title> or og:title
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text().strip()
        # Clean Lever-style titles: "Company - Job Title"
        if ' - ' in title_text:
            parts = title_text.split(' - ', 1)
            if len(parts) == 2:
                meta_content.append(f"Company: {parts[0].strip()}")
                meta_content.append(f"Job Title: {parts[1].strip()}")
            else:
                meta_content.append(f"Job Title: {title_text}")
        else:
            meta_content.append(f"Job Title: {title_text}")

    # Get location from twitter:data1 (Lever puts location there)
    location_meta = soup.find('meta', {'name': 'twitter:data1'})
    if location_meta and location_meta.get('content'):
        meta_content.append(f"Location: {location_meta['content']}")

    # Get team/department from twitter:data2
    team_meta = soup.find('meta', {'name': 'twitter:data2'})
    if team_meta and team_meta.get('content'):
        meta_content.append(f"Team: {team_meta['content']}")

    # Get description from og:description or twitter:description
    # These contain the full job description on Lever
    for meta_name in ['og:description', 'twitter:description']:
        desc_meta = soup.find('meta', {'property': meta_name}) or soup.find('meta', {'name': meta_name})
        if desc_meta and desc_meta.get('content'):
            description = desc_meta['content'].strip()
            if len(description) > 100:  # Only use if substantial
                meta_content.append("\nJob Description:")
                meta_content.append(description)
                break

    # If we only got minimal content from a JS-rendered page, add a note
    if meta_content and len('\n'.join(meta_content)) < 500:
        meta_content.append("\n\nNote: This job posting uses JavaScript rendering. "
                          "For full requirements and skills, please paste the complete job description text.")

    return '\n'.join(meta_content)


def _remove_boilerplate_sections(soup: BeautifulSoup) -> None:
    """
    Remove EEO, legal disclaimer, and application form sections from parsed HTML.

    Modifies soup in-place.
    """
    # Common class/id patterns for EEO and form sections
    boilerplate_patterns = [
        'eeo', 'equal-opportunity', 'diversity', 'voluntary-survey',
        'apply-form', 'application-form', 'submit-application',
        'legal-disclaimer', 'privacy-policy', 'cookie-notice'
    ]

    # Remove elements with matching class or id
    for pattern in boilerplate_patterns:
        for element in soup.find_all(class_=re.compile(pattern, re.IGNORECASE)):
            element.decompose()
        for element in soup.find_all(id=re.compile(pattern, re.IGNORECASE)):
            element.decompose()

    # Remove form elements entirely (application forms)
    for form in soup.find_all('form'):
        form.decompose()


def _filter_eeo_content(text: str) -> str:
    """
    Filter out EEO statements and legal boilerplate from text content.

    Args:
        text: Cleaned text content

    Returns:
        Text with EEO/legal content removed
    """
    # Patterns that indicate EEO/legal sections
    eeo_start_patterns = [
        r'^.*equal\s+employment\s+opportunity.*$',
        r'^.*eeo\s+(statement|policy|voluntary).*$',
        r'^.*we\s+(are\s+)?an?\s+equal\s+opportunity.*$',
        r'^.*voluntary\s+(self[- ]?)?identification.*$',
        r'^.*diversity\s+(and|&)\s+inclusion.*$',
        r'^.*work\s+authorization\s+status.*$',
        r'^.*protected\s+characteristic.*$',
        r'^.*additional\s+information.*$',
        r'^.*eeo\s+voluntary\s+survey.*$',
        r'^.*submission\s+of\s+the\s+information\s+on\s+this\s+form.*$',
        r'^.*we\s+invite\s+you\s+to\s+complete\s+this\s+optional\s+survey.*$',
    ]

    lines = text.split('\n')
    filtered_lines = []
    skip_mode = False

    for line in lines:
        line_lower = line.lower().strip()

        # Check if this line starts an EEO section
        for pattern in eeo_start_patterns:
            if re.match(pattern, line_lower, re.IGNORECASE):
                skip_mode = True
                break

        # If we're in skip mode, check if we've hit a new section header
        if skip_mode:
            # New section indicators that end skip mode
            new_section_patterns = [
                r'^(about|responsibilities|requirements|qualifications|what\s+you)',
                r'^(the\s+role|your\s+role|job\s+description)',
            ]
            for pattern in new_section_patterns:
                if re.match(pattern, line_lower):
                    skip_mode = False
                    break

        if not skip_mode:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def clean_text(text: str) -> str:
    """
    Normalize whitespace and clean text content.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text with normalized whitespace
    """
    if not text:
        return ""

    # Replace multiple whitespace characters with single space
    text = re.sub(r'[ \t]+', ' ', text)

    # Replace multiple newlines with maximum of two
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]

    # Remove empty lines at start and end
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()

    return '\n'.join(lines)


def extract_bullets(text: str) -> List[str]:
    """
    Extract bullet points from text.

    Recognizes common bullet markers:
    - Asterisks (*)
    - Hyphens (-)
    - Plus signs (+)
    - Unicode bullets (•, ◦, ▪, ▫)
    - Numbered lists (1., 2., etc.)

    Args:
        text: Text containing bullet points

    Returns:
        List of extracted bullet point strings (without markers)
    """
    if not text:
        return []

    bullets = []
    lines = text.split('\n')

    # Regex patterns for different bullet styles
    bullet_patterns = [
        r'^[\s]*[-*+•◦▪▫]\s+(.+)$',  # Symbol bullets
        r'^[\s]*\d+[\.)]\s+(.+)$',   # Numbered bullets
    ]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        for pattern in bullet_patterns:
            match = re.match(pattern, line)
            if match:
                bullet_text = match.group(1).strip()
                if bullet_text:
                    bullets.append(bullet_text)
                break

    return bullets
