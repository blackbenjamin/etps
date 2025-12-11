"""
Cover Letter Generation Service

Generates tailored cover letters with tone compliance, ATS optimization,
banned phrase checking, and quality scoring.
"""

import logging
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

import yaml
from sqlalchemy.orm import Session

from db.models import CompanyProfile, JobProfile, User


# Configuration loader
def _load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = os.path.join(
        os.path.dirname(__file__), '..', 'config', 'config.yaml'
    )
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}


_CONFIG = _load_config()
from schemas.cover_letter import (
    ATSKeywordCoverage,
    BannedPhraseCheck,
    BannedPhraseViolation,
    CoverLetterCriticResult,
    CoverLetterOutline,
    CoverLetterRationale,
    CriticIssue,
    GeneratedCoverLetter,
    RequirementCoverage,
    ToneComplianceResult,
)
from schemas.skill_gap import SkillGapResponse
from schemas.capability import CapabilityClusterAnalysis
from services.llm.base import BaseLLM
from services.llm import create_llm
from services.skill_gap import analyze_skill_gap, get_cluster_analysis, find_skill_match, normalize_skill
# Sprint 8: Learning from approved outputs (available for future integration)
from services.output_retrieval import (
    retrieve_similar_cover_letter_paragraphs,
    format_examples_for_prompt,
)

# Initialize logger
logger = logging.getLogger(__name__)


def smart_truncate(text: Optional[str], max_length: int = 100) -> str:
    """Truncate text at natural boundaries without cutting mid-word or mid-sentence.

    Prioritizes keeping complete thoughts over strict length limits.
    Avoids ending on articles, prepositions, or incomplete phrases.
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text

    # Words that should not end a sentence (articles, prepositions, etc.)
    bad_endings = {
        'the', 'a', 'an', 'of', 'for', 'to', 'at', 'in', 'on', 'by', 'with',
        'and', 'or', 'but', 'as', 'from', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'under', 'over', 'its', 'their',
        'our', 'my', 'your', 'this', 'that', 'these', 'those', 'all', 'each',
        'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
        'five', 'three', 'two', 'ten', 'first', 'second', 'third'
    }

    # Try to find a sentence boundary within limit (strong preference)
    truncated = text[:max_length]

    # Look for sentence boundaries first - these are always preferred
    for punct in ['. ', '! ', '? ']:
        last_sent = truncated.rfind(punct)
        if last_sent > max_length // 3:  # Accept if we keep at least 1/3
            return text[:last_sent + 1].strip()

    # Check if there's a sentence boundary just past the limit (allow 30% overflow for complete sentences)
    extended = text[:int(max_length * 1.3)]
    for punct in ['. ', '! ', '? ']:
        sent_pos = extended.find(punct, max_length // 2)
        if sent_pos != -1 and sent_pos < max_length * 1.3:
            return text[:sent_pos + 1].strip()

    # Avoid cutting mid-list: if text has "and" or "or", try to include the full list
    and_pos = truncated.rfind(' and ')
    or_pos = truncated.rfind(' or ')
    list_connector_pos = max(and_pos, or_pos)
    if list_connector_pos > max_length // 2:
        # Find the end of the item after "and"/"or"
        after_connector = text[list_connector_pos + 5:]  # Skip " and " or " or "
        # Find next comma, period, or end
        end_pos = len(after_connector)
        for delim in [',', '.', ';', ' -']:
            pos = after_connector.find(delim)
            if pos != -1 and pos < end_pos:
                end_pos = pos
        # Include the list completion if it doesn't exceed 150% of max
        full_list_end = list_connector_pos + 5 + end_pos
        if full_list_end < max_length * 1.5:
            return text[:full_list_end].strip().rstrip(',')

    # For clauses ending in comma, only use if it's a natural pause (not mid-list)
    for punct in ['; ', ' - ']:  # Semicolon and dash are safer clause boundaries
        last_clause = truncated.rfind(punct)
        if last_clause > max_length // 2:
            return text[:last_clause].strip()

    # Fall back to last word boundary, but avoid bad endings
    last_space = truncated.rfind(' ')
    while last_space > max_length // 3:
        candidate = text[:last_space].strip()
        last_word = candidate.split()[-1].lower().rstrip('.,;:') if candidate.split() else ''
        if last_word not in bad_endings:
            return candidate
        # Try earlier word boundary
        last_space = text[:last_space].rfind(' ')

    # If we can't find a good boundary, just use the truncated text
    return truncated.strip()


# Banned phrases with severity levels
# These are clichéd, generic, or overused phrases that weaken cover letters
# Aligned with cover_letter_style_guide.md
BANNED_PHRASES: Dict[str, str] = {
    # Critical - never use these (from style guide Section 2)
    "i am writing to express my interest": "critical",
    "to whom it may concern": "critical",
    "i believe i would be a great fit": "critical",
    "i am confident i would be a great fit": "critical",
    "i am confident that": "critical",
    "please find attached": "critical",
    "i am the perfect candidate": "critical",

    # Critical - banned openings from style guide
    "i am excited to apply for": "critical",

    # Critical - banned closings from style guide
    "i look forward to hearing from you": "critical",
    "please do not hesitate to contact me": "critical",
    "i am available at your convenience": "critical",

    # Critical - banned references from style guide
    "per your job description": "critical",
    "as listed in the posting": "critical",
    "your requirements state": "critical",

    # Major - avoid strongly (banned adjectives from style guide)
    "dear hiring manager": "major",  # Only major if company is known
    "i am very interested in": "major",
    "i came across this position": "major",
    "i am excited to apply": "major",
    "passionate": "major",
    "passion for": "major",
    "dynamic": "major",
    "motivated": "major",
    "driven": "major",
    "fast-paced": "major",
    "results-oriented": "major",
    "proven track record": "major",
    "team player": "major",
    "detail-oriented": "major",
    "self-starter": "major",
    "think outside the box": "major",
    "go-getter": "major",
    "hard worker": "major",

    # Minor - reduce usage, can be acceptable in context
    "leverage": "minor",
    "synergy": "minor",
    "best-in-class": "minor",
    "world-class": "minor",
    "cutting-edge": "minor",
    "innovative solutions": "minor",
    "hit the ground running": "minor",
    "dynamic environment": "minor",
}

# Em-dash pattern for detection (style guide explicitly bans em-dashes)
# Note: Only match true em-dash (U+2014), not double hyphens which are valid in compound words
EM_DASH_PATTERN = r'—'

# Pre-compiled regex patterns for performance (avoid re-compiling in loops)
_EM_DASH_COMPILED = re.compile(EM_DASH_PATTERN)

# Pre-compiled phrase boundary pattern template
# Used for banned phrases and keyword matching
def _compile_phrase_pattern(phrase: str) -> re.Pattern:
    """Compile a phrase pattern with word boundaries (case-insensitive)."""
    return re.compile(
        r'(?<![a-zA-Z])' + re.escape(phrase) + r'(?![a-zA-Z])',
        re.IGNORECASE
    )

# Pre-compile banned phrase patterns at module load time
_BANNED_PHRASE_PATTERNS: dict[str, re.Pattern] = {
    phrase: _compile_phrase_pattern(phrase)
    for phrase in BANNED_PHRASES.keys()
}

# Structure templates from style guide Section 3
STRUCTURE_TEMPLATES = {
    "standard": {
        "word_count_target": 265,
        "word_count_range": (250, 275),
        "paragraphs": 4,
        "description": "Standard template: Hook + Positioning, Experience Alignment (bullets), Differentiator, Company Fit + Close"
    },
    "executive": {
        "word_count_target": 225,
        "word_count_range": (210, 240),
        "paragraphs": 3,
        "description": "Executive template: Hook + Positioning, Experience + Differentiator, Company Fit + Close"
    },
    "ultra_tight": {
        "word_count_target": 175,
        "word_count_range": (150, 200),
        "paragraphs": 2,
        "description": "Ultra-tight template: Hook + Key Experience, Differentiator + Close"
    }
}

# Tone compatibility matrix for scoring
# Keys are (target_tone, detected_tone) tuples, values are compatibility scores
TONE_COMPATIBILITY: Dict[Tuple[str, str], float] = {
    # Exact matches
    ('formal_corporate', 'formal_corporate'): 1.0,
    ('startup_casual', 'startup_casual'): 1.0,
    ('consulting_professional', 'consulting_professional'): 1.0,
    ('mission_driven', 'mission_driven'): 1.0,
    ('technical_precise', 'technical_precise'): 1.0,
    ('academic_research', 'academic_research'): 1.0,

    # Highly compatible pairs (0.85)
    ('formal_corporate', 'consulting_professional'): 0.85,
    ('consulting_professional', 'formal_corporate'): 0.85,
    ('technical_precise', 'formal_corporate'): 0.85,
    ('formal_corporate', 'technical_precise'): 0.85,
    ('consulting_professional', 'technical_precise'): 0.85,
    ('technical_precise', 'consulting_professional'): 0.85,

    # Moderately compatible pairs (0.70)
    ('mission_driven', 'startup_casual'): 0.70,
    ('startup_casual', 'mission_driven'): 0.70,
    ('mission_driven', 'consulting_professional'): 0.70,
    ('consulting_professional', 'mission_driven'): 0.70,
    ('academic_research', 'technical_precise'): 0.70,
    ('technical_precise', 'academic_research'): 0.70,

    # Less compatible but acceptable pairs (0.55)
    ('startup_casual', 'formal_corporate'): 0.55,
    ('formal_corporate', 'startup_casual'): 0.55,
    ('mission_driven', 'formal_corporate'): 0.55,
    ('formal_corporate', 'mission_driven'): 0.55,
    ('academic_research', 'consulting_professional'): 0.55,
    ('consulting_professional', 'academic_research'): 0.55,

    # Mismatched pairs (default 0.35)
}


def check_em_dashes(text: str) -> List[BannedPhraseViolation]:
    """
    Check for em-dashes in text (explicitly banned by style guide).

    Args:
        text: Text to check

    Returns:
        List of BannedPhraseViolation for each em-dash found
    """
    violations = []

    for match in _EM_DASH_COMPILED.finditer(text):
        # Find which line this match is on
        char_pos = match.start()
        line_count = text[:char_pos].count('\n')

        # Determine section
        lines = text.split('\n')
        if line_count < 3:
            section = "greeting"
        elif line_count >= len(lines) - 4:
            section = "closing"
        else:
            section = "body"

        violations.append(BannedPhraseViolation(
            phrase="em-dash (—)",
            severity="critical",
            section=section
        ))

    return violations


def check_banned_phrases(
    text: str,
    company_name: Optional[str] = None
) -> BannedPhraseCheck:
    """
    Detect banned phrases in cover letter text.

    Includes em-dash detection as per style guide Section 2.

    Args:
        text: Cover letter text to check
        company_name: Company name if known (affects some checks)

    Returns:
        BannedPhraseCheck with violations and severity
    """
    violations: List[BannedPhraseViolation] = []
    text_lower = text.lower()

    # Check for em-dashes first (style guide Section 2: Banned Punctuation)
    em_dash_violations = check_em_dashes(text)
    violations.extend(em_dash_violations)

    # Determine section boundaries (rough heuristics)
    lines = text.split('\n')
    greeting_end = min(3, len(lines))  # First 3 lines typically greeting
    closing_start = max(0, len(lines) - 4)  # Last 4 lines typically closing

    def get_section(line_idx: int) -> str:
        if line_idx < greeting_end:
            return "greeting"
        elif line_idx >= closing_start:
            return "closing"
        return "body"

    # Check each banned phrase using pre-compiled patterns
    for phrase, severity in BANNED_PHRASES.items():
        # Special case: "dear hiring manager" is only major if company is known
        if phrase == "dear hiring manager" and not company_name:
            severity = "minor"  # Downgrade if company unknown

        # Use pre-compiled pattern for performance
        pattern = _BANNED_PHRASE_PATTERNS[phrase]

        for match in pattern.finditer(text_lower):
            # Find which line this match is on
            char_pos = match.start()
            line_idx = text[:char_pos].count('\n')
            section = get_section(line_idx)

            violations.append(BannedPhraseViolation(
                phrase=phrase,
                severity=severity,
                section=section
            ))

    # Determine overall severity
    if not violations:
        overall_severity = "none"
    elif any(v.severity == "critical" for v in violations):
        overall_severity = "critical"
    elif any(v.severity == "major" for v in violations):
        overall_severity = "major"
    else:
        overall_severity = "minor"

    # Passed means no critical or major violations
    passed = overall_severity in ("none", "minor")

    return BannedPhraseCheck(
        violations_found=len(violations),
        violations=violations,
        overall_severity=overall_severity,
        passed=passed
    )


async def assess_tone_compliance(
    cover_letter_text: str,
    job_profile: JobProfile,
    llm: BaseLLM
) -> ToneComplianceResult:
    """
    Assess if cover letter tone matches job description tone.

    Args:
        cover_letter_text: Generated cover letter
        job_profile: Job profile with tone_style
        llm: LLM instance for tone detection

    Returns:
        ToneComplianceResult with compliance score
    """
    # Get target tone from job profile
    target_tone = job_profile.tone_style or "formal_corporate"

    # Detect tone of generated cover letter
    detected_tone = await llm.infer_tone(cover_letter_text)

    # Calculate compliance score from compatibility matrix
    compliance_score = TONE_COMPATIBILITY.get(
        (target_tone, detected_tone),
        0.35  # Default for unknown combinations
    )

    # Determine if tones are compatible (>= 0.55 threshold)
    compatible = compliance_score >= 0.55

    # Generate explanatory notes
    if compliance_score >= 0.85:
        tone_notes = (
            f"Excellent tone alignment. Cover letter matches the {target_tone} "
            f"style expected for this role."
        )
    elif compliance_score >= 0.70:
        tone_notes = (
            f"Good tone alignment. The {detected_tone} style is compatible with "
            f"the expected {target_tone} tone."
        )
    elif compliance_score >= 0.55:
        tone_notes = (
            f"Acceptable tone alignment. The {detected_tone} style may slightly "
            f"differ from {target_tone}, but remains professional."
        )
    else:
        tone_notes = (
            f"Tone mismatch detected. The {detected_tone} style may not align well "
            f"with the expected {target_tone} tone. Consider adjusting formality level."
        )

    return ToneComplianceResult(
        target_tone=target_tone,
        detected_tone=detected_tone,
        compliance_score=round(compliance_score, 2),
        compatible=compatible,
        tone_notes=tone_notes
    )


def analyze_ats_keyword_coverage(
    cover_letter_text: str,
    job_profile: JobProfile
) -> ATSKeywordCoverage:
    """
    Analyze ATS keyword coverage in cover letter.

    Args:
        cover_letter_text: Generated cover letter
        job_profile: Job profile with extracted skills

    Returns:
        ATSKeywordCoverage analysis
    """
    # Build keyword list from job profile
    keywords: Set[str] = set()

    # Add extracted skills
    if job_profile.extracted_skills:
        keywords.update(job_profile.extracted_skills)

    # Add must-have capabilities
    if job_profile.must_have_capabilities:
        keywords.update(job_profile.must_have_capabilities)

    # Extract key terms from core priorities (simple approach)
    if job_profile.core_priorities:
        for priority in job_profile.core_priorities:
            # Add multi-word priority as keyword
            keywords.add(priority)

    if not keywords:
        # No keywords to check - cannot assess coverage adequately
        return ATSKeywordCoverage(
            total_keywords=0,
            keywords_covered=0,
            coverage_percentage=0.0,  # Cannot assess without keywords
            missing_critical_keywords=[],
            covered_keywords=[],
            coverage_adequate=False  # Fail until keywords are available
        )

    # Convert cover letter to word set for matching
    cover_letter_lower = cover_letter_text.lower()

    covered_keywords: List[str] = []
    missing_keywords: List[str] = []

    # Import here to avoid circular import
    from services.skill_gap import SKILL_SYNONYMS

    for keyword in keywords:
        # Check direct match using phrase boundaries (compile once per keyword)
        pattern = _compile_phrase_pattern(keyword.lower())
        if pattern.search(cover_letter_lower):
            covered_keywords.append(keyword)
        else:
            # Check if any synonym of the keyword appears in the cover letter
            found_synonym = False
            normalized_keyword = normalize_skill(keyword)

            # Check if keyword is a canonical skill with synonyms
            for canonical, synonyms in SKILL_SYNONYMS.items():
                if normalized_keyword == normalize_skill(canonical) or \
                   normalized_keyword in [normalize_skill(s) for s in synonyms]:
                    # Check if any synonym appears in cover letter
                    all_variants = [canonical] + synonyms
                    for variant in all_variants:
                        variant_pattern = _compile_phrase_pattern(variant.lower())
                        if variant_pattern.search(cover_letter_lower):
                            covered_keywords.append(keyword)
                            found_synonym = True
                            break
                    break

            if not found_synonym:
                missing_keywords.append(keyword)

    # Identify critical missing keywords (from must-have capabilities)
    must_have_set = set(job_profile.must_have_capabilities or [])
    missing_critical = [k for k in missing_keywords if k in must_have_set]

    # Calculate coverage
    total = len(keywords)
    covered = len(covered_keywords)
    percentage = (covered / total * 100) if total > 0 else 100.0

    # Adequate coverage is >= 60%
    adequate = percentage >= 60.0

    return ATSKeywordCoverage(
        total_keywords=total,
        keywords_covered=covered,
        coverage_percentage=round(percentage, 1),
        missing_critical_keywords=missing_critical[:5],  # Limit to top 5
        covered_keywords=covered_keywords,
        coverage_adequate=adequate
    )


def generate_outline(
    job_profile: JobProfile,
    company_profile: Optional[CompanyProfile],
    skill_gap_result: SkillGapResponse,
    user_name: str,
    referral_name: Optional[str]
) -> CoverLetterOutline:
    """
    Generate structured outline for cover letter.

    Args:
        job_profile: Target job
        company_profile: Company info if available
        skill_gap_result: Skill gap analysis
        user_name: User's name
        referral_name: Referrer name if applicable

    Returns:
        CoverLetterOutline with 4 sections
    """
    job_title = job_profile.job_title or "the position"
    company_name = company_profile.name if company_profile else None

    # Clean up job title if it contains extra info (salary, location, etc.)
    clean_job_title = job_title
    if '.' in job_title:
        clean_job_title = job_title.split('.')[0].strip()
    if ' at ' in clean_job_title.lower() and ',' in clean_job_title:
        # "AI Strategist at Perficient, Boston" -> "AI Strategist"
        clean_job_title = clean_job_title.split(' at ')[0].strip()
    if 'salary' in clean_job_title.lower():
        clean_job_title = clean_job_title.split('Salary')[0].split('salary')[0].strip().rstrip(',').rstrip('.')

    # --- Introduction ---
    # Use cover letter hooks from skill gap if available
    hooks = skill_gap_result.cover_letter_hooks or []

    if referral_name:
        intro = (
            f"{referral_name} suggested I reach out regarding the {clean_job_title} role"
            f"{f' at {company_name}' if company_name else ''}. "
        )
    elif company_name:
        intro = (
            f"I am writing to express my strong interest in the {clean_job_title} opportunity at {company_name}. "
        )
    else:
        intro = f"I am writing to express my strong interest in the {clean_job_title} position. "

    # Sprint 10E: Use key_skills if user has curated them, otherwise fall back to skill gap analysis
    if job_profile.key_skills and len(job_profile.key_skills) >= 2:
        # User has curated key skills - prioritize these
        top_skills = job_profile.key_skills[:3]
    else:
        # Fall back to skill gap analysis
        top_skills = [m.skill for m in sorted(
            skill_gap_result.matched_skills,
            key=lambda x: x.match_strength,
            reverse=True
        )[:3]]  # Get top 3 skills

    if top_skills:
        if len(top_skills) >= 3:
            intro += (
                f"With extensive experience in {top_skills[0]}, {top_skills[1]}, and {top_skills[2]}, "
                f"I bring a strong foundation aligned with this role's core requirements. "
            )
        else:
            intro += (
                f"With expertise in {' and '.join(top_skills)}, I bring a strong foundation "
                f"aligned with this role's requirements. "
            )
        # Add sentences about background and approach
        intro += (
            "My background combines strategic thinking with hands-on technical execution. "
            "I have consistently delivered results in complex environments requiring both analytical rigor and stakeholder collaboration."
        )
    else:
        intro += (
            "My background and experience position me well for this opportunity, "
            "combining strategic insight with practical implementation skills. "
            "I have a track record of delivering results in complex environments."
        )

    # --- Value Proposition ---
    # Highlight top matched skills with evidence - as SEPARATE SENTENCES
    value_sentences = []

    # Sprint 10E: Use key_skills for evidence if available
    skills_to_highlight = []
    if job_profile.key_skills and len(job_profile.key_skills) >= 2:
        # Find matched_skills that correspond to key_skills
        for key_skill in job_profile.key_skills[:3]:
            match = next(
                (m for m in skill_gap_result.matched_skills if m.skill.lower() == key_skill.lower()),
                None
            )
            if match:
                skills_to_highlight.append(match)

    # Fall back to top matched skills if no key skills or no matches found
    if not skills_to_highlight:
        skills_to_highlight = skill_gap_result.matched_skills[:3]

    for match in skills_to_highlight:
        if match.evidence:
            # Extract the bullet text after "Bullet N: " prefix
            raw_evidence = match.evidence[0].split(':')[-1].strip()
            # Remove trailing "..." if present from source truncation
            if raw_evidence.endswith('...'):
                raw_evidence = raw_evidence[:-3].strip()
            # For value proposition, prefer complete sentences over truncation
            # Only truncate very long bullets (>200 chars) to maintain readability
            evidence_summary = smart_truncate(raw_evidence, max_length=200)
            # Create a complete sentence for each skill
            sentence = f"In {match.skill}, I have demonstrated impact through {evidence_summary.lower()}"
            # Ensure sentence ends with period
            if not sentence.endswith('.'):
                sentence += '.'
            value_sentences.append(sentence)

    if not value_sentences:
        # Fallback to user advantages as separate sentences
        for adv in skill_gap_result.user_advantages[:2]:
            sentence = adv if adv.endswith('.') else adv + '.'
            value_sentences.append(sentence)

    # Join with space - each point is already a complete sentence
    value_proposition = " ".join(value_sentences) if value_sentences else (
        "I bring a combination of relevant skills and experience that would enable "
        "me to contribute effectively in this role."
    )

    # --- Alignment ---
    alignment_parts = []

    # Try to extract company name from job description if not available
    effective_company_name = company_name
    if not effective_company_name and job_profile.raw_jd_text:
        # Try to extract company name from common patterns in JD
        jd_lower = job_profile.raw_jd_text.lower()
        if ' at ' in jd_lower:
            # Pattern: "Role at Company"
            parts = job_profile.raw_jd_text.split(' at ')
            if len(parts) > 1:
                potential_company = parts[1].split(',')[0].split('.')[0].strip()
                if len(potential_company) > 2 and len(potential_company) < 50:
                    effective_company_name = potential_company

    # Company-specific alignment
    if company_profile:
        if company_profile.known_initiatives:
            alignment_parts.append(
                f"I am particularly drawn to {effective_company_name}'s work in "
                f"{company_profile.known_initiatives.split('.')[0].strip()}."
            )
        if company_profile.culture_signals:
            culture = company_profile.culture_signals[0] if company_profile.culture_signals else ""
            if culture:
                alignment_parts.append(
                    f"The {culture} culture resonates with my professional values."
                )
    elif effective_company_name:
        # Even without company profile, mention the company
        # Avoid "excited" (emotional) and "contribute to" (weak verb)
        alignment_parts.append(
            f"The opportunity to advance {effective_company_name}'s mission aligns with my career objectives."
        )

    # Address multiple core priorities from job (for better requirement coverage)
    if job_profile.core_priorities:
        priorities = job_profile.core_priorities[:2]  # Top 2 priorities
        if len(priorities) >= 2:
            alignment_parts.append(
                f"Your focus on {priorities[0].lower()} and {priorities[1].lower()} "
                f"aligns closely with my experience and career goals."
            )
        elif len(priorities) == 1:
            alignment_parts.append(
                f"Your focus on {priorities[0].lower()} aligns with my experience and interests."
            )

    # Add specific job requirements addressed
    if job_profile.must_have_capabilities:
        # Find requirements that match user's skills
        for cap in job_profile.must_have_capabilities[:5]:
            cap_lower = cap.lower()
            for match in skill_gap_result.matched_skills:
                if match.skill.lower() in cap_lower or cap_lower in match.skill.lower():
                    alignment_parts.append(
                        f"My background in {match.skill} directly addresses your need for {smart_truncate(cap, 60).lower()}."
                    )
                    break
            if len(alignment_parts) >= 4:  # Don't add too many
                break

    # Address any weak signals strategically
    if skill_gap_result.weak_signals and len(alignment_parts) < 4:
        weak = skill_gap_result.weak_signals[0]
        alignment_parts.append(
            f"While building on my {weak.skill}-adjacent experience, "
            f"I am committed to deepening expertise in this area."
        )

    alignment = " ".join(alignment_parts) if alignment_parts else (
        "My professional goals and working style align well with the requirements "
        "and culture of this role."
    )

    # --- Call to Action ---
    # Use effective_company_name which may have been extracted from JD
    # Avoid banned phrases and weak verbs like "contribute to"
    if effective_company_name:
        call_to_action = (
            f"I would welcome the opportunity to discuss how my background and skills "
            f"can advance {effective_company_name}'s strategic objectives. "
            f"My experience positions me to deliver meaningful impact to your team. "
            f"Thank you for considering my application."
        )
    else:
        call_to_action = (
            "I would welcome the opportunity to discuss how my background and experience "
            "align with your team's needs. My skills position me to deliver meaningful impact. "
            "Thank you for considering my application."
        )

    return CoverLetterOutline(
        introduction=intro,
        value_proposition=value_proposition,
        alignment=alignment,
        call_to_action=call_to_action
    )


def build_rationale(
    job_profile: JobProfile,
    company_profile: Optional[CompanyProfile],
    skill_gap_result: SkillGapResponse,
    outline: CoverLetterOutline,
    ats_coverage: ATSKeywordCoverage
) -> CoverLetterRationale:
    """
    Build rationale explaining generation decisions.

    Args:
        job_profile: Target job
        company_profile: Company info
        skill_gap_result: Skill gap analysis
        outline: Generated outline
        ats_coverage: ATS keyword analysis

    Returns:
        CoverLetterRationale explaining decisions
    """
    # Outline strategy rationale
    company_name = company_profile.name if company_profile else None

    if company_name:
        outline_strategy = (
            f"Used company-specific personalization for {company_name}, "
            f"emphasizing alignment with their known initiatives and culture. "
            f"Structured as: hook with qualifications → value demonstration → "
            f"company fit → clear call to action."
        )
    else:
        outline_strategy = (
            "Used standard professional structure without company-specific "
            "details. Emphasized transferable skills and role alignment. "
            "Structured as: role interest → value proposition → general fit → "
            "professional close."
        )

    # Tone choice rationale
    target_tone = job_profile.tone_style or "formal_corporate"
    tone_choice = (
        f"Selected {target_tone} tone based on job description analysis. "
        f"Adjusted formality level in greeting and closing to match expectations."
    )

    # Keyword strategy rationale
    if ats_coverage.coverage_adequate:
        keyword_strategy = (
            f"Incorporated {ats_coverage.keywords_covered} of {ats_coverage.total_keywords} "
            f"keywords ({ats_coverage.coverage_percentage:.0f}% coverage). "
            f"Key skills naturally woven into value proposition and alignment sections."
        )
    else:
        keyword_strategy = (
            f"Achieved {ats_coverage.coverage_percentage:.0f}% keyword coverage. "
            f"Missing critical keywords: {', '.join(ats_coverage.missing_critical_keywords[:3])}. "
            f"Consider adding explicit mentions or related experience."
        )

    # Customization notes
    customization_parts = []

    if skill_gap_result.matched_skills:
        top_match = max(skill_gap_result.matched_skills, key=lambda m: m.match_strength)
        customization_parts.append(f"Led with strongest skill match: {top_match.skill}")

    if skill_gap_result.weak_signals:
        customization_parts.append(
            f"Addressed skill gap in {skill_gap_result.weak_signals[0].skill} strategically"
        )

    recommendation = skill_gap_result.recommendation
    if recommendation == "strong_match":
        customization_parts.append("Positioned as well-qualified candidate")
    elif recommendation == "stretch_role":
        customization_parts.append("Emphasized learning agility and transferable skills")

    customization_notes = ". ".join(customization_parts) if customization_parts else (
        "Standard customization based on job requirements and user profile."
    )

    return CoverLetterRationale(
        outline_strategy=outline_strategy,
        tone_choice=tone_choice,
        keyword_strategy=keyword_strategy,
        customization_notes=customization_notes,
        structure_template="standard"  # Default to standard template
    )


def compute_quality_score(
    banned_check: BannedPhraseCheck,
    tone_compliance: ToneComplianceResult,
    ats_coverage: ATSKeywordCoverage
) -> float:
    """
    Compute overall quality score for cover letter.

    Args:
        banned_check: Banned phrase check results
        tone_compliance: Tone compliance assessment
        ats_coverage: ATS keyword coverage

    Returns:
        Quality score (0-100)
    """
    base_score = 50.0

    # Tone component (max +20)
    tone_points = tone_compliance.compliance_score * 20.0

    # ATS coverage component (max +20)
    ats_points = (ats_coverage.coverage_percentage / 100.0) * 20.0

    # Banned phrase penalty
    banned_penalty = 0.0
    for violation in banned_check.violations:
        if violation.severity == "critical":
            banned_penalty += 15.0
        elif violation.severity == "major":
            banned_penalty += 8.0
        elif violation.severity == "minor":
            banned_penalty += 2.0

    # Cap penalty at 40 points (don't go below 10)
    banned_penalty = min(banned_penalty, 40.0)

    # Bonus for no violations (+10)
    if banned_check.violations_found == 0:
        base_score += 10.0

    # Calculate final score
    quality_score = base_score + tone_points + ats_points - banned_penalty

    # Clamp to [0, 100]
    return max(0.0, min(100.0, quality_score))


# Default quality threshold from config (can be overridden)
# Sprint 8B.6: Read defaults from config.yaml
DEFAULT_QUALITY_THRESHOLD = float(_CONFIG.get('critic', {}).get('ats_score_threshold', 75.0))
DEFAULT_MAX_ITERATIONS = int(_CONFIG.get('critic', {}).get('max_iterations', 3))


async def evaluate_cover_letter(
    cover_letter_text: str,
    job_profile: JobProfile,
    company_profile: Optional[CompanyProfile],
    llm: BaseLLM,
    iteration: int = 1,
    previous_result: Optional[CoverLetterCriticResult] = None,
    quality_threshold: float = DEFAULT_QUALITY_THRESHOLD
) -> CoverLetterCriticResult:
    """
    Evaluate a cover letter draft using the critic agent.

    Performs comprehensive quality assessment including:
    - Banned phrase detection
    - Tone compliance check
    - ATS keyword coverage analysis
    - Issue aggregation and improvement suggestions

    Args:
        cover_letter_text: The cover letter draft to evaluate
        job_profile: Target job profile for context
        company_profile: Optional company profile for context
        llm: LLM instance for tone inference
        iteration: Current iteration number (1-indexed)
        previous_result: Result from previous iteration (for delta calculation)
        quality_threshold: Minimum quality score to pass (default 75)

    Returns:
        CoverLetterCriticResult with evaluation details and retry decision

    Raises:
        ValueError: If quality_threshold is not between 0 and 100
    """
    # Validate quality_threshold
    if not 0 <= quality_threshold <= 100:
        raise ValueError(f"quality_threshold must be between 0 and 100, got {quality_threshold}")

    company_name = company_profile.name if company_profile else None

    # Run quality checks
    banned_check = check_banned_phrases(cover_letter_text, company_name)
    tone_compliance = await assess_tone_compliance(cover_letter_text, job_profile, llm)
    ats_coverage = analyze_ats_keyword_coverage(cover_letter_text, job_profile)

    # Compute quality score
    quality_score = compute_quality_score(banned_check, tone_compliance, ats_coverage)

    # Aggregate issues from all checks
    issues: List[CriticIssue] = []
    retry_reasons: List[str] = []
    improvement_suggestions: List[str] = []

    # Add banned phrase issues
    for violation in banned_check.violations:
        issues.append(CriticIssue(
            category="banned_phrase",
            severity=violation.severity,
            description=f"Found banned phrase: '{violation.phrase}'",
            suggestion=f"Remove or rephrase '{violation.phrase}' in the {violation.section} section",
            section=violation.section
        ))
        if violation.severity == "critical":
            retry_reasons.append(f"Critical banned phrase: '{violation.phrase}'")
            improvement_suggestions.append(
                f"Replace '{violation.phrase}' with a more specific, non-clichéd alternative"
            )
        elif violation.severity == "major":
            retry_reasons.append(f"Major banned phrase: '{violation.phrase}'")

    # Add tone compliance issues
    if not tone_compliance.compatible:
        issues.append(CriticIssue(
            category="tone",
            severity="major",
            description=f"Tone mismatch: expected {tone_compliance.target_tone}, detected {tone_compliance.detected_tone}",
            suggestion=f"Adjust formality and language to match {tone_compliance.target_tone} tone"
        ))
        retry_reasons.append(f"Tone mismatch: {tone_compliance.detected_tone} vs expected {tone_compliance.target_tone}")
        improvement_suggestions.append(
            f"Adjust language formality to match {tone_compliance.target_tone} style"
        )
    elif tone_compliance.compliance_score < 0.70:
        issues.append(CriticIssue(
            category="tone",
            severity="minor",
            description=f"Tone could be better aligned (score: {tone_compliance.compliance_score:.2f})",
            suggestion="Fine-tune language to better match target tone"
        ))

    # Add ATS coverage issues
    if not ats_coverage.coverage_adequate:
        issues.append(CriticIssue(
            category="ats_coverage",
            severity="major",
            description=f"ATS keyword coverage below threshold: {ats_coverage.coverage_percentage:.1f}%",
            suggestion=f"Incorporate missing keywords: {', '.join(ats_coverage.missing_critical_keywords[:3])}"
        ))
        retry_reasons.append(f"Low ATS coverage: {ats_coverage.coverage_percentage:.1f}%")
        if ats_coverage.missing_critical_keywords:
            improvement_suggestions.append(
                f"Add missing critical keywords: {', '.join(ats_coverage.missing_critical_keywords[:3])}"
            )
    elif ats_coverage.coverage_percentage < 70:
        issues.append(CriticIssue(
            category="ats_coverage",
            severity="minor",
            description=f"ATS coverage could be improved: {ats_coverage.coverage_percentage:.1f}%",
            suggestion="Consider adding more relevant keywords naturally"
        ))

    # Determine pass/fail
    has_critical_issues = any(i.severity == "critical" for i in issues)
    passed = quality_score >= quality_threshold and not has_critical_issues

    # Determine if we should retry
    # Don't retry if:
    # 1. Already passed
    # 2. Reached max iterations (caller handles this)
    # 3. Score is very low (unlikely to improve enough)
    # 4. No actionable improvements identified
    should_retry = (
        not passed and
        len(improvement_suggestions) > 0 and
        quality_score >= 30.0  # Below 30 is too broken to fix
    )

    # Calculate score delta from previous iteration
    score_delta = None
    issues_resolved: List[str] = []
    if previous_result is not None:
        score_delta = quality_score - previous_result.quality_score

        # Find issues that were resolved
        previous_descriptions = {i.description for i in previous_result.issues}
        current_descriptions = {i.description for i in issues}
        resolved = previous_descriptions - current_descriptions
        issues_resolved = list(resolved)[:5]  # Limit to 5

        # If score got worse or stayed same after multiple tries, reduce retry incentive
        if score_delta <= 0 and iteration >= 2:
            should_retry = False

    return CoverLetterCriticResult(
        iteration=iteration,
        quality_score=quality_score,
        passed=passed,
        should_retry=should_retry,
        banned_phrase_check=banned_check,
        tone_compliance=tone_compliance,
        ats_keyword_coverage=ats_coverage,
        issues=issues,
        retry_reasons=retry_reasons,
        improvement_suggestions=improvement_suggestions,
        score_delta=score_delta,
        issues_resolved=issues_resolved,
        evaluated_at=datetime.now(timezone.utc).isoformat()
    )


def analyze_requirement_coverage(
    cover_letter_text: str,
    job_profile: JobProfile
) -> List[RequirementCoverage]:
    """
    Analyze how well the cover letter addresses top job requirements.

    Per style guide Section 6: identify top 2-3 JD requirements and address them explicitly.

    Args:
        cover_letter_text: Generated cover letter text
        job_profile: Job profile with core_priorities and must_have_capabilities

    Returns:
        List of RequirementCoverage objects for top requirements
    """
    requirements_covered = []
    text_lower = cover_letter_text.lower()

    # Get top requirements from job profile
    top_requirements = []

    # Add core priorities (top 2)
    if job_profile.core_priorities:
        top_requirements.extend(job_profile.core_priorities[:2])

    # Add must-have capabilities (top 1)
    if job_profile.must_have_capabilities:
        for cap in job_profile.must_have_capabilities[:1]:
            if cap not in top_requirements:
                top_requirements.append(cap)

    # Limit to top 3
    top_requirements = top_requirements[:3]

    for requirement in top_requirements:
        req_lower = requirement.lower()

        # First try exact phrase match with word boundaries
        phrase_pattern = _compile_phrase_pattern(req_lower)
        covered = bool(phrase_pattern.search(text_lower))

        # If no exact match, check for significant word overlap with word boundaries
        if not covered:
            req_words = [w for w in req_lower.split() if len(w) >= 3]
            if req_words:
                matching_count = 0
                for word in req_words:
                    word_pattern = _compile_phrase_pattern(word)
                    if word_pattern.search(text_lower):
                        matching_count += 1
                # Require at least 60% of significant words to match
                covered = matching_count >= len(req_words) * 0.6

        # Find evidence sentence if covered
        evidence = None
        if covered:
            sentences = cover_letter_text.replace('\n', ' ').split('.')
            for sentence in sentences:
                sentence_lower = sentence.lower()
                # Look for the sentence containing the requirement words
                req_words = [w for w in req_lower.split() if len(w) >= 3]
                if any(w in sentence_lower for w in req_words[:2]):
                    evidence = sentence.strip()[:150]
                    if evidence and not evidence.endswith('.'):
                        evidence += "..."
                    break

        requirements_covered.append(RequirementCoverage(
            requirement=requirement,
            covered=covered,
            evidence=evidence
        ))

    return requirements_covered


def generate_mission_alignment_summary(
    cover_letter_text: str,
    company_profile: Optional[CompanyProfile]
) -> Optional[str]:
    """
    Generate summary of how the letter aligns with company mission/positioning.

    Per style guide Section 6: Reference company mission/approach specifically.

    Args:
        cover_letter_text: Generated cover letter text
        company_profile: Company profile with mission, known_initiatives, culture_signals

    Returns:
        Summary string or None if no company profile
    """
    if not company_profile:
        return None

    alignment_parts = []
    text_lower = cover_letter_text.lower()

    # Check if company name is mentioned
    if company_profile.name and company_profile.name.lower() in text_lower:
        alignment_parts.append(f"References {company_profile.name} by name")

    # Check for mission/initiative keywords
    if company_profile.known_initiatives:
        initiative_words = company_profile.known_initiatives.lower().split()[:5]
        matched = [w for w in initiative_words if len(w) > 4 and w in text_lower]
        if matched:
            alignment_parts.append(f"Addresses company initiatives ({', '.join(matched[:3])})")

    # Check for culture signal alignment
    if company_profile.culture_signals:
        for signal in company_profile.culture_signals[:2]:
            if signal.lower() in text_lower:
                alignment_parts.append(f"Aligns with '{signal}' culture")
                break

    if alignment_parts:
        return ". ".join(alignment_parts) + "."
    else:
        return "Company positioning not explicitly addressed in cover letter."


async def generate_cover_letter(
    job_profile_id: int,
    user_id: int,
    db: Session,
    company_profile_id: Optional[int] = None,
    context_notes: Optional[str] = None,
    referral_name: Optional[str] = None,
    company_name: Optional[str] = None,
    llm: Optional[BaseLLM] = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
    enable_learning: bool = True
) -> GeneratedCoverLetter:
    """
    Generate tailored cover letter for job application with critic iteration loop.

    Main orchestrator for cover letter generation. Analyzes skill gaps,
    generates structured outline, produces draft, runs critic evaluation,
    and iteratively revises until quality threshold is met or max iterations reached.

    Args:
        job_profile_id: Target job profile ID
        user_id: User ID
        db: Database session
        company_profile_id: Optional company profile ID
        context_notes: Optional user-provided context
        referral_name: Optional referrer name
        company_name: Optional company name override (takes priority over company_profile)
        llm: Optional LLM instance (defaults to MockLLM)
        max_iterations: Maximum critic iterations (default 3)
        quality_threshold: Minimum quality score to pass (default 75)
        enable_learning: Enable learning from approved outputs (default True)

    Returns:
        GeneratedCoverLetter with complete analysis and iteration history

    Raises:
        ValueError: If user, job profile, or company profile not found
    """
    # Initialize LLM (uses ClaudeLLM if ANTHROPIC_API_KEY is set, otherwise MockLLM)
    if llm is None:
        llm = create_llm()

    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Fetch job profile
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile:
        raise ValueError(f"Job profile {job_profile_id} not found")

    # Check for required data
    if not job_profile.extracted_skills:
        raise ValueError(
            f"Job profile {job_profile_id} has no extracted skills. "
            "Please parse the job description first."
        )

    # Fetch company profile if provided
    company_profile: Optional[CompanyProfile] = None
    if company_profile_id:
        company_profile = db.query(CompanyProfile).filter(
            CompanyProfile.id == company_profile_id
        ).first()
        if not company_profile:
            raise ValueError(f"Company profile {company_profile_id} not found")

    # Run skill gap analysis
    skill_gap_result = await analyze_skill_gap(
        job_profile_id=job_profile_id,
        user_id=user_id,
        db=db
    )

    # Sprint 11: Run capability cluster analysis for strategic positioning
    cluster_analysis: Optional[CapabilityClusterAnalysis] = None
    try:
        cluster_analysis = await get_cluster_analysis(
            job_profile_id=job_profile_id,
            user_id=user_id,
            db=db,
            use_mock=False  # Use real LLM when ANTHROPIC_API_KEY is set
        )
        if cluster_analysis:
            logger.info(
                f"Cluster analysis: {len(cluster_analysis.clusters)} clusters, "
                f"overall score: {cluster_analysis.overall_match_score:.1f}%"
            )
    except Exception as e:
        logger.warning(f"Cluster analysis failed (continuing without): {e}")

    # Sprint 8B.2: Retrieve similar approved cover letter paragraphs for learning
    similar_approved_paragraphs = []
    if enable_learning:
        try:
            from services.embeddings import create_embedding_service
            from services.vector_store import create_vector_store
            from services.output_retrieval import (
                retrieve_similar_cover_letter_paragraphs,
                format_examples_for_prompt
            )

            embedding_service = create_embedding_service(use_mock=False)
            vector_store = create_vector_store(use_mock=False)

            similar_approved_paragraphs = await retrieve_similar_cover_letter_paragraphs(
                job_profile=job_profile,
                embedding_service=embedding_service,
                vector_store=vector_store,
                user_id=user_id,
                limit=3,
                min_quality_score=0.70
            )

            if similar_approved_paragraphs:
                logger.info(f"Retrieved {len(similar_approved_paragraphs)} similar approved paragraphs for job {job_profile_id}")
        except Exception as e:
            logger.warning(f"Failed to retrieve similar approved paragraphs (continuing without): {e}")

    # Generate outline
    outline = generate_outline(
        job_profile=job_profile,
        company_profile=company_profile,
        skill_gap_result=skill_gap_result,
        user_name=user.full_name,
        referral_name=referral_name
    )

    # Build job and company context for LLM
    job_context = {
        "title": job_profile.job_title,
        "priorities": job_profile.core_priorities or [],
        "skills": job_profile.extracted_skills or [],
        "must_have": job_profile.must_have_capabilities or [],
    }

    # Sprint 11: Add cluster analysis context for strategic positioning
    if cluster_analysis:
        job_context["cluster_positioning"] = cluster_analysis.positioning_summary
        job_context["key_strengths"] = cluster_analysis.key_strengths
        job_context["critical_gaps"] = cluster_analysis.critical_gaps
        job_context["cluster_recommendation"] = cluster_analysis.recommendation
        # Add top cluster names with their match percentages
        job_context["capability_clusters"] = [
            {"name": c.name, "match": c.match_percentage, "importance": c.importance}
            for c in cluster_analysis.clusters[:4]  # Top 4 clusters
        ]

    # Sanitize context_notes before passing to LLM
    sanitized_context_notes = None
    if context_notes:
        # Strip whitespace and enforce max length
        sanitized_context_notes = context_notes.strip()[:2000]
        # Remove any control characters
        sanitized_context_notes = ''.join(c for c in sanitized_context_notes if c.isprintable() or c in '\n\t')

    # Build examples context from approved paragraphs (Sprint 8B.2)
    examples_context = ""
    if similar_approved_paragraphs:
        examples_context = format_examples_for_prompt(
            similar_outputs=similar_approved_paragraphs,
            max_examples=2,
            include_quality_score=True
        )

    # Use company_name override if provided, otherwise fall back to company_profile
    effective_company_name = company_name or (company_profile.name if company_profile else None)

    company_context = {
        "name": effective_company_name,
        "initiatives": company_profile.known_initiatives if company_profile else None,
        "culture": company_profile.culture_signals if company_profile else None,
        "referral_name": referral_name,
        "context_notes": sanitized_context_notes,
        "examples_context": examples_context,
    }

    # Generate initial cover letter draft
    target_tone = job_profile.tone_style or "formal_corporate"
    draft = await llm.generate_cover_letter(
        outline={
            "introduction": outline.introduction,
            "value_proposition": outline.value_proposition,
            "alignment": outline.alignment,
            "call_to_action": outline.call_to_action,
        },
        job_context=job_context,
        company_context=company_context,
        tone=target_tone,
        user_name=user.full_name,
        max_words=265  # Target: 250-275 words
    )

    # =============================================
    # CRITIC ITERATION LOOP
    # =============================================
    iteration_history: List[CoverLetterCriticResult] = []
    current_draft = draft
    previous_result: Optional[CoverLetterCriticResult] = None

    for iteration in range(1, max_iterations + 1):
        # Evaluate current draft
        critic_result = await evaluate_cover_letter(
            cover_letter_text=current_draft,
            job_profile=job_profile,
            company_profile=company_profile,
            llm=llm,
            iteration=iteration,
            previous_result=previous_result,
            quality_threshold=quality_threshold
        )

        # Store in history
        iteration_history.append(critic_result)

        # Check if we're done
        if critic_result.passed:
            # Quality threshold met, exit loop
            break

        if not critic_result.should_retry:
            # Critic determined no point in retrying
            break

        if iteration >= max_iterations:
            # Max iterations reached
            break

        # Prepare feedback for revision
        critic_feedback = {
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                    "section": issue.section
                }
                for issue in critic_result.issues
            ],
            "improvement_suggestions": critic_result.improvement_suggestions,
            "quality_score": critic_result.quality_score,
            "retry_reasons": critic_result.retry_reasons
        }

        # Request revision from LLM
        current_draft = await llm.revise_cover_letter(
            current_draft=current_draft,
            critic_feedback=critic_feedback,
            job_context=job_context,
            company_context=company_context,
            tone=target_tone,
            user_name=user.full_name,
            max_words=265  # Target: 250-275 words
        )

        previous_result = critic_result

    # =============================================
    # FINALIZE RESULTS
    # =============================================
    final_critic_result = iteration_history[-1] if iteration_history else None
    iterations_used = len(iteration_history)

    # Use final critic result's checks for the response
    if final_critic_result:
        banned_check = final_critic_result.banned_phrase_check
        tone_compliance = final_critic_result.tone_compliance
        ats_coverage = final_critic_result.ats_keyword_coverage
        quality_score = final_critic_result.quality_score
        critic_passed = final_critic_result.passed
    else:
        # Fallback if no critic run (shouldn't happen)
        company_name = company_profile.name if company_profile else None
        banned_check = check_banned_phrases(current_draft, company_name)
        tone_compliance = await assess_tone_compliance(current_draft, job_profile, llm)
        ats_coverage = analyze_ats_keyword_coverage(current_draft, job_profile)
        quality_score = compute_quality_score(banned_check, tone_compliance, ats_coverage)
        critic_passed = quality_score >= quality_threshold

    # Build rationale
    rationale = build_rationale(
        job_profile=job_profile,
        company_profile=company_profile,
        skill_gap_result=skill_gap_result,
        outline=outline,
        ats_coverage=ats_coverage
    )

    # Analyze requirement coverage (style guide Section 6)
    requirements_covered = analyze_requirement_coverage(current_draft, job_profile)

    # Generate mission alignment summary (style guide Section 6)
    mission_alignment_summary = generate_mission_alignment_summary(current_draft, company_profile)

    # Extract ATS keywords used
    ats_keywords_used = ats_coverage.covered_keywords

    return GeneratedCoverLetter(
        job_profile_id=job_profile_id,
        user_id=user_id,
        company_profile_id=company_profile_id,
        company_name=effective_company_name,
        job_title=job_profile.job_title,
        draft_cover_letter=current_draft,
        outline=outline,
        banned_phrase_check=banned_check,
        tone_compliance=tone_compliance,
        ats_keyword_coverage=ats_coverage,
        rationale=rationale,
        generated_at=datetime.now(timezone.utc).isoformat(),
        quality_score=quality_score,
        requirements_covered=requirements_covered,
        mission_alignment_summary=mission_alignment_summary,
        ats_keywords_used=ats_keywords_used,
        iterations_used=iterations_used,
        final_critic_result=final_critic_result,
        iteration_history=iteration_history,
        critic_passed=critic_passed
    )
