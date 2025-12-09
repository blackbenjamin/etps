"""
Capability Cluster Extraction Service (Sprint 11)

Uses LLM to extract capability clusters from job descriptions,
with caching to reduce API costs.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from schemas.capability import (
    CapabilityCluster,
    ComponentSkill,
    EvidenceSkill,
    CapabilityClusterAnalysis
)
from services.capability_ontology import (
    CAPABILITY_ONTOLOGY,
    get_ontology_summary,
    get_clusters_by_keywords,
    get_clusters_by_role_indicators
)
from services.llm import create_llm

logger = logging.getLogger(__name__)

# Cache TTL in hours
CLUSTER_CACHE_TTL_HOURS = 24


def compute_jd_cache_key(jd_text: str, job_title: str) -> str:
    """
    Generate SHA256 hash of normalized JD text + title for cache lookup.
    """
    # Normalize: lowercase, remove extra whitespace, remove punctuation
    normalized_jd = re.sub(r'\s+', ' ', jd_text.lower().strip())
    normalized_title = job_title.lower().strip()
    content = f"{normalized_title}||{normalized_jd}"
    return hashlib.sha256(content.encode()).hexdigest()


def is_cache_valid(cache_timestamp: Optional[datetime]) -> bool:
    """Check if cached analysis is still valid based on TTL."""
    if cache_timestamp is None:
        return False
    expiry = cache_timestamp + timedelta(hours=CLUSTER_CACHE_TTL_HOURS)
    return datetime.utcnow() < expiry


async def extract_capability_clusters(
    jd_text: str,
    job_title: str,
    seniority: Optional[str] = None,
    extracted_skills: Optional[List[str]] = None,
    use_mock: bool = False
) -> List[CapabilityCluster]:
    """
    Extract 4-6 capability clusters from a job description using LLM.

    Args:
        jd_text: Full job description text
        job_title: Job title
        seniority: Optional seniority level (e.g., "Senior", "Director")
        extracted_skills: Optional list of already-extracted skills
        use_mock: If True, use mock extraction instead of LLM

    Returns:
        List of CapabilityCluster objects
    """
    if use_mock:
        return _mock_extract_clusters(jd_text, job_title, extracted_skills)

    try:
        clusters = await _llm_extract_clusters(jd_text, job_title, seniority, extracted_skills)
        return clusters
    except Exception as e:
        logger.warning(f"LLM extraction failed, falling back to mock: {e}")
        return _mock_extract_clusters(jd_text, job_title, extracted_skills)


async def _llm_extract_clusters(
    jd_text: str,
    job_title: str,
    seniority: Optional[str],
    extracted_skills: Optional[List[str]]
) -> List[CapabilityCluster]:
    """
    Use LLM to extract capability clusters from JD.
    """
    llm_service = create_llm()

    # Build context
    skills_context = ""
    if extracted_skills:
        skills_context = f"\nAlready identified skills: {', '.join(extracted_skills[:20])}"

    ontology_summary = get_ontology_summary()

    prompt = f"""Analyze this job description and extract 4-6 capability clusters that represent the core competencies required for the role.

Job Title: {job_title}
Seniority: {seniority or 'Not specified'}
{skills_context}

Job Description:
{jd_text[:6000]}  # Truncate to avoid token limits

Reference Ontology (use as guidance, adapt as needed):
{ontology_summary}

For each capability cluster, provide:
1. name: A clear name (e.g., "AI & Data Strategy", "Solution Architecture")
2. description: 1-2 sentence description of what this capability entails for THIS role
3. importance: "critical", "important", or "nice-to-have"
4. component_skills: List of 3-8 specific skills/competencies within this cluster
   - Each with: name, required (true/false)
5. evidence_keywords: Specific technologies/tools that demonstrate this capability

Return valid JSON in this exact format:
{{
  "clusters": [
    {{
      "name": "Cluster Name",
      "description": "Description of capability...",
      "importance": "critical",
      "component_skills": [
        {{"name": "Specific skill", "required": true}},
        {{"name": "Another skill", "required": false}}
      ],
      "evidence_keywords": ["Keyword1", "Keyword2"]
    }}
  ]
}}

Focus on:
- Strategic capabilities, not just technical skills
- Compound skills that combine multiple competencies
- Role-specific context and seniority level
- Distinguishing must-haves from nice-to-haves
"""

    try:
        response = await llm_service.generate(prompt)
        clusters = _parse_llm_response(response)
        return clusters
    except Exception as e:
        logger.error(f"LLM cluster extraction failed: {e}")
        raise


def _parse_llm_response(response: str) -> List[CapabilityCluster]:
    """
    Parse LLM JSON response into CapabilityCluster objects.
    """
    # Try to extract JSON from response
    try:
        # Handle markdown code blocks
        if "```json" in response:
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)
        elif "```" in response:
            json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                response = json_match.group(1)

        data = json.loads(response)
        clusters_data = data.get("clusters", [])

        clusters = []
        for cd in clusters_data:
            # Parse component skills
            component_skills = []
            for cs in cd.get("component_skills", []):
                if isinstance(cs, str):
                    component_skills.append(ComponentSkill(name=cs, required=True))
                elif isinstance(cs, dict):
                    component_skills.append(ComponentSkill(
                        name=cs.get("name", ""),
                        required=cs.get("required", True),
                        description=cs.get("description")
                    ))

            # Parse evidence keywords into EvidenceSkill objects
            evidence_skills = []
            for ek in cd.get("evidence_keywords", []):
                if isinstance(ek, str):
                    evidence_skills.append(EvidenceSkill(name=ek, category="tech"))

            # Assign evidence skills to first component that doesn't have any
            if evidence_skills and component_skills:
                for comp in component_skills:
                    if not comp.evidence_skills:
                        comp.evidence_skills = evidence_skills
                        break

            cluster = CapabilityCluster(
                name=cd.get("name", "Unknown Cluster"),
                description=cd.get("description", ""),
                importance=cd.get("importance", "important"),
                component_skills=component_skills,
                gaps=cd.get("gaps", [])
            )
            clusters.append(cluster)

        return clusters

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        logger.debug(f"Response was: {response[:500]}")
        raise ValueError(f"Invalid JSON from LLM: {e}")


def _keyword_in_context(keyword: str, text: str) -> bool:
    """
    Check if keyword appears in text in a meaningful context.
    Uses word boundaries and filters out false positives like URLs and benefits sections.
    """
    import re
    text_lower = text.lower()
    kw_lower = keyword.lower()

    # Use word boundaries to avoid partial matches (e.g., "ehr" in "hrportal.ehr.com")
    pattern = r'\b' + re.escape(kw_lower) + r'\b'
    matches = list(re.finditer(pattern, text_lower))

    if not matches:
        return False

    # Check each match to filter out false positives
    for match in matches:
        start = max(0, match.start() - 100)
        end = min(len(text_lower), match.end() + 100)
        context = text_lower[start:end]

        # Skip if in benefits/insurance context
        benefits_indicators = ['insurance', 'dental', 'vision', '401k', 'retirement', 'vacation', 'pto', 'benefits include']
        if any(ind in context for ind in benefits_indicators):
            continue

        # Skip if appears to be in a URL
        if '.com/' in context or 'http' in context or 'www.' in context:
            continue

        # This match is in a meaningful context
        return True

    return False


def _mock_extract_clusters(
    jd_text: str,
    job_title: str,
    extracted_skills: Optional[List[str]] = None
) -> List[CapabilityCluster]:
    """
    Mock cluster extraction for testing and fallback.
    Uses ontology matching based on keywords and job title.
    """
    clusters = []
    jd_lower = jd_text.lower()
    job_title_lower = job_title.lower()

    # Domain clusters require stricter matching - need domain-specific keywords
    DOMAIN_CLUSTERS = {
        "Healthcare & Life Sciences Domain",
        "Financial Services Domain",
        "Transportation & Mobility Domain",
        "Critical Infrastructure Domain"
    }

    # Keywords that are too generic to indicate domain expertise
    GENERIC_KEYWORDS = {"compliance", "risk", "data", "analytics", "systems", "management"}

    # Find matching clusters from ontology
    matched_cluster_names = set()

    # Match by role indicators in job title
    title_matches = get_clusters_by_role_indicators(job_title)
    matched_cluster_names.update(title_matches[:3])

    # Match by extracted skills
    if extracted_skills:
        skill_matches = get_clusters_by_keywords(extracted_skills)
        matched_cluster_names.update(skill_matches[:4])

    # Match by JD keywords with stricter rules for domain clusters
    for cluster_name, cluster_data in CAPABILITY_ONTOLOGY.items():
        evidence_keywords = cluster_data.get("evidence_keywords", [])

        if cluster_name in DOMAIN_CLUSTERS:
            # Domain clusters need domain-SPECIFIC keywords in MEANINGFUL context
            # (not in benefits section, URLs, etc.)
            specific_matches = sum(
                1 for kw in evidence_keywords
                if kw.lower() not in GENERIC_KEYWORDS and _keyword_in_context(kw, jd_text)
            )
            # Also check if domain indicator is in job title
            role_indicators = cluster_data.get("role_indicators", [])
            title_match = any(ind in job_title_lower for ind in role_indicators)

            # Only add domain cluster if: title match OR 2+ domain-specific keywords in meaningful context
            if title_match or specific_matches >= 2:
                matched_cluster_names.add(cluster_name)
        else:
            # Non-domain clusters use context-aware matching too
            matches = sum(1 for kw in evidence_keywords if _keyword_in_context(kw, jd_text))
            if matches >= 2:
                matched_cluster_names.add(cluster_name)

    # Limit to 6 clusters
    selected_names = list(matched_cluster_names)[:6]

    # If we have less than 4, add common ones
    if len(selected_names) < 4:
        default_clusters = ["Technical Leadership", "Cross-Functional Collaboration"]
        for dc in default_clusters:
            if dc not in selected_names and len(selected_names) < 4:
                selected_names.append(dc)

    # Build cluster objects from ontology
    for cluster_name in selected_names:
        if cluster_name not in CAPABILITY_ONTOLOGY:
            continue

        ontology_data = CAPABILITY_ONTOLOGY[cluster_name]

        # Create component skills
        component_skills = []
        for i, skill_name in enumerate(ontology_data.get("component_skills", [])[:6]):
            # Create evidence skills from keywords
            evidence_skills = []
            for kw in ontology_data.get("evidence_keywords", [])[:3]:
                evidence_skills.append(EvidenceSkill(
                    name=kw,
                    category="tech",
                    matched=kw.lower() in jd_lower
                ))

            component_skills.append(ComponentSkill(
                name=skill_name,
                required=i < 3,  # First 3 are required
                evidence_skills=evidence_skills if i == 0 else []
            ))

        # Determine importance based on position and ontology
        importance = ontology_data.get("typical_importance", "important")

        cluster = CapabilityCluster(
            name=cluster_name,
            description=ontology_data.get("description", ""),
            importance=importance,
            component_skills=component_skills,
            match_percentage=0.0,  # Will be calculated by evidence mapper
            gaps=[],
            positioning=None
        )
        clusters.append(cluster)

    # Sort by importance
    importance_order = {"critical": 0, "important": 1, "nice-to-have": 2}
    clusters.sort(key=lambda c: importance_order.get(c.importance, 1))

    return clusters


def calculate_cluster_importance(
    cluster: CapabilityCluster,
    jd_text: str,
    must_have_skills: List[str],
    nice_to_have_skills: List[str]
) -> str:
    """
    Calculate the importance of a cluster based on JD analysis.
    """
    jd_lower = jd_text.lower()
    cluster_keywords = []

    # Collect all keywords from cluster
    for comp in cluster.component_skills:
        cluster_keywords.append(comp.name.lower())
        for ev in comp.evidence_skills:
            cluster_keywords.append(ev.name.lower())

    # Check for critical indicators
    critical_phrases = ["required", "must have", "essential", "mandatory"]
    nice_phrases = ["preferred", "nice to have", "bonus", "plus"]

    critical_score = 0
    nice_score = 0

    for kw in cluster_keywords:
        # Check context around keyword in JD
        kw_pattern = re.escape(kw)
        for match in re.finditer(kw_pattern, jd_lower):
            start = max(0, match.start() - 200)
            end = min(len(jd_lower), match.end() + 200)
            context = jd_lower[start:end]

            if any(phrase in context for phrase in critical_phrases):
                critical_score += 1
            if any(phrase in context for phrase in nice_phrases):
                nice_score += 1

    # Also check must_have vs nice_to_have lists
    for kw in cluster_keywords:
        if any(kw in mh.lower() for mh in must_have_skills):
            critical_score += 2
        if any(kw in nth.lower() for nth in nice_to_have_skills):
            nice_score += 1

    if critical_score > nice_score and critical_score >= 2:
        return "critical"
    elif nice_score > critical_score:
        return "nice-to-have"
    else:
        return "important"


async def get_or_extract_clusters(
    job_profile,
    db: Session,
    force_refresh: bool = False,
    use_mock: bool = True  # Default to mock for now
) -> Tuple[List[CapabilityCluster], bool]:
    """
    Get cached clusters or extract new ones.

    Args:
        job_profile: JobProfile ORM object
        db: Database session
        force_refresh: If True, bypass cache
        use_mock: If True, use mock extraction

    Returns:
        Tuple of (clusters, was_cached)
    """
    # Check cache
    if not force_refresh and job_profile.capability_clusters:
        if is_cache_valid(job_profile.capability_analysis_timestamp):
            # Parse cached clusters
            try:
                clusters = [
                    CapabilityCluster(**c) for c in job_profile.capability_clusters
                ]
                return clusters, True
            except Exception as e:
                logger.warning(f"Failed to parse cached clusters: {e}")

    # Extract new clusters
    clusters = await extract_capability_clusters(
        jd_text=job_profile.raw_jd_text,
        job_title=job_profile.job_title,
        seniority=job_profile.seniority,
        extracted_skills=job_profile.extracted_skills,
        use_mock=use_mock
    )

    # Update importance based on JD analysis
    must_have = job_profile.must_have_capabilities or []
    nice_to_have = job_profile.nice_to_have_capabilities or []

    for cluster in clusters:
        cluster.importance = calculate_cluster_importance(
            cluster, job_profile.raw_jd_text, must_have, nice_to_have
        )

    # Cache results
    cache_key = compute_jd_cache_key(job_profile.raw_jd_text, job_profile.job_title)
    job_profile.capability_clusters = [c.model_dump() for c in clusters]
    job_profile.capability_cluster_cache_key = cache_key
    job_profile.capability_analysis_timestamp = datetime.utcnow()
    db.commit()

    return clusters, False


# Export
__all__ = [
    "extract_capability_clusters",
    "compute_jd_cache_key",
    "is_cache_valid",
    "get_or_extract_clusters",
    "calculate_cluster_importance",
    "CLUSTER_CACHE_TTL_HOURS"
]
