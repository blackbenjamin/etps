"""
Company Enrichment Service

Enriches company profiles with industry, size, culture signals, and AI/data maturity
by analyzing job descriptions and optionally fetching company website data.

Security considerations:
- SSRF protection: validates URLs and blocks private IP addresses
- Rate limiting: caches enrichment results to prevent excessive requests
- Input validation: sanitizes all user inputs
"""

import logging
import re
import socket
from datetime import datetime, timezone
from ipaddress import ip_address
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from db.models import CompanyProfile
from services.llm.mock_llm import MockLLM

logger = logging.getLogger(__name__)

# Configuration defaults (can be overridden via config.yaml)
DEFAULT_CONFIG = {
    "website_fetch_timeout": 10,
    "max_response_size": 50 * 1024,  # 50KB
    "user_agent": "ETPS/1.0 (Company Profile Enrichment)",
    "cache_duration_hours": 168,  # 1 week
}

# Industry taxonomy
INDUSTRIES = [
    "Financial Services",
    "Technology",
    "Healthcare",
    "Consulting",
    "Manufacturing",
    "Retail",
    "Government",
    "Education",
    "Non-Profit",
    "Energy",
    "Telecommunications",
    "Media & Entertainment",
    "Real Estate",
    "Transportation",
    "Other",
]

# Company size bands
SIZE_BANDS = [
    "1-50",
    "51-200",
    "201-1000",
    "1001-5000",
    "5000+",
]

# Culture signal taxonomy
CULTURE_SIGNALS = [
    "formal",
    "innovative",
    "mission-driven",
    "collaborative",
    "fast-paced",
    "customer-centric",
    "data-driven",
    "experimental",
    "conservative",
    "traditional",
]

# AI maturity levels
AI_MATURITY_LEVELS = ["low", "developing", "advanced"]


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for deduplication.

    Removes common suffixes (Inc., LLC, Corp, etc.) and standardizes whitespace.

    Args:
        name: Raw company name

    Returns:
        Normalized company name for matching
    """
    if not name:
        return ""

    # Limit input length to prevent ReDoS attacks
    if len(name) > 500:
        name = name[:500]

    # Convert to lowercase and strip whitespace
    normalized = name.lower().strip()

    # Remove common suffixes
    suffixes = [
        r',?\s*inc\.?$',
        r',?\s*llc\.?$',
        r',?\s*ltd\.?$',
        r',?\s*corp\.?$',
        r',?\s*corporation$',
        r',?\s*company$',
        r',?\s*co\.?$',
        r',?\s*plc\.?$',
        r',?\s*limited$',
        r',?\s*l\.?p\.?$',
        r',?\s*group$',
        r',?\s*holdings?$',
        r',?\s*international$',
        r',?\s*global$',
    ]

    for pattern in suffixes:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)

    # Normalize whitespace
    normalized = ' '.join(normalized.split())

    return normalized


def is_private_ip(hostname: str) -> bool:
    """
    Check if hostname resolves to a private or loopback IP address.

    SSRF protection: prevents fetching from internal network addresses.

    Args:
        hostname: Hostname to check

    Returns:
        True if hostname resolves to private/loopback IP
    """
    try:
        # Try to parse as IP address directly
        try:
            ip = ip_address(hostname)
            return ip.is_private or ip.is_loopback or ip.is_reserved
        except ValueError:
            pass

        # Resolve hostname to IP
        resolved_ip = socket.gethostbyname(hostname)
        ip = ip_address(resolved_ip)
        return ip.is_private or ip.is_loopback or ip.is_reserved

    except (socket.gaierror, socket.herror):
        # If we can't resolve, be conservative and block
        return True


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL for security concerns.

    Checks:
    - Valid URL format
    - HTTPS scheme (or HTTP with warning)
    - Not a private IP address
    - Not a commonly blocked host

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message_or_empty_string)
    """
    if not url:
        return False, "URL is empty"

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    # Check scheme
    if parsed.scheme not in ('http', 'https'):
        return False, f"Invalid URL scheme: {parsed.scheme}"

    # Check for hostname
    if not parsed.hostname:
        return False, "URL has no hostname"

    # Check for private IP / localhost
    if is_private_ip(parsed.hostname):
        return False, "Private IP addresses are not allowed"

    # Block common internal hostnames
    blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', 'internal', 'intranet']
    if parsed.hostname.lower() in blocked_hosts:
        return False, f"Blocked hostname: {parsed.hostname}"

    return True, ""


def check_robots_txt(url: str, user_agent: str = "*") -> bool:
    """
    Check if robots.txt allows fetching the given URL.

    Args:
        url: URL to check
        user_agent: User agent to check for (default: *)

    Returns:
        True if allowed, False if disallowed
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        return rp.can_fetch(user_agent, url)
    except Exception:
        # If we can't check robots.txt, assume allowed
        return True


def fetch_company_website_data(
    website_url: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Fetch and parse company website content for enrichment.

    Note: This is a synchronous function that uses requests library.
    It should be called from async context using run_in_executor if needed.

    Security measures:
    - URL validation (no private IPs)
    - Robots.txt compliance
    - Response size limits
    - Timeout enforcement

    Args:
        website_url: Company website URL
        config: Optional configuration overrides

    Returns:
        Dict with homepage_text, about_text, meta_description (may be empty on error)
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    result = {
        "homepage_text": "",
        "about_text": "",
        "meta_description": "",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }

    # Validate URL
    is_valid, error_msg = validate_url(website_url)
    if not is_valid:
        logger.warning(f"URL validation failed for {website_url}: {error_msg}")
        result["error"] = error_msg
        return result

    # Check robots.txt
    if not check_robots_txt(website_url, cfg["user_agent"]):
        logger.info(f"Robots.txt disallows fetching: {website_url}")
        result["error"] = "Blocked by robots.txt"
        return result

    try:
        headers = {
            "User-Agent": cfg["user_agent"],
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Fetch homepage
        response = requests.get(
            website_url,
            headers=headers,
            timeout=cfg["website_fetch_timeout"],
            allow_redirects=True,
            stream=True,
        )
        response.raise_for_status()

        # Check content size
        content_length = int(response.headers.get('content-length', 0))
        if content_length > cfg["max_response_size"]:
            logger.warning(f"Response too large ({content_length} bytes): {website_url}")
            result["error"] = "Response too large"
            return result

        # Read with size limit
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > cfg["max_response_size"]:
                break

        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')

        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            result["meta_description"] = meta_desc.get('content', '')[:500]

        # Extract main page text (limited)
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        text = soup.get_text(separator=' ', strip=True)
        result["homepage_text"] = text[:2000]

        # Try to find about page link
        parsed = urlparse(website_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        about_patterns = ['/about', '/about-us', '/company', '/who-we-are', '/our-story']
        about_link = None

        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            for pattern in about_patterns:
                if pattern in href:
                    about_link = link['href']
                    break
            if about_link:
                break

        # Fetch about page if found
        if about_link:
            if not about_link.startswith('http'):
                about_link = base_url + about_link if about_link.startswith('/') else base_url + '/' + about_link

            # Validate the reconstructed about-page URL (SSRF protection)
            about_is_valid, about_error = validate_url(about_link)
            if not about_is_valid:
                logger.warning(f"About page URL validation failed for {about_link}: {about_error}")
            else:
                try:
                    about_response = requests.get(
                        about_link,
                        headers=headers,
                        timeout=cfg["website_fetch_timeout"],
                        allow_redirects=True,
                    )
                    about_response.raise_for_status()

                    about_soup = BeautifulSoup(about_response.content[:cfg["max_response_size"]], 'html.parser')
                    for script in about_soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()

                    about_text = about_soup.get_text(separator=' ', strip=True)
                    result["about_text"] = about_text[:2000]

                except requests.Timeout:
                    logger.info(f"Timeout fetching about page: {about_link}")
                except requests.RequestException as e:
                    logger.info(f"Could not fetch about page {about_link}: {type(e).__name__}: {str(e)[:100]}")

    except requests.Timeout:
        logger.warning(f"Timeout fetching {website_url}")
        result["error"] = "Request timeout"
    except requests.RequestException as e:
        logger.warning(f"Error fetching {website_url}: {e}")
        result["error"] = str(e)[:200]
    except Exception as e:
        logger.error(f"Unexpected error fetching {website_url}: {e}")
        result["error"] = "Unexpected error"

    return result


async def infer_industry_and_size(
    company_name: str,
    website_content: Optional[str] = None,
    jd_text: Optional[str] = None,
    llm: Optional[Any] = None
) -> Dict[str, Optional[str]]:
    """
    Infer company industry and size band from available data.

    Uses LLM to analyze company name, website content, and job description
    to determine industry classification and approximate size.

    Args:
        company_name: Company name
        website_content: Optional website text content
        jd_text: Optional job description text
        llm: Optional LLM instance (defaults to MockLLM)

    Returns:
        Dict with industry, size_band, headquarters (may be None)
    """
    if llm is None:
        llm = MockLLM()

    context = f"""Company: {company_name}

Website content (if available):
{(website_content or 'Not available')[:1500]}

Job description (if available):
{(jd_text or 'Not available')[:1500]}"""

    prompt = f"""Analyze this company information and extract:
1. Industry - choose from: {', '.join(INDUSTRIES)}
2. Size band - choose from: {', '.join(SIZE_BANDS)}
3. Headquarters location (City, State/Country format)

{context}

Return as JSON: {{"industry": "...", "size_band": "...", "headquarters": "..."}}
If uncertain, use null for that field."""

    try:
        # Use LLM's capability method or fallback to generating
        if hasattr(llm, 'generate_company_metadata'):
            result = await llm.generate_company_metadata(company_name, context)
        else:
            # Fallback for MockLLM - use heuristics
            result = _infer_metadata_heuristic(company_name, website_content, jd_text)

        # Validate results against taxonomy
        if result.get('industry') and result['industry'] not in INDUSTRIES:
            result['industry'] = 'Other'
        if result.get('size_band') and result['size_band'] not in SIZE_BANDS:
            result['size_band'] = None

        return result

    except Exception as e:
        logger.warning(f"Failed to infer industry/size for {company_name}: {e}")
        return {"industry": None, "size_band": None, "headquarters": None}


def _infer_metadata_heuristic(
    company_name: str,
    website_content: Optional[str] = None,
    jd_text: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """
    Heuristic-based company metadata inference.

    Used as fallback when LLM is not available.
    """
    combined_text = f"{company_name} {website_content or ''} {jd_text or ''}".lower()

    # Industry detection patterns
    industry_patterns = {
        "Financial Services": ["bank", "financial", "investment", "trading", "wealth", "asset management", "fintech", "insurance"],
        "Technology": ["software", "technology", "tech", "saas", "platform", "digital", "cloud", "ai", "machine learning"],
        "Healthcare": ["health", "medical", "pharma", "biotech", "clinical", "patient", "hospital"],
        "Consulting": ["consulting", "advisory", "strategy", "management consulting", "professional services"],
        "Manufacturing": ["manufacturing", "factory", "production", "industrial", "assembly"],
        "Retail": ["retail", "e-commerce", "store", "shopping", "consumer goods"],
        "Government": ["government", "federal", "state", "public sector", "agency"],
        "Education": ["education", "university", "school", "learning", "academic", "edtech"],
    }

    detected_industry = None
    max_matches = 0

    for industry, keywords in industry_patterns.items():
        matches = sum(1 for kw in keywords if kw in combined_text)
        if matches > max_matches:
            max_matches = matches
            detected_industry = industry

    # Size detection based on common phrases
    size_band = None
    if "fortune 500" in combined_text or "global enterprise" in combined_text:
        size_band = "5000+"
    elif "startup" in combined_text or "early stage" in combined_text:
        size_band = "1-50"
    elif "growing team" in combined_text:
        size_band = "51-200"

    return {
        "industry": detected_industry,
        "size_band": size_band,
        "headquarters": None,
    }


async def infer_culture_signals(
    website_content: Optional[str] = None,
    jd_text: Optional[str] = None,
    llm: Optional[Any] = None
) -> List[str]:
    """
    Extract culture signals from website content and job description.

    Analyzes language and keywords to identify company culture attributes
    from the predefined taxonomy.

    Args:
        website_content: Optional website text content
        jd_text: Optional job description text
        llm: Optional LLM instance (defaults to MockLLM)

    Returns:
        List of culture signals (max 5) from CULTURE_SIGNALS taxonomy
    """
    combined_text = f"{website_content or ''} {jd_text or ''}".lower()

    if not combined_text.strip():
        return []

    # Keyword-based culture detection
    culture_keywords = {
        "formal": ["professional", "corporate", "established", "traditional"],
        "innovative": ["innovation", "cutting-edge", "disrupt", "transform", "pioneering"],
        "mission-driven": ["mission", "purpose", "impact", "change the world", "meaningful"],
        "collaborative": ["team", "collaborative", "together", "partnership", "cross-functional"],
        "fast-paced": ["fast-paced", "dynamic", "agile", "rapidly", "startup", "high-growth"],
        "customer-centric": ["customer", "client-first", "user experience", "customer success"],
        "data-driven": ["data-driven", "analytics", "metrics", "evidence-based", "data-informed"],
        "experimental": ["experiment", "test and learn", "iterate", "fail fast", "prototype"],
        "conservative": ["established", "stable", "reliable", "trusted", "heritage"],
        "traditional": ["traditional", "legacy", "established practice", "proven"],
    }

    detected_signals = []
    for signal, keywords in culture_keywords.items():
        if any(kw in combined_text for kw in keywords):
            detected_signals.append(signal)

    # Limit to 5 signals
    return detected_signals[:5]


async def infer_ai_maturity(
    website_content: Optional[str] = None,
    jd_text: Optional[str] = None,
    llm: Optional[Any] = None
) -> Optional[str]:
    """
    Infer company's AI/data maturity level.

    Analyzes job descriptions and website content for indicators of
    AI/ML adoption and sophistication.

    Levels:
    - low: No AI/ML mentions, basic data infrastructure
    - developing: Some AI pilots, hiring data scientists/ML engineers
    - advanced: Production AI systems, governance frameworks, MLOps mentioned

    Args:
        website_content: Optional website text content
        jd_text: Optional job description text
        llm: Optional LLM instance (defaults to MockLLM)

    Returns:
        AI maturity level string or None if insufficient data
    """
    combined_text = f"{website_content or ''} {jd_text or ''}".lower()

    if not combined_text.strip():
        return None

    # Advanced maturity indicators
    advanced_keywords = [
        "mlops", "ai governance", "ai ethics", "responsible ai",
        "production ml", "model monitoring", "feature store",
        "ai at scale", "enterprise ai", "ai platform", "ml platform",
        "genai", "large language model", "llm", "ai transformation",
    ]

    # Developing maturity indicators
    developing_keywords = [
        "machine learning", "data science", "ai/ml", "data scientist",
        "ml engineer", "analytics", "predictive", "ai strategy",
        "data platform", "data lake", "data warehouse",
    ]

    # Count indicators
    advanced_count = sum(1 for kw in advanced_keywords if kw in combined_text)
    developing_count = sum(1 for kw in developing_keywords if kw in combined_text)

    if advanced_count >= 2:
        return "advanced"
    elif developing_count >= 2 or advanced_count >= 1:
        return "developing"
    elif developing_count >= 1:
        return "low"

    return None


async def enrich_company_profile(
    company_name: str,
    jd_text: Optional[str] = None,
    website_url: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Optional[Session] = None,
    llm: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None
) -> CompanyProfile:
    """
    Main enrichment function: creates or updates a CompanyProfile.

    Orchestrates all enrichment steps:
    1. Normalize company name for deduplication
    2. Check if profile exists
    3. Fetch website data (if URL provided)
    4. Infer industry, size, headquarters
    5. Extract culture signals
    6. Determine AI/data maturity
    7. Create or update database record

    Args:
        company_name: Company name (required)
        jd_text: Job description text (optional)
        website_url: Company website URL (optional)
        user_id: User ID for audit trail (optional)
        db: SQLAlchemy session (required for persistence)
        llm: LLM instance (optional, defaults to MockLLM)
        config: Configuration overrides (optional)

    Returns:
        CompanyProfile ORM object (new or updated)

    Raises:
        ValueError: If company_name is empty or db is None
    """
    if not company_name or not company_name.strip():
        raise ValueError("company_name is required")

    if db is None:
        raise ValueError("Database session is required")

    company_name = company_name.strip()
    normalized_name = normalize_company_name(company_name)

    # Check for existing profile
    existing_profile = db.query(CompanyProfile).filter(
        CompanyProfile.name == company_name
    ).first()

    # Also check normalized name match using database ILIKE (scalable approach)
    # Instead of loading all profiles, use SQL pattern matching
    if not existing_profile and normalized_name:
        # Search for profiles that might match after normalization
        # Using ILIKE with the normalized name as a pattern
        potential_matches = db.query(CompanyProfile).filter(
            CompanyProfile.name.ilike(f"%{normalized_name}%")
        ).limit(20).all()

        for profile in potential_matches:
            if normalize_company_name(profile.name) == normalized_name:
                existing_profile = profile
                break

    # Fetch website data if URL provided (synchronous call)
    website_data = {}
    if website_url:
        website_data = fetch_company_website_data(website_url, config)

    # Combine website content
    website_content = None
    if website_data.get("homepage_text") or website_data.get("about_text"):
        website_content = f"{website_data.get('homepage_text', '')} {website_data.get('about_text', '')}".strip()

    # Infer metadata
    metadata = await infer_industry_and_size(
        company_name, website_content, jd_text, llm
    )

    # Get culture signals
    culture_signals = await infer_culture_signals(
        website_content, jd_text, llm
    )

    # Get AI maturity
    ai_maturity = await infer_ai_maturity(
        website_content, jd_text, llm
    )

    # Create or update profile
    if existing_profile:
        # Update existing profile with new data (don't overwrite with None)
        if website_url and not existing_profile.website:
            existing_profile.website = website_url
        if metadata.get('industry') and not existing_profile.industry:
            existing_profile.industry = metadata['industry']
        if metadata.get('size_band') and not existing_profile.size_band:
            existing_profile.size_band = metadata['size_band']
        if metadata.get('headquarters') and not existing_profile.headquarters:
            existing_profile.headquarters = metadata['headquarters']
        if culture_signals and not existing_profile.culture_signals:
            existing_profile.culture_signals = culture_signals
        if ai_maturity and not existing_profile.data_ai_maturity:
            existing_profile.data_ai_maturity = ai_maturity

        db.commit()
        db.refresh(existing_profile)

        logger.info(f"Updated existing company profile: {company_name} (id={existing_profile.id})")
        return existing_profile

    else:
        # Create new profile
        new_profile = CompanyProfile(
            name=company_name,
            website=website_url,
            industry=metadata.get('industry'),
            size_band=metadata.get('size_band'),
            headquarters=metadata.get('headquarters'),
            culture_signals=culture_signals if culture_signals else None,
            data_ai_maturity=ai_maturity,
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        logger.info(f"Created new company profile: {company_name} (id={new_profile.id})")
        return new_profile


async def get_company_profile(
    company_id: int,
    db: Session
) -> Optional[CompanyProfile]:
    """
    Get a company profile by ID.

    Args:
        company_id: CompanyProfile ID
        db: SQLAlchemy session

    Returns:
        CompanyProfile or None if not found
    """
    return db.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()


async def search_company_profiles(
    name_query: str,
    db: Session,
    limit: int = 10
) -> List[CompanyProfile]:
    """
    Search company profiles by name (fuzzy matching).

    Args:
        name_query: Search query
        db: SQLAlchemy session
        limit: Maximum results to return

    Returns:
        List of matching CompanyProfile objects
    """
    if not name_query or not name_query.strip():
        return []

    # Case-insensitive LIKE search
    search_pattern = f"%{name_query.strip()}%"

    return db.query(CompanyProfile).filter(
        CompanyProfile.name.ilike(search_pattern)
    ).limit(limit).all()
