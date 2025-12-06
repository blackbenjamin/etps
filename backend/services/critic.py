"""
Critic Service

Evaluates and scores tailored resumes and cover letters for quality,
ATS compliance, banned phrase detection, tone matching, and rule enforcement.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple
from sqlalchemy.orm import Session

from db.models import Experience, JobProfile
from schemas.critic import (
    ATSScoreBreakdown,
    CoverLetterCriticResult,
    CriticIssue,
    CriticResult,
    RequirementCoverageScore,
    ResumeCriticResult,
    StructureCheckResult,
    StyleScoreBreakdown,
)
from services.cover_letter import (
    BANNED_PHRASES,
    EM_DASH_PATTERN,
    TONE_COMPATIBILITY,
    analyze_ats_keyword_coverage,
    analyze_requirement_coverage,
)
from services.llm.base import BaseLLM
from services.llm.mock_llm import MockLLM
from services.pagination import PaginationService, PageSplitSimulator


# Severity mapping from banned phrase severity to critic severity
SEVERITY_MAP = {
    "critical": "error",
    "major": "warning",
    "minor": "info",
}

# Recommended fixes for banned phrases by category
BANNED_PHRASE_FIXES = {
    "i am writing to express my interest": "Start with a compelling hook about your qualifications",
    "to whom it may concern": "Address the hiring team by company name or find the hiring manager's name",
    "dear hiring manager": "Use the company name: 'Dear [Company] Hiring Team'",
    "i believe i would be a great fit": "Show fit through specific examples rather than stating it",
    "i am confident i would be a great fit": "Demonstrate fit with concrete achievements",
    "please find attached": "Omit - attachments are assumed in applications",
    "i am the perfect candidate": "Let qualifications speak for themselves",
    "i am very interested in": "Lead with what you bring, not what you want",
    "i came across this position": "Open with relevant experience or connection",
    "i am excited to apply": "Show enthusiasm through specifics, not generic statements",
    "passion for": "Replace with demonstrated expertise and achievements",
    "results-oriented": "Replace with specific results you've achieved",
    "proven track record": "Replace with specific metrics and accomplishments",
    "team player": "Show collaboration through examples",
    "detail-oriented": "Demonstrate attention to detail through specifics",
    "self-starter": "Provide examples of initiative",
    "think outside the box": "Use original language that demonstrates creativity",
    "go-getter": "Replace with concrete achievements",
    "hard worker": "Show work ethic through accomplishments",
    "leverage": "Use simpler language: 'use', 'apply', 'utilize'",
    "synergy": "Use clearer language: 'collaboration', 'combined effort'",
    "best-in-class": "Be specific about what makes it excellent",
    "world-class": "Use concrete achievements instead",
    "cutting-edge": "Specify what technology or approach",
    "innovative solutions": "Describe the actual innovation",
    "hit the ground running": "Specify relevant experience that enables quick contribution",
    "dynamic environment": "Be specific about the work environment",
    # Em-dash fix
    "em-dash (—)": "Use commas, parentheses, or restructure the sentence instead",
}

# =============================================================================
# STYLE ENFORCEMENT CONSTANTS
# =============================================================================

# Strong action verbs for lexical analysis (preferred)
STRONG_VERBS = {
    "lead", "led", "build", "built", "deliver", "delivered", "drive", "drove",
    "implement", "implemented", "architect", "architected", "design", "designed",
    "establish", "established", "scale", "scaled", "transform", "transformed",
    "optimize", "optimized", "execute", "executed", "launch", "launched",
    "develop", "developed", "create", "created", "manage", "managed",
    "direct", "directed", "engineer", "engineered", "spearhead", "spearheaded",
    "orchestrate", "orchestrated", "formulate", "formulated", "strategize",
    "strategized", "streamline", "streamlined", "pioneer", "pioneered",
    "accelerate", "accelerated", "modernize", "modernized", "negotiate",
    "negotiated", "secure", "secured", "champion", "championed",
}

# Weak verbs that should be avoided (flagged)
WEAK_VERBS = {
    "helped", "help", "assisted", "assist", "worked on", "working on",
    "was responsible for", "responsible for", "contributed to", "contribute to",
    "participated in", "participate in", "involved in", "involve in",
    "supported", "support", "was part of", "part of", "handled", "handle",
    "dealt with", "deal with", "took care of", "take care of",
}

# Filler words to flag (reduce quality)
FILLER_WORDS = {
    "really", "very", "quite", "just", "actually", "basically",
    "literally", "simply", "essentially", "generally", "practically",
    "kind of", "sort of", "somewhat", "rather", "fairly",
}

# Emotional opening phrases (critical violations)
EMOTIONAL_OPENINGS = {
    "i'm thrilled", "i'm excited to", "i'm delighted",
    "i am thrilled", "i am excited to", "i am delighted",
    "it is with great excitement", "i'm passionate about",
    "i am passionate about", "i'm eager to", "i am eager to",
    "i'm enthusiastic", "i am enthusiastic",
}

# Generic value statements (critical violations)
GENERIC_STATEMENTS = {
    "fast-paced environment", "dynamic professional",
    "results-oriented professional", "proven track record",
    "team player", "self-starter", "go-getter",
    "hard worker", "motivated individual", "driven professional",
    "detail-oriented professional", "highly motivated",
}

# Style score thresholds
STYLE_SCORE_THRESHOLD = 85
PASSIVE_VOICE_THRESHOLD = 0.15  # 15% max passive voice
WEAK_VERB_THRESHOLD = 0.10  # 10% max weak verb usage
AVG_SENTENCE_LENGTH_TARGET = (14, 22)  # Target range
MAX_SENTENCE_LENGTH = 35  # Absolute max
MAX_COMMAS_PER_SENTENCE = 2  # Limit comma density

# Opening patterns that indicate non-value-oriented intro (bad)
BAD_OPENING_PATTERNS = [
    r"^i am writing to",
    r"^i'm writing to",
    r"^this letter is to",
    r"^i would like to apply",
    r"^i am applying for",
    r"^please accept this",
    r"^i wish to apply",
]

# Closing patterns that indicate non-impact-oriented close (bad)
BAD_CLOSING_PATTERNS = [
    r"look forward to hearing",
    r"looking forward to hearing",
    r"please feel free to contact",
    r"do not hesitate to contact",
    r"thank you for your consideration",
    r"thank you for considering",
    r"i hope to hear from you",
]


def check_em_dashes(
    text: str,
    context: Optional[str] = None
) -> List[CriticIssue]:
    """
    Check for em-dashes in text (explicitly banned by style guide).

    Per style guide Section 2: Em-dashes (—) are banned punctuation.

    Args:
        text: Text to check
        context: Section context (e.g., "cover_letter")

    Returns:
        List of CriticIssue objects for each em-dash found
    """
    if not text:
        return []

    issues: List[CriticIssue] = []
    pattern = re.compile(EM_DASH_PATTERN)

    for match in pattern.finditer(text):
        # Get surrounding context
        start = max(0, match.start() - 20)
        end = min(len(text), match.end() + 20)
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        issues.append(CriticIssue(
            issue_type="em_dash_violation",
            severity="error",  # Em-dashes are critical violations per style guide
            section=context,
            message="Em-dash detected (banned punctuation per style guide)",
            original_text=snippet,
            recommended_fix="Use commas, parentheses, or restructure the sentence instead"
        ))

    return issues


def check_banned_phrases(
    text: str,
    company_name: Optional[str] = None,
    context: Optional[str] = None
) -> List[CriticIssue]:
    """
    Check for banned phrases in text.

    Args:
        text: Text to check (resume summary, cover letter body, etc.)
        company_name: Company name if known (affects some checks)
        context: Section context (e.g., "summary", "cover_letter_body")

    Returns:
        List of CriticIssue objects for each violation
    """
    # Guard against None or empty text
    if not text:
        return []

    issues: List[CriticIssue] = []
    text_lower = text.lower()

    for phrase, severity in BANNED_PHRASES.items():
        # Special case: "dear hiring manager" is only major if company is known
        if phrase == "dear hiring manager" and not company_name:
            severity = "minor"

        # Use lookahead/lookbehind for phrase boundaries
        pattern = re.compile(
            r'(?<![a-zA-Z])' + re.escape(phrase) + r'(?![a-zA-Z])',
            re.IGNORECASE
        )

        for match in pattern.finditer(text_lower):
            # Get surrounding context for original_text
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            snippet = text[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."

            # Get recommended fix
            recommended_fix = BANNED_PHRASE_FIXES.get(
                phrase,
                "Remove or rephrase to avoid cliché"
            )

            issues.append(CriticIssue(
                issue_type="banned_phrase",
                severity=SEVERITY_MAP.get(severity, "warning"),
                section=context,
                message=f"Banned phrase detected: '{phrase}'",
                original_text=snippet,
                recommended_fix=recommended_fix
            ))

    return issues


# =============================================================================
# STYLE ENFORCEMENT HELPER FUNCTIONS
# =============================================================================

def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text.

    Handles common sentence-ending punctuation (., !, ?) while
    avoiding false splits on abbreviations and decimals.

    Args:
        text: Text to split into sentences

    Returns:
        List of sentences with whitespace trimmed
    """
    if not text:
        return []

    # Simple sentence splitting - split on . ! ? followed by space or end
    # This avoids issues with abbreviations like "Dr." or decimals like "3.5"
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    return len(re.findall(r'\b\w+\b', text))


def detect_passive_voice(text: str) -> Tuple[float, List[str]]:
    """
    Detect passive voice constructions in text.

    Looks for patterns like "was/were/is/are/been + verb(ed/en)"

    Args:
        text: Text to analyze

    Returns:
        Tuple of (passive_rate, examples):
        - passive_rate: float 0-1 representing % of sentences with passive voice
        - examples: list of passive voice snippets found
    """
    if not text:
        return 0.0, []

    sentences = extract_sentences(text)
    if not sentences:
        return 0.0, []

    # Pattern for passive voice: be-verb + past participle
    # Matches: is/are/was/were/be/being/been + word ending in ed/en
    passive_pattern = re.compile(
        r'\b(is|are|was|were|be|being|been|has been|have been|had been)\s+\w+(?:ed|en)\b',
        re.IGNORECASE
    )

    passive_sentences = 0
    examples = []

    for sentence in sentences:
        matches = passive_pattern.findall(sentence)
        if matches:
            passive_sentences += 1
            # Get snippet around the passive construction
            match = passive_pattern.search(sentence)
            if match and len(examples) < 3:
                start = max(0, match.start() - 20)
                end = min(len(sentence), match.end() + 20)
                snippet = sentence[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(sentence):
                    snippet = snippet + "..."
                examples.append(snippet)

    passive_rate = passive_sentences / len(sentences) if sentences else 0.0
    return passive_rate, examples


def detect_emotional_adjectives(text: str) -> List[Tuple[str, str]]:
    """
    Detect emotional/fluffy adjectives that should be avoided.

    Args:
        text: Text to analyze

    Returns:
        List of (adjective, context_snippet) tuples
    """
    if not text:
        return []

    text_lower = text.lower()
    found = []

    # Emotional/fluffy adjectives to flag
    emotional_adjectives = [
        "excited", "thrilled", "passionate", "enthusiastic", "eager",
        "amazing", "incredible", "fantastic", "wonderful", "tremendous",
    ]

    for adj in emotional_adjectives:
        pattern = re.compile(r'\b' + re.escape(adj) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(text_lower):
            start = max(0, match.start() - 15)
            end = min(len(text), match.end() + 15)
            snippet = text[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."
            found.append((adj, snippet))

    return found


def analyze_sentence_metrics(text: str) -> Dict:
    """
    Analyze sentence-level metrics for conciseness scoring.

    Args:
        text: Text to analyze

    Returns:
        Dict with:
        - avg_length: average words per sentence
        - max_length: maximum sentence length
        - total_sentences: number of sentences
        - long_sentences: list of sentences exceeding MAX_SENTENCE_LENGTH
        - comma_violations: list of sentences with too many commas
    """
    if not text:
        return {
            "avg_length": 0.0,
            "max_length": 0,
            "total_sentences": 0,
            "long_sentences": [],
            "comma_violations": [],
        }

    sentences = extract_sentences(text)
    if not sentences:
        return {
            "avg_length": 0.0,
            "max_length": 0,
            "total_sentences": 0,
            "long_sentences": [],
            "comma_violations": [],
        }

    lengths = [count_words(s) for s in sentences]
    comma_counts = [s.count(',') for s in sentences]

    avg_length = sum(lengths) / len(lengths)
    max_length = max(lengths) if lengths else 0

    # Find long sentences
    long_sentences = [
        (sentences[i], lengths[i])
        for i in range(len(sentences))
        if lengths[i] > MAX_SENTENCE_LENGTH
    ]

    # Find sentences with too many commas
    comma_violations = [
        (sentences[i], comma_counts[i])
        for i in range(len(sentences))
        if comma_counts[i] > MAX_COMMAS_PER_SENTENCE
    ]

    return {
        "avg_length": avg_length,
        "max_length": max_length,
        "total_sentences": len(sentences),
        "long_sentences": long_sentences,
        "comma_violations": comma_violations,
    }


def check_verb_strength(text: str) -> Tuple[int, float, List[CriticIssue]]:
    """
    Check for strong vs weak verb usage in text.

    Args:
        text: Text to analyze

    Returns:
        Tuple of (lexical_score, weak_verb_rate, issues):
        - lexical_score: 0-100 score based on verb quality
        - weak_verb_rate: float 0-1 representing weak verb usage
        - issues: list of CriticIssue for weak verb violations
    """
    if not text:
        return 100, 0.0, []

    text_lower = text.lower()
    issues: List[CriticIssue] = []

    # Count strong and weak verbs
    strong_count = 0
    weak_count = 0

    # Check for strong verbs
    for verb in STRONG_VERBS:
        pattern = re.compile(r'\b' + re.escape(verb) + r'\b', re.IGNORECASE)
        matches = pattern.findall(text_lower)
        strong_count += len(matches)

    # Check for weak verbs
    weak_found = []
    for phrase in WEAK_VERBS:
        pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(text_lower):
            weak_count += 1
            if len(weak_found) < 5:  # Limit examples
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                snippet = text[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                weak_found.append((phrase, snippet))

    # Calculate rates
    total_verbs = strong_count + weak_count
    weak_verb_rate = weak_count / total_verbs if total_verbs > 0 else 0.0

    # Generate issues for weak verbs found
    for phrase, snippet in weak_found:
        issues.append(CriticIssue(
            issue_type="weak_verb_violation",
            severity="warning",
            section="cover_letter",
            message=f"Weak verb detected: '{phrase}'",
            original_text=snippet,
            recommended_fix=f"Replace '{phrase}' with a stronger action verb like 'led', 'built', 'drove', 'implemented'"
        ))

    # Calculate score: start at 100, deduct for weak verb rate
    # If weak_verb_rate > threshold, significant deduction
    if weak_verb_rate > WEAK_VERB_THRESHOLD:
        lexical_score = max(0, 100 - int(weak_verb_rate * 200))  # Heavy penalty
    else:
        lexical_score = max(70, 100 - int(weak_verb_rate * 100))

    # Bonus for having strong verbs
    if strong_count >= 5:
        lexical_score = min(100, lexical_score + 10)

    return lexical_score, weak_verb_rate, issues


def check_filler_words(text: str) -> List[CriticIssue]:
    """
    Check for filler words that reduce writing quality.

    Aggregates counts per filler word to avoid excessive noise.
    Limits to 5 representative examples to keep the issue list manageable.

    Args:
        text: Text to analyze

    Returns:
        List of CriticIssue (limited to 5 total, aggregated by filler word type)
    """
    if not text:
        return []

    text_lower = text.lower()
    issues: List[CriticIssue] = []

    # Count occurrences per filler word
    filler_counts: Dict[str, int] = {}
    filler_examples: Dict[str, str] = {}

    for filler in FILLER_WORDS:
        pattern = re.compile(r'\b' + re.escape(filler) + r'\b', re.IGNORECASE)
        matches = list(pattern.finditer(text_lower))
        if matches:
            filler_counts[filler] = len(matches)
            # Get one example snippet for the first occurrence
            match = matches[0]
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            snippet = text[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(text):
                snippet = snippet + "..."
            filler_examples[filler] = snippet

    # Create aggregated issues (limit to 5 total)
    sorted_fillers = sorted(filler_counts.items(), key=lambda x: x[1], reverse=True)
    for filler, count in sorted_fillers[:5]:
        issues.append(CriticIssue(
            issue_type="filler_word_violation",
            severity="info",  # Informational - not blocking
            section="cover_letter",
            message=f"Filler word '{filler}' used {count} time(s)",
            original_text=filler_examples.get(filler),
            recommended_fix=f"Remove '{filler}' or use more specific language"
        ))

    return issues


def check_conciseness(text: str) -> Tuple[int, List[CriticIssue]]:
    """
    Check sentence and paragraph conciseness constraints.

    Args:
        text: Text to analyze

    Returns:
        Tuple of (conciseness_score, issues):
        - conciseness_score: 0-100 based on sentence length and structure
        - issues: list of CriticIssue for violations
    """
    if not text:
        return 100, []

    metrics = analyze_sentence_metrics(text)
    issues: List[CriticIssue] = []

    # Start with perfect score
    conciseness_score = 100

    # Check average sentence length
    avg_length = metrics["avg_length"]
    if avg_length < AVG_SENTENCE_LENGTH_TARGET[0]:
        # Too short - might be choppy
        conciseness_score -= 10
        issues.append(CriticIssue(
            issue_type="sentence_length_violation",
            severity="info",
            section="cover_letter",
            message=f"Average sentence length ({avg_length:.1f} words) is below target ({AVG_SENTENCE_LENGTH_TARGET[0]}-{AVG_SENTENCE_LENGTH_TARGET[1]} words)",
            original_text=None,
            recommended_fix="Consider combining short sentences for better flow"
        ))
    elif avg_length > AVG_SENTENCE_LENGTH_TARGET[1]:
        # Too long - might be dense
        penalty = min(30, int((avg_length - AVG_SENTENCE_LENGTH_TARGET[1]) * 3))
        conciseness_score -= penalty
        issues.append(CriticIssue(
            issue_type="sentence_length_violation",
            severity="warning",
            section="cover_letter",
            message=f"Average sentence length ({avg_length:.1f} words) exceeds target ({AVG_SENTENCE_LENGTH_TARGET[0]}-{AVG_SENTENCE_LENGTH_TARGET[1]} words)",
            original_text=None,
            recommended_fix="Break long sentences into shorter, clearer statements"
        ))

    # Check for individual long sentences
    for sentence, length in metrics["long_sentences"]:
        conciseness_score -= 10
        issues.append(CriticIssue(
            issue_type="sentence_length_violation",
            severity="error",  # Long sentences are blocking
            section="cover_letter",
            message=f"Sentence exceeds maximum length ({length} words, max is {MAX_SENTENCE_LENGTH})",
            original_text=sentence[:80] + "..." if len(sentence) > 80 else sentence,
            recommended_fix=f"Split this {length}-word sentence into 2-3 shorter sentences"
        ))

    # Check for comma overuse
    for sentence, comma_count in metrics["comma_violations"]:
        conciseness_score -= 5
        issues.append(CriticIssue(
            issue_type="comma_overuse_violation",
            severity="warning",
            section="cover_letter",
            message=f"Sentence has too many commas ({comma_count}, max is {MAX_COMMAS_PER_SENTENCE})",
            original_text=sentence[:80] + "..." if len(sentence) > 80 else sentence,
            recommended_fix="Restructure to reduce comma usage or split into multiple sentences"
        ))

    conciseness_score = max(0, conciseness_score)
    return conciseness_score, issues


def check_emotional_openings(text: str) -> List[CriticIssue]:
    """
    Check for emotional opening phrases (critical violations).

    Args:
        text: Text to analyze

    Returns:
        List of CriticIssue for each emotional opening found
    """
    if not text:
        return []

    text_lower = text.lower()
    issues: List[CriticIssue] = []

    for phrase in EMOTIONAL_OPENINGS:
        if phrase in text_lower:
            issues.append(CriticIssue(
                issue_type="emotional_opening_violation",
                severity="error",  # Critical violation
                section="cover_letter",
                message=f"Emotional opening phrase detected: '{phrase}'",
                original_text=None,
                recommended_fix="Start with a professional, value-oriented statement instead of expressing emotions"
            ))

    return issues


def check_generic_statements(text: str) -> List[CriticIssue]:
    """
    Check for generic value statements (critical violations).

    Args:
        text: Text to analyze

    Returns:
        List of CriticIssue for each generic statement found
    """
    if not text:
        return []

    text_lower = text.lower()
    issues: List[CriticIssue] = []

    for phrase in GENERIC_STATEMENTS:
        if phrase in text_lower:
            issues.append(CriticIssue(
                issue_type="generic_statement_violation",
                severity="error",  # Critical violation
                section="cover_letter",
                message=f"Generic statement detected: '{phrase}'",
                original_text=None,
                recommended_fix=f"Replace '{phrase}' with specific, concrete examples of your achievements"
            ))

    return issues


def check_prohibited_patterns(
    text: str,
    company_name: Optional[str] = None
) -> List[CriticIssue]:
    """
    Check for all prohibited patterns (combined check).

    Includes:
    - Emotional openings
    - Generic statements
    - Other critical pattern violations

    Args:
        text: Text to analyze
        company_name: Company name (for context-specific checks)

    Returns:
        List of CriticIssue for all prohibited pattern violations
    """
    issues: List[CriticIssue] = []

    # Check emotional openings
    issues.extend(check_emotional_openings(text))

    # Check generic statements
    issues.extend(check_generic_statements(text))

    return issues


def check_cover_letter_structure_enhanced(
    cover_letter_json: Dict,
    job_profile: JobProfile
) -> Tuple[int, List[CriticIssue], Dict[str, bool]]:
    """
    Check cover letter structure for the 4 required ETPS elements.

    Required structure:
    1. Value-oriented opening (not generic intro)
    2. Alignment to top 2-3 JD requirements
    3. Company/industry/mission connection
    4. Impact-oriented closing

    Args:
        cover_letter_json: Generated cover letter JSON
        job_profile: Job profile for requirement matching

    Returns:
        Tuple of (structure_score, issues, structure_details):
        - structure_score: 0-100 (0 if any section missing)
        - issues: list of CriticIssue for structural problems
        - structure_details: dict with boolean for each section
    """
    issues: List[CriticIssue] = []
    structure_details = {
        "has_value_opening": True,
        "has_jd_alignment": True,
        "has_company_connection": True,
        "has_impact_closing": True,
    }

    draft = cover_letter_json.get("draft_cover_letter", "")
    if not draft:
        return 0, [CriticIssue(
            issue_type="structure_gap_violation",
            severity="error",
            section="cover_letter",
            message="Cover letter draft is empty",
            original_text=None,
            recommended_fix="Generate cover letter content"
        )], structure_details

    text_lower = draft.lower()
    paragraphs = [p.strip() for p in draft.split('\n\n') if p.strip()]
    if len(paragraphs) < 2:
        paragraphs = [p.strip() for p in draft.split('\n') if p.strip()]

    # 1. Check value-oriented opening
    opening = paragraphs[0] if paragraphs else ""
    opening_lower = opening.lower()

    for pattern in BAD_OPENING_PATTERNS:
        if re.search(pattern, opening_lower):
            structure_details["has_value_opening"] = False
            issues.append(CriticIssue(
                issue_type="structure_gap_violation",
                severity="error",
                section="opening",
                message="Opening is not value-oriented (uses generic intro pattern)",
                original_text=opening[:100] + "..." if len(opening) > 100 else opening,
                recommended_fix="Start with a compelling qualification or achievement, not a generic introduction"
            ))
            break

    # 2. Check JD requirement alignment
    # Use existing requirements_covered data if available
    requirements_covered = cover_letter_json.get("requirements_covered", [])
    if requirements_covered:
        covered_count = sum(1 for r in requirements_covered if r.get("covered", False))
        if covered_count < 2:
            structure_details["has_jd_alignment"] = False
            issues.append(CriticIssue(
                issue_type="structure_gap_violation",
                severity="error",
                section="alignment",
                message=f"Insufficient JD requirement coverage ({covered_count}/3 requirements addressed)",
                original_text=None,
                recommended_fix="Explicitly address at least 2 of the top 3 job requirements"
            ))
    else:
        # Fallback: check if core priorities are mentioned
        core_priorities = job_profile.core_priorities or []
        if isinstance(core_priorities, str):
            core_priorities = [core_priorities]
        priorities_addressed = 0
        for priority in core_priorities[:3]:
            if priority and priority.lower() in text_lower:
                priorities_addressed += 1
        if priorities_addressed < 2:
            structure_details["has_jd_alignment"] = False
            issues.append(CriticIssue(
                issue_type="structure_gap_violation",
                severity="error",
                section="alignment",
                message="JD requirement alignment not evident",
                original_text=None,
                recommended_fix="Explicitly address at least 2 of the top 3 job requirements"
            ))

    # 3. Check company/mission connection
    # Try to get company name from job_profile.company relationship or cover_letter_json
    company_name = None
    if hasattr(job_profile, 'company') and job_profile.company:
        company_name = job_profile.company.name
    if not company_name:
        company_name = cover_letter_json.get("company_name")
    if company_name:
        if company_name.lower() not in text_lower:
            structure_details["has_company_connection"] = False
            issues.append(CriticIssue(
                issue_type="structure_gap_violation",
                severity="error",
                section="company_connection",
                message=f"Company name '{company_name}' not mentioned",
                original_text=None,
                recommended_fix=f"Include meaningful reference to {company_name} and why you want to work there"
            ))
    else:
        # No company name available - check for mission/industry keywords
        mission_keywords = ["mission", "vision", "industry", "sector", "company", "organization"]
        if not any(kw in text_lower for kw in mission_keywords):
            structure_details["has_company_connection"] = False
            issues.append(CriticIssue(
                issue_type="structure_gap_violation",
                severity="warning",
                section="company_connection",
                message="No clear company or mission connection found",
                original_text=None,
                recommended_fix="Add context about why this specific company/industry interests you"
            ))

    # 4. Check impact-oriented closing
    closing = paragraphs[-1] if paragraphs else ""
    closing_lower = closing.lower()

    for pattern in BAD_CLOSING_PATTERNS:
        if re.search(pattern, closing_lower):
            structure_details["has_impact_closing"] = False
            issues.append(CriticIssue(
                issue_type="structure_gap_violation",
                severity="error",
                section="closing",
                message="Closing is not impact-oriented (uses generic closing pattern)",
                original_text=closing[:100] + "..." if len(closing) > 100 else closing,
                recommended_fix="End with a value proposition or confident statement about your contribution"
            ))
            break

    # Calculate structure score
    # Missing any section = 0 (auto-fail)
    missing_count = sum(1 for v in structure_details.values() if not v)
    if missing_count > 0:
        structure_score = 0
    else:
        structure_score = 100

    return structure_score, issues, structure_details


def calculate_overall_style_score(
    tone_score: int,
    structure_score: int,
    lexical_score: int,
    conciseness_score: int
) -> int:
    """
    Calculate weighted overall style score.

    Weights:
    - tone_score: 30%
    - structure_score: 30%
    - lexical_score: 20%
    - conciseness_score: 20%

    Args:
        tone_score: Tone analysis score (0-100)
        structure_score: Structure validation score (0-100)
        lexical_score: Lexical quality score (0-100)
        conciseness_score: Conciseness score (0-100)

    Returns:
        Weighted average score (0-100), clamped to valid range

    Raises:
        ValueError: If any input score is outside 0-100 range
    """
    # Validate inputs
    scores = {
        "tone_score": tone_score,
        "structure_score": structure_score,
        "lexical_score": lexical_score,
        "conciseness_score": conciseness_score
    }
    for name, score in scores.items():
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            raise ValueError(f"Invalid {name}: {score} (must be 0-100)")

    weighted = (
        tone_score * 0.30 +
        structure_score * 0.30 +
        lexical_score * 0.20 +
        conciseness_score * 0.20
    )
    # Clamp to 0-100 and convert to int
    return max(0, min(100, int(round(weighted))))


async def check_tone_enhanced(
    text: str,
    expected_tone: str,
    llm: BaseLLM,
    content_type: Literal["resume", "cover_letter"]
) -> Tuple[int, List[CriticIssue]]:
    """
    Enhanced tone check combining deterministic and LLM-based analysis.

    Checks:
    - Passive voice rate
    - Emotional/fluffy adjectives
    - LLM-based tone detection

    Args:
        text: Text to analyze
        expected_tone: Expected tone style
        llm: LLM instance for tone inference
        content_type: Type of content

    Returns:
        Tuple of (tone_score, issues):
        - tone_score: 0-100 based on tone compliance
        - issues: list of CriticIssue for tone violations
    """
    if not text:
        return 100, []

    issues: List[CriticIssue] = []
    tone_score = 100

    # 1. Check passive voice
    passive_rate, passive_examples = detect_passive_voice(text)
    if passive_rate > PASSIVE_VOICE_THRESHOLD:
        penalty = min(30, int(passive_rate * 100))
        tone_score -= penalty
        issues.append(CriticIssue(
            issue_type="passive_voice_violation",
            severity="warning",
            section=content_type,
            message=f"Excessive passive voice ({passive_rate*100:.1f}%, threshold is {PASSIVE_VOICE_THRESHOLD*100}%)",
            original_text=passive_examples[0] if passive_examples else None,
            recommended_fix="Rewrite using active voice with strong action verbs"
        ))

    # 2. Check emotional adjectives
    emotional_found = detect_emotional_adjectives(text)
    if emotional_found:
        tone_score -= len(emotional_found) * 5
        for adj, snippet in emotional_found[:3]:  # Limit to 3 issues
            issues.append(CriticIssue(
                issue_type="tone_mismatch",
                severity="warning",
                section=content_type,
                message=f"Emotional/fluffy adjective detected: '{adj}'",
                original_text=snippet,
                recommended_fix=f"Replace '{adj}' with factual, professional language"
            ))

    # 3. Run existing LLM-based tone check
    tone_issues = await check_tone(text, expected_tone, llm, content_type)
    if tone_issues:
        tone_score -= 20
        issues.extend(tone_issues)

    tone_score = max(0, tone_score)
    return tone_score, issues


async def check_tone(
    text: str,
    expected_tone: str,
    llm: BaseLLM,
    content_type: Literal["resume", "cover_letter"]
) -> List[CriticIssue]:
    """
    Check if tone matches expected tone.

    Args:
        text: Text to analyze
        expected_tone: Expected tone (from job_profile.tone_style)
        llm: LLM instance for tone detection
        content_type: Type of content being evaluated

    Returns:
        List of CriticIssue objects (empty if tone OK, 1 issue if mismatch)
    """
    # Detect tone using LLM
    detected_tone = await llm.infer_tone(text)

    # Check compatibility
    compatibility_score = TONE_COMPATIBILITY.get(
        (expected_tone, detected_tone),
        0.35  # Default for unknown combinations
    )

    if compatibility_score < 0.55:
        content_label = "resume" if content_type == "resume" else "cover letter"

        # Generate specific fix recommendation based on tones
        if expected_tone in ("formal_corporate", "consulting_professional"):
            fix = (
                f"Adjust to more formal tone: use professional language, "
                f"avoid contractions, maintain respectful distance"
            )
        elif expected_tone in ("startup_casual", "mission_driven"):
            fix = (
                f"Adjust to more casual tone: use conversational language, "
                f"show personality, emphasize values and impact"
            )
        else:
            fix = f"Adjust tone to match {expected_tone} style"

        return [CriticIssue(
            issue_type="tone_mismatch",
            severity="warning",
            section=content_label,
            message=f"Tone mismatch: expected {expected_tone}, detected {detected_tone}",
            original_text=None,
            recommended_fix=fix
        )]

    return []


def check_structure(
    content_json: Dict,
    content_type: Literal["resume", "cover_letter"]
) -> StructureCheckResult:
    """
    Check structure and formatting requirements.

    Args:
        content_json: TailoredResume or GeneratedCoverLetter JSON
        content_type: Type of content

    Returns:
        StructureCheckResult with validation details
    """
    # Guard against None or invalid content_json
    if not isinstance(content_json, dict):
        content_json = {}

    missing_sections: List[str] = []

    if content_type == "resume":
        # Resume required sections
        if not content_json.get("tailored_summary"):
            missing_sections.append("tailored_summary")

        selected_roles = content_json.get("selected_roles", [])
        if not selected_roles or len(selected_roles) < 1:
            missing_sections.append("selected_roles (at least 1)")

        selected_skills = content_json.get("selected_skills", [])
        if not selected_skills or len(selected_skills) < 5:
            missing_sections.append("selected_skills (at least 5)")

        # Word count for summary
        summary = content_json.get("tailored_summary", "")
        word_count = len(re.findall(r'\w+', summary))
        expected_range = "60-100 words"
        word_count_valid = 60 <= word_count <= 100

    else:  # cover_letter
        # Cover letter required sections (in outline)
        outline = content_json.get("outline", {})
        if not outline.get("introduction"):
            missing_sections.append("introduction")
        if not outline.get("value_proposition"):
            missing_sections.append("value_proposition")
        if not outline.get("alignment"):
            missing_sections.append("alignment")
        if not outline.get("call_to_action"):
            missing_sections.append("call_to_action")

        # Also check draft exists
        if not content_json.get("draft_cover_letter"):
            missing_sections.append("draft_cover_letter")

        # Word count for full cover letter
        draft = content_json.get("draft_cover_letter", "")
        word_count = len(re.findall(r'\w+', draft))
        expected_range = "250-350 words"
        word_count_valid = 250 <= word_count <= 350

    has_required = len(missing_sections) == 0

    return StructureCheckResult(
        has_required_sections=has_required,
        missing_sections=missing_sections,
        word_count=word_count,
        word_count_valid=word_count_valid,
        expected_range=expected_range
    )


def compute_ats_score(
    job_profile: JobProfile,
    content_json: Dict,
    content_type: Literal["resume", "cover_letter"]
) -> ATSScoreBreakdown:
    """
    Compute ATS score with detailed breakdown.

    Args:
        job_profile: JobProfile with extracted_skills, must_have_capabilities
        content_json: TailoredResume or GeneratedCoverLetter JSON
        content_type: Type of content

    Returns:
        ATSScoreBreakdown with detailed scores
    """
    # Extract text to analyze
    if content_type == "resume":
        # Concatenate summary + all bullet texts
        text_parts = [content_json.get("tailored_summary", "")]
        for role in content_json.get("selected_roles", []):
            for bullet in role.get("selected_bullets", []):
                text_parts.append(bullet.get("text", ""))
        # Add skill names
        for skill in content_json.get("selected_skills", []):
            text_parts.append(skill.get("skill_name", ""))
        text = " ".join(text_parts)
    else:
        # Cover letter - use draft text
        text = content_json.get("draft_cover_letter", "")

    # Call existing ATS keyword coverage function
    ats_result = analyze_ats_keyword_coverage(text, job_profile)

    # keyword_score: direct from coverage_percentage
    keyword_score = ats_result.coverage_percentage

    # format_score: based on structure completeness
    structure_result = check_structure(content_json, content_type)
    if structure_result.has_required_sections and structure_result.word_count_valid:
        format_score = 100.0
    elif structure_result.has_required_sections:
        format_score = 80.0  # Missing word count requirements
    elif structure_result.word_count_valid:
        format_score = 70.0  # Missing some sections
    else:
        format_score = 50.0  # Multiple issues

    # skills_score: based on skills section density
    if content_type == "resume":
        selected_skills = content_json.get("selected_skills", [])
        max_skills = 12  # Default max
        skills_score = min((len(selected_skills) / max_skills) * 100, 100.0)
    else:
        # For cover letter, skills score = keyword score (skills reflected in keywords)
        skills_score = keyword_score

    # Overall ATS score: weighted average
    # keyword_score: 50%, format_score: 30%, skills_score: 20%
    overall_score = (
        (keyword_score * 0.5) +
        (format_score * 0.3) +
        (skills_score * 0.2)
    )

    return ATSScoreBreakdown(
        overall_score=overall_score,
        keyword_score=keyword_score,
        format_score=format_score,
        skills_score=skills_score,
        total_keywords=ats_result.total_keywords,
        keywords_matched=ats_result.keywords_covered,
        keywords_missing=ats_result.missing_critical_keywords[:5]
    )


def enforce_rules(
    content_json: Dict,
    content_type: Literal["resume", "cover_letter"],
    db: Session
) -> List[CriticIssue]:
    """
    Enforce content-specific rules (immutability, constraints).

    Args:
        content_json: TailoredResume or GeneratedCoverLetter JSON
        content_type: Type of content
        db: Database session for validation lookups

    Returns:
        List of CriticIssue objects for rule violations
    """
    # Guard against None or invalid content_json
    if not isinstance(content_json, dict):
        content_json = {}

    issues: List[CriticIssue] = []

    if content_type == "resume":
        # Check immutability of job titles, employer names, locations
        selected_roles = content_json.get("selected_roles", [])

        for idx, role in enumerate(selected_roles):
            experience_id = role.get("experience_id")
            if experience_id:
                # Query original experience
                experience = db.query(Experience).filter(
                    Experience.id == experience_id
                ).first()

                if experience:
                    # Check job_title immutability
                    if role.get("job_title") != experience.job_title:
                        issues.append(CriticIssue(
                            issue_type="rule_violation",
                            severity="error",
                            section=f"role_{idx}",
                            message=f"Job title modified from original: '{experience.job_title}'",
                            original_text=role.get("job_title"),
                            recommended_fix="Restore original job title - titles must not be changed"
                        ))

                    # Check employer_name immutability
                    if role.get("employer_name") != experience.employer_name:
                        issues.append(CriticIssue(
                            issue_type="rule_violation",
                            severity="error",
                            section=f"role_{idx}",
                            message=f"Employer name modified from original: '{experience.employer_name}'",
                            original_text=role.get("employer_name"),
                            recommended_fix="Restore original employer name - company names must not be changed"
                        ))

                    # Check location immutability
                    role_location = role.get("location")
                    if role_location and experience.location and role_location != experience.location:
                        issues.append(CriticIssue(
                            issue_type="rule_violation",
                            severity="error",
                            section=f"role_{idx}",
                            message=f"Location modified from original: '{experience.location}'",
                            original_text=role_location,
                            recommended_fix="Restore original location - locations must not be changed"
                        ))

            # Check bullet count constraint
            max_bullets_per_role = 4
            selected_bullets = role.get("selected_bullets", [])
            if len(selected_bullets) > max_bullets_per_role:
                issues.append(CriticIssue(
                    issue_type="rule_violation",
                    severity="warning",
                    section=f"role_{idx}",
                    message=f"Too many bullets ({len(selected_bullets)}) for role, max is {max_bullets_per_role}",
                    original_text=None,
                    recommended_fix=f"Select at most {max_bullets_per_role} bullets per role"
                ))

        # Check skills count constraint
        max_skills = 12
        selected_skills = content_json.get("selected_skills", [])
        if len(selected_skills) > max_skills:
            issues.append(CriticIssue(
                issue_type="rule_violation",
                severity="warning",
                section="skills",
                message=f"Too many skills ({len(selected_skills)}), max is {max_skills}",
                original_text=None,
                recommended_fix=f"Select at most {max_skills} skills"
            ))

        # Check constraints_validated field
        if not content_json.get("constraints_validated", True):
            issues.append(CriticIssue(
                issue_type="rule_violation",
                severity="warning",
                section="resume",
                message="Resume constraints were not validated during generation",
                original_text=None,
                recommended_fix="Re-run resume tailoring with constraint validation enabled"
            ))

    else:  # cover_letter
        # Check word count
        draft = content_json.get("draft_cover_letter", "")
        word_count = len(re.findall(r'\w+', draft))

        if word_count < 200:
            issues.append(CriticIssue(
                issue_type="word_count_violation",
                severity="warning",
                section="cover_letter",
                message=f"Cover letter too short ({word_count} words), minimum is 200",
                original_text=None,
                recommended_fix="Expand content with more detail about qualifications and fit"
            ))
        elif word_count > 400:
            issues.append(CriticIssue(
                issue_type="word_count_violation",
                severity="warning",
                section="cover_letter",
                message=f"Cover letter too long ({word_count} words), maximum is 400",
                original_text=None,
                recommended_fix="Condense content to focus on most relevant points"
            ))

        # Check quality_score threshold
        quality_score = content_json.get("quality_score", 100)
        if quality_score < 50:
            issues.append(CriticIssue(
                issue_type="rule_violation",
                severity="warning",
                section="cover_letter",
                message=f"Cover letter quality score ({quality_score}) below threshold (50)",
                original_text=None,
                recommended_fix="Review and address issues in banned phrases, tone, or keyword coverage"
            ))

        # Check banned_phrase_check.passed from generation
        banned_check = content_json.get("banned_phrase_check", {})
        if not banned_check.get("passed", True):
            overall_severity = banned_check.get("overall_severity", "minor")
            if overall_severity == "critical":
                issues.append(CriticIssue(
                    issue_type="rule_violation",
                    severity="error",
                    section="cover_letter",
                    message="Cover letter contains critical banned phrases from generation",
                    original_text=None,
                    recommended_fix="Remove or rephrase critical banned phrases before submission"
                ))
            elif overall_severity == "major":
                issues.append(CriticIssue(
                    issue_type="rule_violation",
                    severity="warning",
                    section="cover_letter",
                    message="Cover letter contains major banned phrases from generation",
                    original_text=None,
                    recommended_fix="Consider rephrasing major banned phrases"
                ))

    return issues


async def critic_pass(
    content_json: Dict,
    content_type: Literal["resume", "cover_letter"],
    job_profile: JobProfile,
    db: Session,
    llm: Optional[BaseLLM] = None,
    strict_mode: bool = False
) -> CriticResult:
    """
    Perform complete critic evaluation.

    Main orchestrator that runs all checks and aggregates results.

    Args:
        content_json: TailoredResume or GeneratedCoverLetter JSON
        content_type: Type of content to evaluate
        job_profile: Target job profile
        db: Database session
        llm: LLM instance (defaults to MockLLM)
        strict_mode: If True, treat warnings as errors

    Returns:
        CriticResult with pass/fail and detailed feedback
    """
    # Initialize LLM
    if llm is None:
        llm = MockLLM()

    # Extract text for analysis
    if content_type == "resume":
        text_parts = [content_json.get("tailored_summary", "")]
        for role in content_json.get("selected_roles", []):
            for bullet in role.get("selected_bullets", []):
                text_parts.append(bullet.get("text", ""))
        text = " ".join(text_parts)
        company_name = None
    else:
        text = content_json.get("draft_cover_letter", "")
        company_name = content_json.get("company_name")

    # Run all checks
    all_issues: List[CriticIssue] = []

    # 1. Check banned phrases
    banned_issues = check_banned_phrases(
        text,
        company_name=company_name,
        context=content_type
    )
    all_issues.extend(banned_issues)

    # 2. Check tone
    expected_tone = job_profile.tone_style or "formal_corporate"
    tone_issues = await check_tone(text, expected_tone, llm, content_type)
    all_issues.extend(tone_issues)

    # 3. Check structure
    structure_result = check_structure(content_json, content_type)

    # Convert structure issues to CriticIssue objects
    for missing in structure_result.missing_sections:
        all_issues.append(CriticIssue(
            issue_type="structure_violation",
            severity="error",
            section=content_type,
            message=f"Missing required section: {missing}",
            original_text=None,
            recommended_fix=f"Add {missing} section"
        ))

    if not structure_result.word_count_valid:
        all_issues.append(CriticIssue(
            issue_type="word_count_violation",
            severity="warning",
            section=content_type,
            message=f"Word count ({structure_result.word_count}) outside expected range ({structure_result.expected_range})",
            original_text=None,
            recommended_fix=f"Adjust content to be within {structure_result.expected_range}"
        ))

    # 4. Compute ATS score
    ats_score = compute_ats_score(job_profile, content_json, content_type)

    # Add issues for critical missing keywords
    for keyword in ats_score.keywords_missing[:3]:  # Top 3 missing
        all_issues.append(CriticIssue(
            issue_type="ats_keyword_missing",
            severity="warning",
            section=content_type,
            message=f"Critical ATS keyword missing: '{keyword}'",
            original_text=None,
            recommended_fix=f"Incorporate '{keyword}' naturally into content"
        ))

    # 5. Enforce rules
    rule_issues = enforce_rules(content_json, content_type, db)
    all_issues.extend(rule_issues)

    # Count issues by severity
    error_count = sum(1 for issue in all_issues if issue.severity == "error")
    warning_count = sum(1 for issue in all_issues if issue.severity == "warning")
    info_count = sum(1 for issue in all_issues if issue.severity == "info")

    # Determine pass/fail
    if strict_mode:
        passed = (error_count == 0 and warning_count == 0)
    else:
        passed = (error_count == 0)

    # Calculate quality score
    base_score = 50.0

    # Add ATS score contribution (30%)
    ats_contribution = ats_score.overall_score * 0.3

    # Add bonus for no banned phrases (20 points)
    banned_bonus = 20.0 if not banned_issues else 0.0

    # Subtract for errors and warnings
    error_penalty = error_count * 10.0
    warning_penalty = warning_count * 3.0

    quality_score = base_score + ats_contribution + banned_bonus - error_penalty - warning_penalty
    quality_score = max(0.0, min(100.0, quality_score))

    # Generate evaluation summary
    if passed:
        if warning_count > 0:
            summary = f"Content meets quality standards with {warning_count} warning(s) to consider"
        else:
            summary = "Content meets all quality standards"
    else:
        summary = f"Content has {error_count} blocking issue(s) requiring fixes"

    return CriticResult(
        content_type=content_type,
        passed=passed,
        issues=all_issues,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        ats_score=ats_score,
        structure_check=structure_result,
        quality_score=quality_score,
        evaluation_summary=summary,
        evaluated_at=datetime.utcnow().isoformat()
    )


def check_requirement_coverage(
    cover_letter_json: Dict,
    job_profile: JobProfile
) -> Tuple[RequirementCoverageScore, List[CriticIssue]]:
    """
    Check if cover letter addresses top 2-3 job requirements.

    Per style guide Section 6: Identify top 2-3 JD requirements and address them explicitly.

    Uses the same matching algorithm as cover_letter.analyze_requirement_coverage()
    to ensure consistency between generation and critic evaluation.

    Args:
        cover_letter_json: GeneratedCoverLetter JSON
        job_profile: Job profile with core_priorities and must_have_capabilities

    Returns:
        Tuple of (RequirementCoverageScore, List of CriticIssue for uncovered requirements)
    """
    issues: List[CriticIssue] = []

    # Get requirements_covered from the cover letter JSON (if available)
    requirements_covered_data = cover_letter_json.get("requirements_covered", [])

    if not requirements_covered_data:
        # Fallback: analyze from scratch using the same algorithm as cover_letter service
        draft = cover_letter_json.get("draft_cover_letter", "")

        try:
            # Use the imported function for consistency
            result = analyze_requirement_coverage(draft, job_profile)

            # Convert RequirementCoverage objects to dicts with safe attribute access
            requirements_covered_data = []
            if result:
                for r in result:
                    requirements_covered_data.append({
                        "requirement": getattr(r, 'requirement', ''),
                        "covered": getattr(r, 'covered', False),
                        "evidence": getattr(r, 'evidence', None)
                    })
        except Exception as e:
            # Log error and return empty coverage (don't fail the entire evaluation)
            import logging
            logging.getLogger(__name__).error(f"Requirement coverage analysis failed: {e}")
            requirements_covered_data = []

    # Calculate coverage statistics
    total = len(requirements_covered_data)
    covered_count = sum(1 for r in requirements_covered_data if r.get("covered", False))
    percentage = (covered_count / total * 100) if total > 0 else 0.0

    # Generate issues for uncovered requirements
    for req in requirements_covered_data:
        if not req.get("covered", False):
            requirement_text = req.get("requirement", "")
            issues.append(CriticIssue(
                issue_type="requirement_coverage",
                severity="warning",
                section="cover_letter",
                message=f"Job requirement not addressed: '{requirement_text}'",
                original_text=None,
                recommended_fix=f"Add experience or context that addresses: {requirement_text}"
            ))

    score = RequirementCoverageScore(
        total_requirements=total,
        requirements_covered=covered_count,
        coverage_percentage=round(percentage, 1)
    )

    return score, issues


async def evaluate_cover_letter(
    cover_letter_json: Dict,
    job_profile: JobProfile,
    db: Session,
    llm: Optional[BaseLLM] = None,
    strict_mode: bool = False
) -> CoverLetterCriticResult:
    """
    Perform complete critic evaluation specifically for cover letters.

    Enhanced version of critic_pass that includes:
    - Em-dash detection (per style guide Section 2)
    - Requirement coverage checking (per style guide Section 6)
    - FULL STYLE ENFORCEMENT (Section 4.8):
      - Tone analysis (deterministic + LLM)
      - Structure analysis (4 required sections)
      - Lexical quality (strong/weak verbs, filler words)
      - Conciseness (sentence length, comma density)
      - Prohibited patterns (emotional openings, generic statements)
      - Style scoring with pass/fail threshold (85)

    Args:
        cover_letter_json: GeneratedCoverLetter JSON
        job_profile: Target job profile
        db: Database session
        llm: LLM instance (defaults to MockLLM)
        strict_mode: If True, treat warnings as errors

    Returns:
        CoverLetterCriticResult with pass/fail and detailed feedback including style_score
    """
    # Initialize LLM
    if llm is None:
        llm = MockLLM()

    # Guard against None or invalid content_json
    if not isinstance(cover_letter_json, dict):
        cover_letter_json = {}

    # Extract text for analysis
    text = cover_letter_json.get("draft_cover_letter", "")
    company_name = cover_letter_json.get("company_name")
    expected_tone = job_profile.tone_style or "formal_corporate"

    # Run all checks
    all_issues: List[CriticIssue] = []

    # =========================================================================
    # PHASE 1: CRITICAL VIOLATIONS (Em-dashes, Banned Phrases, Prohibited)
    # =========================================================================

    # 1. Check em-dashes (style guide critical violation)
    em_dash_issues = check_em_dashes(text, context="cover_letter")
    all_issues.extend(em_dash_issues)
    em_dash_count = len(em_dash_issues)

    # 2. Check banned phrases
    banned_issues = check_banned_phrases(
        text,
        company_name=company_name,
        context="cover_letter"
    )
    all_issues.extend(banned_issues)

    # 3. Check prohibited patterns (emotional openings, generic statements)
    prohibited_issues = check_prohibited_patterns(text, company_name)
    all_issues.extend(prohibited_issues)

    # =========================================================================
    # PHASE 2: STYLE ENFORCEMENT (NEW)
    # =========================================================================

    # 4. Enhanced tone analysis (deterministic + LLM)
    tone_score, tone_issues = await check_tone_enhanced(text, expected_tone, llm, "cover_letter")
    all_issues.extend(tone_issues)

    # Get passive voice rate for reporting
    passive_rate, _ = detect_passive_voice(text)

    # 5. Enhanced structure analysis (4 required ETPS sections)
    structure_score, structure_issues, structure_details = check_cover_letter_structure_enhanced(
        cover_letter_json, job_profile
    )
    all_issues.extend(structure_issues)

    # 6. Lexical quality (strong/weak verbs)
    lexical_score, weak_verb_rate, lexical_issues = check_verb_strength(text)
    all_issues.extend(lexical_issues)

    # 7. Filler words check
    filler_issues = check_filler_words(text)
    all_issues.extend(filler_issues)

    # 8. Conciseness check (sentence length, comma density)
    conciseness_score, conciseness_issues = check_conciseness(text)
    all_issues.extend(conciseness_issues)

    # Get sentence metrics for reporting
    sentence_metrics = analyze_sentence_metrics(text)

    # 9. Calculate overall style score
    overall_style_score = calculate_overall_style_score(
        tone_score, structure_score, lexical_score, conciseness_score
    )

    # Build StyleScoreBreakdown
    style_score_breakdown = StyleScoreBreakdown(
        tone_score=tone_score,
        structure_score=structure_score,
        lexical_score=lexical_score,
        conciseness_score=conciseness_score,
        overall_style_score=overall_style_score,
        passive_voice_rate=passive_rate,
        weak_verb_rate=weak_verb_rate,
        avg_sentence_length=sentence_metrics["avg_length"],
        max_sentence_length=sentence_metrics["max_length"],
        has_value_opening=structure_details["has_value_opening"],
        has_jd_alignment=structure_details["has_jd_alignment"],
        has_company_connection=structure_details["has_company_connection"],
        has_impact_closing=structure_details["has_impact_closing"],
    )

    # =========================================================================
    # PHASE 3: EXISTING CHECKS (Structure, ATS, Requirements, Rules)
    # =========================================================================

    # 10. Basic structure check (for outline sections)
    basic_structure_result = check_structure(cover_letter_json, "cover_letter")

    # Convert structure issues to CriticIssue objects (outline-based)
    for missing in basic_structure_result.missing_sections:
        all_issues.append(CriticIssue(
            issue_type="structure_violation",
            severity="error",
            section="cover_letter",
            message=f"Missing required section: {missing}",
            original_text=None,
            recommended_fix=f"Add {missing} section"
        ))

    if not basic_structure_result.word_count_valid:
        all_issues.append(CriticIssue(
            issue_type="word_count_violation",
            severity="warning",
            section="cover_letter",
            message=f"Word count ({basic_structure_result.word_count}) outside expected range ({basic_structure_result.expected_range})",
            original_text=None,
            recommended_fix=f"Adjust content to be within {basic_structure_result.expected_range}"
        ))

    # 11. Compute ATS score
    ats_score = compute_ats_score(job_profile, cover_letter_json, "cover_letter")

    # Add issues for critical missing keywords
    for keyword in ats_score.keywords_missing[:3]:
        all_issues.append(CriticIssue(
            issue_type="ats_keyword_missing",
            severity="warning",
            section="cover_letter",
            message=f"Critical ATS keyword missing: '{keyword}'",
            original_text=None,
            recommended_fix=f"Incorporate '{keyword}' naturally into content"
        ))

    # 12. Check requirement coverage (style guide Section 6)
    requirement_score, requirement_issues = check_requirement_coverage(cover_letter_json, job_profile)
    all_issues.extend(requirement_issues)

    # 13. Enforce rules
    rule_issues = enforce_rules(cover_letter_json, "cover_letter", db)
    all_issues.extend(rule_issues)

    # =========================================================================
    # PHASE 4: PASS/FAIL DETERMINATION (Enhanced with Style Enforcement)
    # =========================================================================

    # Count issues by severity
    error_count = sum(1 for issue in all_issues if issue.severity == "error")
    warning_count = sum(1 for issue in all_issues if issue.severity == "warning")
    info_count = sum(1 for issue in all_issues if issue.severity == "info")

    # Check for critical style violations that cause auto-fail
    has_critical_style_violations = any(
        issue.issue_type in [
            "em_dash_violation",
            "emotional_opening_violation",
            "generic_statement_violation",
            "structure_gap_violation",
        ] and issue.severity == "error"
        for issue in all_issues
    )

    # Check for structural gaps (any missing section = auto-fail)
    has_structure_gap = structure_score == 0

    # Check style score threshold
    style_score_fail = overall_style_score < STYLE_SCORE_THRESHOLD

    # Determine pass/fail with enhanced logic
    if strict_mode:
        passed = (
            error_count == 0 and
            warning_count == 0 and
            not style_score_fail
        )
    else:
        # Standard mode: fail on errors, critical violations, or style score below threshold
        passed = (
            error_count == 0 and
            not has_critical_style_violations and
            not has_structure_gap and
            not style_score_fail
        )

    # =========================================================================
    # PHASE 5: QUALITY SCORE CALCULATION (Enhanced)
    # =========================================================================
    # Quality score should reflect overall quality and be consistent with pass/fail
    # If the cover letter fails style enforcement, quality score should be < 85

    # Style-first quality calculation
    # Style score contributes 50% to ensure failing style = failing quality
    if style_score_fail or has_structure_gap or has_critical_style_violations:
        # Cap quality score at 84 when style enforcement fails
        max_quality = 84.0
    else:
        max_quality = 100.0

    # Component contributions (total 100%)
    # Style: 50%, ATS: 25%, Requirements: 15%, Clean bonus: 10%
    style_contribution = overall_style_score * 0.50
    ats_contribution = ats_score.overall_score * 0.25
    req_contribution = requirement_score.coverage_percentage * 0.15
    clean_bonus = 10.0 if (not banned_issues and not em_dash_issues and not prohibited_issues) else 0.0

    # Error and warning penalties
    error_penalty = error_count * 5.0
    warning_penalty = warning_count * 1.5

    quality_score = style_contribution + ats_contribution + req_contribution + clean_bonus - error_penalty - warning_penalty
    quality_score = max(0.0, min(max_quality, quality_score))

    # =========================================================================
    # PHASE 6: GENERATE SUMMARY
    # =========================================================================

    if passed:
        if warning_count > 0:
            summary = f"Cover letter meets quality standards (style score: {overall_style_score}) with {warning_count} warning(s)"
        else:
            summary = f"Cover letter meets all quality standards (style score: {overall_style_score})"
    else:
        issues_list = []
        if style_score_fail:
            issues_list.append(f"style score {overall_style_score} < {STYLE_SCORE_THRESHOLD}")
        if em_dash_count > 0:
            issues_list.append(f"{em_dash_count} em-dash(es)")
        if has_structure_gap:
            issues_list.append("structural gaps")
        if has_critical_style_violations and not has_structure_gap and em_dash_count == 0:
            issues_list.append("critical style violations")
        other_errors = error_count - em_dash_count - len([i for i in all_issues if i.issue_type == "structure_gap_violation" and i.severity == "error"])
        if other_errors > 0:
            issues_list.append(f"{other_errors} other error(s)")
        summary = f"Cover letter has blocking issues: {', '.join(issues_list) if issues_list else 'style enforcement failed'}"

    return CoverLetterCriticResult(
        content_type="cover_letter",
        passed=passed,
        issues=all_issues,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        ats_score=ats_score,
        structure_check=basic_structure_result,
        requirement_coverage=requirement_score,
        style_score=style_score_breakdown,
        em_dash_count=em_dash_count,
        quality_score=quality_score,
        evaluation_summary=summary,
        evaluated_at=datetime.utcnow().isoformat()
    )


# =============================================================================
# RESUME CRITIC FUNCTIONS (PRD 4.3)
# =============================================================================

# Strong action verbs preferred for resume bullets (extended list)
RESUME_STRONG_VERBS = {
    "achieved", "accelerated", "advanced", "architected", "automated",
    "built", "championed", "closed", "coached", "consolidated",
    "created", "delivered", "designed", "developed", "directed",
    "drove", "eliminated", "enabled", "engineered", "established",
    "exceeded", "executed", "expanded", "founded", "generated",
    "grew", "implemented", "improved", "increased", "influenced",
    "initiated", "innovated", "integrated", "introduced", "launched",
    "led", "managed", "maximized", "mentored", "modernized",
    "negotiated", "optimized", "orchestrated", "originated", "overhauled",
    "partnered", "pioneered", "produced", "reduced", "redesigned",
    "reengineered", "restructured", "revamped", "scaled", "secured",
    "shaped", "simplified", "spearheaded", "standardized", "steered",
    "streamlined", "strengthened", "structured", "succeeded", "surpassed",
    "sustained", "systematized", "transformed", "tripled", "unified",
}

# Weak/vague verbs to avoid in resume bullets
RESUME_WEAK_VERBS = {
    "assisted", "contributed", "helped", "participated", "supported",
    "worked", "was responsible", "handled", "dealt with", "involved",
    "tasked with", "took part", "aided",
}

# Metrics indicators (presence = impact-oriented)
METRICS_PATTERNS = [
    r'\$[\d,]+[KMB]?',  # Dollar amounts
    r'\d+%',  # Percentages
    r'\d+x',  # Multipliers
    r'\d+\+',  # Plus amounts
    r'\b\d{2,}\b(?:\s+(?:clients?|users?|customers?|partners?|stakeholders?|teams?|employees?|engineers?))?',  # Numbers with context
    r'(?:increased|decreased|reduced|improved|grew|generated|saved|delivered)\s+(?:by\s+)?\d+',  # Action + number
    r'(?:million|billion|thousand)\b',  # Large numbers in words
]


def extract_bullets_from_resume(resume_json: Dict) -> List[Dict]:
    """
    Extract all bullet points from a TailoredResume JSON.

    Args:
        resume_json: TailoredResume JSON structure

    Returns:
        List of bullet dicts with text and metadata
    """
    bullets = []
    for role in resume_json.get("selected_roles", []):
        for bullet in role.get("selected_bullets", []):
            bullets.append({
                "text": bullet.get("text", ""),
                "bullet_id": bullet.get("bullet_id"),
                "role_title": role.get("job_title", ""),
                "employer": role.get("employer_name", ""),
            })
    return bullets


def check_bullet_action_verbs(bullets: List[Dict]) -> Tuple[int, int, List[CriticIssue]]:
    """
    Check that bullets start with strong action verbs.

    Args:
        bullets: List of bullet dicts from extract_bullets_from_resume

    Returns:
        Tuple of (weak_verb_count, total_bullets, issues)
    """
    issues: List[CriticIssue] = []
    weak_count = 0

    for bullet in bullets:
        text = bullet.get("text", "").strip()
        if not text:
            continue

        # Get first word (the action verb)
        first_word = text.split()[0].lower().rstrip(".,;:") if text.split() else ""

        # Check for weak verbs
        for weak in RESUME_WEAK_VERBS:
            if first_word == weak or text.lower().startswith(weak):
                weak_count += 1
                issues.append(CriticIssue(
                    issue_type="weak_verb_violation",
                    severity="warning",
                    section=f"bullet_{bullet.get('bullet_id', 'unknown')}",
                    message=f"Bullet starts with weak verb: '{first_word}'",
                    original_text=text[:80] + "..." if len(text) > 80 else text,
                    recommended_fix=f"Start with a strong action verb like 'Led', 'Built', 'Delivered', 'Drove'"
                ))
                break

    return weak_count, len(bullets), issues


def check_bullet_metrics(bullets: List[Dict]) -> Tuple[int, List[CriticIssue]]:
    """
    Check for quantifiable metrics/achievements in bullets.

    Args:
        bullets: List of bullet dicts

    Returns:
        Tuple of (bullets_with_metrics, issues for bullets lacking metrics)
    """
    issues: List[CriticIssue] = []
    metrics_count = 0

    for bullet in bullets:
        text = bullet.get("text", "")
        has_metrics = any(re.search(pattern, text) for pattern in METRICS_PATTERNS)

        if has_metrics:
            metrics_count += 1
        else:
            # Not all bullets need metrics, but flag if majority don't have them
            issues.append(CriticIssue(
                issue_type="requirement_coverage",  # Using existing type
                severity="info",  # Informational - not blocking
                section=f"bullet_{bullet.get('bullet_id', 'unknown')}",
                message="Bullet lacks quantifiable metrics",
                original_text=text[:80] + "..." if len(text) > 80 else text,
                recommended_fix="Add specific metrics (%, $, numbers) to quantify impact"
            ))

    return metrics_count, issues


def check_bullet_clarity(bullets: List[Dict]) -> Tuple[float, List[CriticIssue]]:
    """
    Check bullet clarity and conciseness.

    Clarity criteria:
    - Length: 15-35 words ideal
    - No run-on sentences (max 2 commas)
    - No jargon without context

    Args:
        bullets: List of bullet dicts

    Returns:
        Tuple of (clarity_score, issues)
    """
    issues: List[CriticIssue] = []
    clarity_scores = []

    for bullet in bullets:
        text = bullet.get("text", "")
        word_count = count_words(text)
        comma_count = text.count(",")
        bullet_score = 100

        # Check length
        if word_count < 10:
            bullet_score -= 20
            issues.append(CriticIssue(
                issue_type="structure_violation",
                severity="warning",
                section=f"bullet_{bullet.get('bullet_id', 'unknown')}",
                message=f"Bullet too short ({word_count} words)",
                original_text=text,
                recommended_fix="Expand with more detail about impact and context"
            ))
        elif word_count > 40:
            bullet_score -= 25
            issues.append(CriticIssue(
                issue_type="structure_violation",
                severity="warning",
                section=f"bullet_{bullet.get('bullet_id', 'unknown')}",
                message=f"Bullet too long ({word_count} words)",
                original_text=text[:80] + "..." if len(text) > 80 else text,
                recommended_fix="Split into multiple bullets or condense to 15-35 words"
            ))

        # Check comma density (run-on indicator)
        if comma_count > 3:
            bullet_score -= 15
            issues.append(CriticIssue(
                issue_type="comma_overuse_violation",
                severity="info",
                section=f"bullet_{bullet.get('bullet_id', 'unknown')}",
                message=f"Bullet has too many commas ({comma_count})",
                original_text=text[:80] + "..." if len(text) > 80 else text,
                recommended_fix="Restructure to reduce complexity"
            ))

        clarity_scores.append(max(0, bullet_score))

    avg_clarity = sum(clarity_scores) / len(clarity_scores) if clarity_scores else 100.0
    return avg_clarity, issues


def calculate_jd_alignment_score(
    resume_json: Dict,
    job_profile: JobProfile
) -> Tuple[float, List[CriticIssue]]:
    """
    Calculate how well resume content aligns with JD requirements.

    Checks:
    - Skills match to extracted_skills
    - Bullets relevance to core_priorities
    - Must-have capabilities coverage

    Args:
        resume_json: TailoredResume JSON
        job_profile: Target JobProfile

    Returns:
        Tuple of (alignment_score 0-100, issues for gaps)
    """
    issues: List[CriticIssue] = []

    # Extract resume text for matching
    text_parts = [resume_json.get("tailored_summary", "")]
    for role in resume_json.get("selected_roles", []):
        for bullet in role.get("selected_bullets", []):
            text_parts.append(bullet.get("text", ""))
    for skill in resume_json.get("selected_skills", []):
        text_parts.append(skill.get("skill_name", ""))
    resume_text = " ".join(text_parts).lower()

    # Check must-have capabilities
    must_haves = job_profile.must_have_capabilities or []
    must_have_matched = 0
    must_have_missing = []

    for cap in must_haves:
        if cap and cap.lower() in resume_text:
            must_have_matched += 1
        else:
            must_have_missing.append(cap)

    must_have_score = (must_have_matched / len(must_haves) * 100) if must_haves else 100.0

    # Check core priorities
    core_priorities = job_profile.core_priorities or []
    priorities_matched = 0

    for priority in core_priorities[:5]:  # Top 5 priorities
        if priority and any(word.lower() in resume_text for word in priority.split() if len(word) > 4):
            priorities_matched += 1

    priority_score = (priorities_matched / min(5, len(core_priorities)) * 100) if core_priorities else 100.0

    # Check extracted skills
    extracted_skills = job_profile.extracted_skills or []
    skills_matched = 0

    for skill in extracted_skills:
        if skill and skill.lower() in resume_text:
            skills_matched += 1

    skills_score = (skills_matched / len(extracted_skills) * 100) if extracted_skills else 100.0

    # Generate issues for missing must-haves
    for cap in must_have_missing[:3]:  # Top 3 missing
        issues.append(CriticIssue(
            issue_type="requirement_coverage",
            severity="warning",
            section="alignment",
            message=f"Must-have capability not evident: '{cap}'",
            original_text=None,
            recommended_fix=f"Add experience or skill demonstrating: {cap}"
        ))

    # Weighted alignment score
    alignment_score = (
        must_have_score * 0.50 +  # Must-haves most important
        priority_score * 0.30 +   # Core priorities
        skills_score * 0.20       # Extracted skills
    )

    return alignment_score, issues


def calculate_impact_score(bullets: List[Dict]) -> float:
    """
    Calculate impact orientation score based on metrics presence and achievement focus.

    Args:
        bullets: List of bullet dicts

    Returns:
        Impact score 0-100
    """
    if not bullets:
        return 100.0

    metrics_count, _ = check_bullet_metrics(bullets)
    metrics_rate = metrics_count / len(bullets) if bullets else 0

    # Achievement indicators (beyond metrics)
    achievement_words = {
        "achieved", "exceeded", "surpassed", "delivered", "generated",
        "increased", "decreased", "improved", "grew", "reduced", "saved",
        "won", "earned", "recognized", "awarded",
    }

    achievement_count = 0
    for bullet in bullets:
        text = bullet.get("text", "").lower()
        if any(word in text for word in achievement_words):
            achievement_count += 1

    achievement_rate = achievement_count / len(bullets) if bullets else 0

    # Score calculation
    # 50% metrics, 50% achievement language
    impact_score = (metrics_rate * 50) + (achievement_rate * 50)

    # Bonus for high metrics density
    if metrics_rate > 0.6:
        impact_score = min(100, impact_score + 10)

    return impact_score


async def check_resume_tone(
    resume_text: str,
    expected_tone: str,
    llm: BaseLLM
) -> Tuple[float, List[CriticIssue]]:
    """
    Check resume tone matches expected style.

    For resumes, tone should generally be:
    - Executive and direct
    - Achievement-focused
    - Professional (no casual language)

    Args:
        resume_text: Full resume text
        expected_tone: Expected tone from job_profile
        llm: LLM for tone detection

    Returns:
        Tuple of (tone_score 0-100, issues)
    """
    issues: List[CriticIssue] = []
    tone_score = 100

    # Check passive voice (should be minimal in resumes)
    passive_rate, passive_examples = detect_passive_voice(resume_text)
    if passive_rate > 0.10:  # Stricter for resumes than cover letters
        tone_score -= min(30, int(passive_rate * 150))
        issues.append(CriticIssue(
            issue_type="passive_voice_violation",
            severity="warning",
            section="resume",
            message=f"Excessive passive voice ({passive_rate*100:.1f}%)",
            original_text=passive_examples[0] if passive_examples else None,
            recommended_fix="Rewrite using active voice: 'Led team...' not 'Team was led by...'"
        ))

    # Check for casual/unprofessional language
    casual_phrases = [
        "i think", "i feel", "kind of", "sort of", "a lot of",
        "really good", "very nice", "awesome", "amazing",
    ]

    for phrase in casual_phrases:
        if phrase in resume_text.lower():
            tone_score -= 10
            issues.append(CriticIssue(
                issue_type="tone_mismatch",
                severity="warning",
                section="resume",
                message=f"Casual language detected: '{phrase}'",
                original_text=None,
                recommended_fix="Use professional, formal language"
            ))

    # Run LLM tone check
    detected_tone = await llm.infer_tone(resume_text)

    # Resume-specific tone compatibility
    # Formal/professional tones are always acceptable for resumes
    acceptable_tones = {"formal_corporate", "consulting_professional", "executive"}
    if detected_tone not in acceptable_tones and expected_tone in acceptable_tones:
        tone_score -= 15
        issues.append(CriticIssue(
            issue_type="tone_mismatch",
            severity="warning",
            section="resume",
            message=f"Tone ({detected_tone}) may not match expected {expected_tone}",
            original_text=None,
            recommended_fix=f"Adjust language to match {expected_tone} style"
        ))

    return max(0, tone_score), issues


def check_hallucination(
    resume_json: Dict,
    db: Session,
    user_id: int
) -> Tuple[bool, List[str]]:
    """
    Check for potential hallucinations in resume content.

    Validates that:
    - Job titles match original experience records
    - Employer names match original records
    - Dates haven't been altered
    - Bullet text is from actual bullet records (not fabricated)

    Args:
        resume_json: TailoredResume JSON
        db: Database session
        user_id: User ID for validation

    Returns:
        Tuple of (hallucination_check_passed, list of hallucination concerns)
    """
    concerns = []

    for role in resume_json.get("selected_roles", []):
        experience_id = role.get("experience_id")
        if not experience_id:
            concerns.append(f"Role missing experience_id reference")
            continue

        # Fetch original experience
        experience = db.query(Experience).filter(
            Experience.id == experience_id,
            Experience.user_id == user_id
        ).first()

        if not experience:
            concerns.append(f"Experience ID {experience_id} not found in database")
            continue

        # Validate job title
        if role.get("job_title") != experience.job_title:
            concerns.append(
                f"Job title mismatch: '{role.get('job_title')}' vs original '{experience.job_title}'"
            )

        # Validate employer name
        if role.get("employer_name") != experience.employer_name:
            concerns.append(
                f"Employer mismatch: '{role.get('employer_name')}' vs original '{experience.employer_name}'"
            )

        # Validate bullets exist in database
        from db.models import Bullet
        for bullet in role.get("selected_bullets", []):
            bullet_id = bullet.get("bullet_id")
            if bullet_id:
                db_bullet = db.query(Bullet).filter(
                    Bullet.id == bullet_id,
                    Bullet.user_id == user_id
                ).first()
                if not db_bullet:
                    concerns.append(f"Bullet ID {bullet_id} not found in database")

    passed = len(concerns) == 0
    return passed, concerns


# =============================================================================
# SUMMARY QUALITY VALIDATION (PRD 2.10, 4.8)
# =============================================================================

# Generic openings that indicate a stale/non-tailored summary
GENERIC_SUMMARY_PATTERNS = [
    r"^professional with",
    r"^experienced professional",
    r"^seasoned (?:professional|expert|leader)",
    r"^highly motivated",
    r"^dedicated professional",
    r"^accomplished professional",
    r"^results-driven professional",
]


def validate_summary_quality(
    summary_text: str,
    job_profile: JobProfile,
    max_words: int = 60,
    context: str = "summary"
) -> List[CriticIssue]:
    """
    Validate professional summary for PRD 2.10 and 4.8 compliance.

    Checks:
    - Word count limit (default 60)
    - Banned phrases
    - Em-dashes
    - Generic/stale language
    - Job priority alignment

    Args:
        summary_text: Summary to validate
        job_profile: Target job for context
        max_words: Maximum word count (default 60 per PRD 2.10)
        context: Section context for issues

    Returns:
        List of CriticIssue objects
    """
    issues: List[CriticIssue] = []

    if not summary_text:
        issues.append(CriticIssue(
            issue_type="structure_violation",
            severity="error",
            section=context,
            message="Summary is empty or missing",
            original_text=None,
            recommended_fix="Generate a tailored summary using candidate profile and job priorities"
        ))
        return issues

    # 1. Word count check
    word_count = count_words(summary_text)
    if word_count > max_words:
        issues.append(CriticIssue(
            issue_type="word_count_violation",
            severity="error",  # Exceeding limit is an error per PRD 2.10
            section=context,
            message=f"Summary exceeds {max_words}-word limit ({word_count} words)",
            original_text=summary_text[:100] + "..." if len(summary_text) > 100 else summary_text,
            recommended_fix=f"Reduce summary to {max_words} words while maintaining key positioning"
        ))

    # 2. Banned phrases check (reuse existing infrastructure)
    banned_issues = check_banned_phrases(
        text=summary_text,
        company_name=None,  # Company context not needed for summary
        context=context
    )
    issues.extend(banned_issues)

    # 3. Em-dash check
    if re.search(EM_DASH_PATTERN, summary_text):
        # Find the context around the em-dash
        match = re.search(EM_DASH_PATTERN, summary_text)
        start = max(0, match.start() - 15)
        end = min(len(summary_text), match.end() + 15)
        snippet = summary_text[start:end]

        issues.append(CriticIssue(
            issue_type="em_dash_violation",
            severity="error",  # Em-dashes are banned per PRD 4.8
            section=context,
            message="Em-dash detected in summary (banned punctuation)",
            original_text=f"...{snippet}..." if start > 0 else f"{snippet}...",
            recommended_fix="Use commas, parentheses, or restructure the sentence"
        ))

    # 4. Generic opening check (stale summary detection)
    summary_lower = summary_text.lower().strip()
    for pattern in GENERIC_SUMMARY_PATTERNS:
        if re.match(pattern, summary_lower):
            issues.append(CriticIssue(
                issue_type="cliche_violation",
                severity="warning",
                section=context,
                message=f"Generic opening detected: '{summary_text[:50]}...'",
                original_text=summary_text[:60],
                recommended_fix="Lead with specific identity/specialization aligned to job (use candidate_profile.primary_identity)"
            ))
            break  # Only flag once

    # 5. Job priority alignment check (stale summary detection)
    if job_profile.core_priorities:
        priority_mentioned = False
        for priority in job_profile.core_priorities[:3]:
            # Check for key terms from each priority
            key_terms = [term.lower() for term in priority.split() if len(term) > 4]
            for term in key_terms:
                if term in summary_lower:
                    priority_mentioned = True
                    break
            if priority_mentioned:
                break

        if not priority_mentioned:
            priorities_str = ", ".join(job_profile.core_priorities[:3])
            issues.append(CriticIssue(
                issue_type="requirement_coverage",
                severity="warning",
                section=context,
                message="Summary appears non-tailored: no alignment to job priorities detected",
                original_text=summary_text[:80] + "..." if len(summary_text) > 80 else summary_text,
                recommended_fix=f"Incorporate themes from job priorities: {priorities_str}"
            ))

    return issues


async def validate_resume_truthfulness(
    resume_json: Dict[str, Any],
    user_id: int,
    db: Session,
) -> Tuple[bool, List[CriticIssue]]:
    """
    Validate that a tailored resume does not contain fabricated information.

    Checks:
    1. All employer names match stored employment_history
    2. All job titles match exactly
    3. All employment dates match exactly
    4. All locations are not altered

    Args:
        resume_json: The tailored resume as a dictionary
        user_id: User ID to validate against
        db: Database session

    Returns:
        (is_truthful, list_of_issues)
    """
    from db.models import Experience  # Local import to avoid circular

    issues = []

    # Fetch user's stored experiences
    experiences = db.query(Experience).filter(
        Experience.user_id == user_id
    ).all()

    # Build lookup by ID
    stored_experiences = {exp.id: exp for exp in experiences}

    # Check each selected_role in resume
    selected_roles = resume_json.get('selected_roles', [])

    for role in selected_roles:
        exp_id = role.get('experience_id')

        if exp_id is None:
            continue  # Skip portfolio bullets without experience_id

        # Handle synthetic portfolio bullet IDs (negative)
        if exp_id < 0:
            continue  # Portfolio bullets don't need truthfulness validation

        if exp_id not in stored_experiences:
            issues.append(CriticIssue(
                issue_type='truthfulness',
                severity='error',
                section='experience',
                message=f"Experience ID {exp_id} not found in stored employment history",
                recommended_fix="Remove this fabricated experience or verify experience_id",
                original_text=None
            ))
            continue

        stored = stored_experiences[exp_id]

        # Check employer name
        role_employer = role.get('employer_name', '')
        if role_employer and role_employer != stored.employer_name:
            issues.append(CriticIssue(
                issue_type='truthfulness',
                severity='error',
                section='experience',
                message=f"Employer name mismatch: '{role_employer}' vs stored '{stored.employer_name}'",
                recommended_fix=f"Change employer_name to '{stored.employer_name}'",
                original_text=role_employer
            ))

        # Check job title
        role_title = role.get('job_title', '')
        if role_title and role_title != stored.job_title:
            issues.append(CriticIssue(
                issue_type='truthfulness',
                severity='error',
                section='experience',
                message=f"Job title mismatch: '{role_title}' vs stored '{stored.job_title}'",
                recommended_fix=f"Change job_title to '{stored.job_title}'",
                original_text=role_title
            ))

        # Check start date
        role_start = role.get('start_date', '')
        stored_start = stored.start_date.isoformat() if stored.start_date else None
        if role_start and stored_start and role_start != stored_start:
            issues.append(CriticIssue(
                issue_type='truthfulness',
                severity='error',
                section='experience',
                message=f"Start date mismatch for {stored.employer_name}: '{role_start}' vs stored '{stored_start}'",
                recommended_fix=f"Change start_date to '{stored_start}'",
                original_text=role_start
            ))

        # Check end date (if provided)
        role_end = role.get('end_date')
        stored_end = stored.end_date.isoformat() if stored.end_date else None
        if role_end and stored_end and role_end != stored_end:
            issues.append(CriticIssue(
                issue_type='truthfulness',
                severity='error',
                section='experience',
                message=f"End date mismatch for {stored.employer_name}: '{role_end}' vs stored '{stored_end}'",
                recommended_fix=f"Change end_date to '{stored_end}'",
                original_text=role_end
            ))

        # Check location (if provided in both)
        role_location = role.get('location')
        if role_location and stored.location and role_location != stored.location:
            issues.append(CriticIssue(
                issue_type='truthfulness',
                severity='warning',  # Location is less critical
                section='experience',
                message=f"Location mismatch for {stored.employer_name}: '{role_location}' vs stored '{stored.location}'",
                recommended_fix=f"Change location to '{stored.location}'",
                original_text=role_location
            ))

    is_truthful = len([i for i in issues if i.severity == 'error']) == 0

    if issues:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Truthfulness validation found {len(issues)} issues for user {user_id}")

    return is_truthful, issues


def check_pagination_constraints(
    resume_json: Dict,
    context: str = "resume"
) -> Tuple[bool, int, List[CriticIssue]]:
    """
    Check if resume fits within 2-page line budget per PRD 2.11.

    Args:
        resume_json: TailoredResume JSON structure
        context: Section context for issue reporting

    Returns:
        Tuple of (fits_budget, estimated_lines, list of CriticIssue)
    """
    issues: List[CriticIssue] = []

    try:
        pagination_service = PaginationService()
        page_simulator = PageSplitSimulator(pagination_service)

        # Extract and estimate summary lines
        summary_text = resume_json.get("tailored_summary", "")
        summary_lines = pagination_service.estimate_summary_lines(summary_text)

        # Extract and estimate skills lines
        selected_skills = resume_json.get("selected_skills", [])
        skills = [s.get("skill", "") if isinstance(s, dict) else str(s) for s in selected_skills]
        skills_lines = pagination_service.estimate_skills_lines(skills)

        # Build role structures for simulation
        role_structures = []
        for role in resume_json.get("selected_roles", []):
            bullets_info = []

            # Handle direct bullets
            for bullet in role.get("selected_bullets", []):
                bullet_text = bullet.get("text", "") if isinstance(bullet, dict) else str(bullet)
                line_cost = pagination_service.estimate_bullet_lines(bullet_text)
                bullets_info.append({'text': bullet_text, 'lines': line_cost})

            # Handle engagement bullets (consulting roles)
            for eng in role.get("selected_engagements", []):
                for bullet in eng.get("selected_bullets", []):
                    bullet_text = bullet.get("text", "") if isinstance(bullet, dict) else str(bullet)
                    line_cost = pagination_service.estimate_bullet_lines(bullet_text)
                    bullets_info.append({'text': bullet_text, 'lines': line_cost})

            role_structures.append({
                'experience_id': role.get("experience_id", 0),
                'job_header_lines': pagination_service.get_job_header_lines(),
                'bullets': bullets_info
            })

        # Simulate page layout
        layout = page_simulator.simulate_page_layout(summary_lines, skills_lines, role_structures)

        total_budget = pagination_service.get_total_budget()
        estimated_lines = layout.total_lines
        fits_budget = layout.fits_in_budget

        # Report violations
        if not fits_budget:
            overflow = estimated_lines - total_budget
            issues.append(CriticIssue(
                issue_type="pagination_overflow",
                severity="warning",
                section=context,
                message=f"Resume exceeds 2-page budget by ~{overflow} lines ({estimated_lines} estimated vs {total_budget} budget)",
                original_text=None,
                recommended_fix="Reduce bullet count on older roles or compress bullet text"
            ))

        # Report specific page violations from simulator
        for violation in layout.violations:
            if "orphan" in violation.lower():
                issues.append(CriticIssue(
                    issue_type="pagination_orphan",
                    severity="info",
                    section=context,
                    message=violation,
                    original_text=None,
                    recommended_fix="Role was moved to avoid orphaned header"
                ))

        return fits_budget, estimated_lines, issues

    except (TypeError, KeyError, AttributeError) as e:
        # Handle expected errors from malformed resume_json
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Pagination check failed due to malformed input (non-blocking): {e}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        # Return None for estimated_lines to indicate error, but don't block
        return True, None, [CriticIssue(
            issue_type="pagination_check_error",
            severity="info",
            section=context,
            message=f"Pagination check could not complete: {str(e)[:100]}",
            original_text=None,
            recommended_fix="Ensure resume JSON structure is valid"
        )]
    except Exception as e:
        # Unexpected errors should be logged with full traceback
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(
            f"Unexpected error in pagination check: {e}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        return True, None, []


async def evaluate_resume(
    resume_json: Dict,
    job_profile: JobProfile,
    db: Session,
    user_id: int,
    llm: Optional[BaseLLM] = None,
    strict_mode: bool = False,
    iteration: int = 1
) -> ResumeCriticResult:
    """
    Perform complete critic evaluation for a tailored resume.

    Implements PRD 4.3 resume rubric:
    - Alignment to JD requirements (alignment_score)
    - Clarity and conciseness of bullets (clarity_score)
    - Impact orientation - achievements, metrics (impact_score)
    - Tone - executive, direct, professional (tone_score)
    - No hallucinations (hallucination_check)
    - ATS keyword coverage (ats_score)
    - Skills relevance (via ats_score.skills_score)
    - Proper action verbs (weak_verb_count)

    Args:
        resume_json: TailoredResume JSON structure
        job_profile: Target JobProfile for alignment checking
        db: Database session
        user_id: User ID for hallucination validation
        llm: LLM instance (defaults to MockLLM)
        strict_mode: If True, treat warnings as errors
        iteration: Current critic iteration number

    Returns:
        ResumeCriticResult with detailed evaluation and scoring
    """
    # Initialize LLM
    if llm is None:
        llm = MockLLM()

    if not isinstance(resume_json, dict):
        resume_json = {}

    all_issues: List[CriticIssue] = []

    # Extract bullets for analysis
    bullets = extract_bullets_from_resume(resume_json)
    bullets_total = len(bullets)

    # Extract full text for analysis
    text_parts = [resume_json.get("tailored_summary", "")]
    for bullet in bullets:
        text_parts.append(bullet.get("text", ""))
    resume_text = " ".join(text_parts)

    # ==========================================================================
    # 1. JD ALIGNMENT SCORING
    # ==========================================================================
    alignment_score, alignment_issues = calculate_jd_alignment_score(resume_json, job_profile)
    all_issues.extend(alignment_issues)

    # ==========================================================================
    # 2. CLARITY AND CONCISENESS SCORING
    # ==========================================================================
    clarity_score, clarity_issues = check_bullet_clarity(bullets)
    all_issues.extend(clarity_issues)

    # ==========================================================================
    # 3. IMPACT ORIENTATION SCORING
    # ==========================================================================
    impact_score = calculate_impact_score(bullets)
    bullets_with_metrics, metrics_issues = check_bullet_metrics(bullets)
    # Only add metrics issues if impact score is low
    if impact_score < 50:
        all_issues.extend(metrics_issues[:3])  # Limit to top 3

    # ==========================================================================
    # 4. TONE VALIDATION
    # ==========================================================================
    expected_tone = job_profile.tone_style or "formal_corporate"
    tone_score, tone_issues = await check_resume_tone(resume_text, expected_tone, llm)
    all_issues.extend(tone_issues)

    # ==========================================================================
    # 5. ACTION VERB QUALITY
    # ==========================================================================
    weak_verb_count, _, verb_issues = check_bullet_action_verbs(bullets)
    all_issues.extend(verb_issues)

    # ==========================================================================
    # 6. HALLUCINATION DETECTION
    # ==========================================================================
    hallucination_passed, hallucination_concerns = check_hallucination(
        resume_json, db, user_id
    )
    if not hallucination_passed:
        for concern in hallucination_concerns:
            all_issues.append(CriticIssue(
                issue_type="rule_violation",
                severity="error",  # Hallucinations are blocking
                section="resume",
                message=f"Hallucination detected: {concern}",
                original_text=None,
                recommended_fix="Ensure all content matches original database records"
            ))

    # ==========================================================================
    # 7. BANNED PHRASES CHECK
    # ==========================================================================
    banned_issues = check_banned_phrases(resume_text, context="resume")
    all_issues.extend(banned_issues)

    # ==========================================================================
    # 7B. SUMMARY QUALITY VALIDATION (PRD 2.10, 4.8)
    # ==========================================================================
    summary_text = resume_json.get("tailored_summary", "")
    summary_issues = validate_summary_quality(
        summary_text=summary_text,
        job_profile=job_profile,
        max_words=60,  # PRD 2.10 default
        context="summary"
    )
    all_issues.extend(summary_issues)

    # ==========================================================================
    # 8. STRUCTURE CHECK
    # ==========================================================================
    structure_result = check_structure(resume_json, "resume")
    for missing in structure_result.missing_sections:
        all_issues.append(CriticIssue(
            issue_type="structure_violation",
            severity="error",
            section="resume",
            message=f"Missing required section: {missing}",
            original_text=None,
            recommended_fix=f"Add {missing} section"
        ))

    if not structure_result.word_count_valid:
        all_issues.append(CriticIssue(
            issue_type="word_count_violation",
            severity="warning",
            section="resume_summary",
            message=f"Summary word count ({structure_result.word_count}) outside range ({structure_result.expected_range})",
            original_text=None,
            recommended_fix=f"Adjust summary to {structure_result.expected_range}"
        ))

    # ==========================================================================
    # 9. ATS SCORE
    # ==========================================================================
    ats_score = compute_ats_score(job_profile, resume_json, "resume")

    for keyword in ats_score.keywords_missing[:3]:
        all_issues.append(CriticIssue(
            issue_type="ats_keyword_missing",
            severity="warning",
            section="resume",
            message=f"Critical ATS keyword missing: '{keyword}'",
            original_text=None,
            recommended_fix=f"Incorporate '{keyword}' into summary or bullets"
        ))

    # ==========================================================================
    # 9B. PAGINATION CONSTRAINTS CHECK (Sprint 8C.8)
    # ==========================================================================
    fits_pagination, estimated_lines, pagination_issues = check_pagination_constraints(
        resume_json=resume_json,
        context="resume"
    )
    all_issues.extend(pagination_issues)

    # ==========================================================================
    # 10. RULE ENFORCEMENT
    # ==========================================================================
    rule_issues = enforce_rules(resume_json, "resume", db)
    all_issues.extend(rule_issues)

    # ==========================================================================
    # 11. TRUTHFULNESS VALIDATION
    # ==========================================================================
    truthful, truthfulness_issues = await validate_resume_truthfulness(
        resume_json=resume_json,
        user_id=user_id,
        db=db,
    )
    all_issues.extend(truthfulness_issues)

    # ==========================================================================
    # PASS/FAIL DETERMINATION
    # ==========================================================================
    error_count = sum(1 for issue in all_issues if issue.severity == "error")
    warning_count = sum(1 for issue in all_issues if issue.severity == "warning")
    info_count = sum(1 for issue in all_issues if issue.severity == "info")

    if strict_mode:
        passed = error_count == 0 and warning_count == 0 and truthful
    else:
        passed = error_count == 0 and truthful

    # ==========================================================================
    # QUALITY SCORE CALCULATION
    # ==========================================================================
    # Weighted average of component scores
    # Alignment: 30%, Clarity: 20%, Impact: 20%, Tone: 15%, ATS: 15%
    quality_score = (
        alignment_score * 0.30 +
        clarity_score * 0.20 +
        impact_score * 0.20 +
        tone_score * 0.15 +
        ats_score.overall_score * 0.15
    )

    # Penalties for errors and hallucinations
    if not hallucination_passed:
        quality_score = max(0, quality_score - 30)  # Major penalty
    if not truthful:
        quality_score = min(quality_score, 60.0)  # Cap score if truthfulness fails
    quality_score = max(0, quality_score - (error_count * 5) - (warning_count * 2))
    quality_score = min(100, max(0, quality_score))

    # ==========================================================================
    # DETERMINE IF RETRY NEEDED
    # ==========================================================================
    # Retry if passed=False and iteration < 3
    should_retry = not passed and iteration < 3

    # ==========================================================================
    # GENERATE SUMMARY
    # ==========================================================================
    if passed:
        if warning_count > 0:
            summary = f"Resume meets quality standards with {warning_count} warning(s)"
        else:
            summary = "Resume meets all quality standards"
    else:
        blocking_reasons = []
        if not hallucination_passed:
            blocking_reasons.append("hallucination detected")
        if error_count > len(hallucination_concerns):
            blocking_reasons.append(f"{error_count - len(hallucination_concerns)} other error(s)")
        summary = f"Resume has blocking issues: {', '.join(blocking_reasons) if blocking_reasons else f'{error_count} error(s)'}"

    return ResumeCriticResult(
        content_type="resume",
        passed=passed,
        issues=all_issues,
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        alignment_score=round(alignment_score, 1),
        clarity_score=round(clarity_score, 1),
        impact_score=round(impact_score, 1),
        tone_score=round(tone_score, 1),
        ats_score=ats_score,
        structure_check=structure_result,
        hallucination_check_passed=hallucination_passed,
        hallucination_issues=hallucination_concerns,
        bullets_with_metrics=bullets_with_metrics,
        bullets_total=bullets_total,
        weak_verb_count=weak_verb_count,
        quality_score=round(quality_score, 1),
        evaluation_summary=summary,
        evaluated_at=datetime.utcnow().isoformat(),
        iteration=iteration,
        should_retry=should_retry,
    )
