"""
Text Processing Utilities

Functions for fetching, cleaning, and extracting content from job descriptions.
"""

import re
from typing import List
import requests
from bs4 import BeautifulSoup


def fetch_url_content(url: str, timeout: int = 10) -> str:
    """
    Fetch HTML content from a URL and extract clean text.

    Args:
        url: The URL to fetch content from
        timeout: Request timeout in seconds (default: 10)

    Returns:
        Cleaned text content from the URL

    Raises:
        requests.RequestException: If the request fails
        ValueError: If the URL is invalid or empty
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    # Add schema if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()

    # Parse HTML and extract text
    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style", "meta", "link"]):
        script.decompose()

    # Get text content
    text = soup.get_text(separator='\n')

    # Clean the text
    return clean_text(text)


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
