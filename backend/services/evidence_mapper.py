"""
Evidence Mapper Service (Sprint 11)

Maps resume bullets to capability clusters to calculate match percentages
and identify gaps.
"""

import logging
import re
from typing import List, Dict, Set, Tuple, Optional, Any

from sqlalchemy.orm import Session

from db.models import Bullet, User, Experience, Engagement
from schemas.capability import (
    CapabilityCluster,
    ComponentSkill,
    EvidenceSkill,
    CapabilityClusterAnalysis,
    EvidenceMapping
)
from services.capability_ontology import CAPABILITY_ONTOLOGY

logger = logging.getLogger(__name__)


def get_user_bullets(user_id: int, db: Session) -> List[Bullet]:
    """
    Get all non-retired bullets for a user.
    """
    return db.query(Bullet).filter(
        Bullet.user_id == user_id,
        Bullet.retired == False
    ).all()


def extract_bullet_keywords(bullet: Bullet) -> Set[str]:
    """
    Extract keywords from a bullet for matching.
    Returns lowercase keywords from text and tags.
    Includes both full phrases AND individual significant words for fuzzy matching.
    """
    keywords = set()

    # Extract from text (basic word extraction)
    if bullet.text:
        # Extract words of 3+ chars
        words = re.findall(r'\b[A-Za-z]{3,}\b', bullet.text)
        keywords.update(w.lower() for w in words)

        # Also look for common tech patterns
        tech_patterns = [
            r'\bAWS\b', r'\bAzure\b', r'\bGCP\b', r'\bAI\b', r'\bML\b',
            r'\bAPI\b', r'\bETL\b', r'\bCI/CD\b', r'\bSQL\b', r'\bNoSQL\b'
        ]
        for pattern in tech_patterns:
            if re.search(pattern, bullet.text, re.IGNORECASE):
                match = re.search(pattern, bullet.text, re.IGNORECASE)
                if match:
                    keywords.add(match.group().lower())

    # Extract from tags - include BOTH full tag AND individual words
    if bullet.tags:
        for tag in bullet.tags:
            # Add full tag
            keywords.add(tag.lower())
            # Also add variations (e.g., "machine_learning" -> "machine learning")
            keywords.add(tag.lower().replace('_', ' '))
            # Add individual words from tag for fuzzy matching
            # (e.g., "Program Management" -> "program", "management")
            for word in tag.lower().replace('_', ' ').split():
                if len(word) >= 3:
                    keywords.add(word)

    return keywords


def compute_keyword_overlap(
    cluster_keywords: Set[str],
    bullet_keywords: Set[str]
) -> float:
    """
    Compute overlap score between cluster and bullet keywords.
    Returns 0-1 score.
    """
    if not cluster_keywords or not bullet_keywords:
        return 0.0

    # Normalize keywords
    cluster_norm = {k.lower().strip() for k in cluster_keywords}
    bullet_norm = {k.lower().strip() for k in bullet_keywords}

    # Direct match
    direct_overlap = cluster_norm & bullet_norm

    # Partial match (substring matching)
    partial_matches = 0
    for ck in cluster_norm:
        for bk in bullet_norm:
            if len(ck) > 3 and len(bk) > 3:
                if ck in bk or bk in ck:
                    partial_matches += 0.5

    overlap_count = len(direct_overlap) + partial_matches
    max_possible = len(cluster_norm)

    return min(1.0, overlap_count / max_possible) if max_possible > 0 else 0.0


def _get_skill_synonyms() -> Dict[str, Set[str]]:
    """Get common skill synonyms for better matching (bidirectional)."""
    # Define base synonyms - include verb/noun forms
    base_synonyms = {
        # Program/Project management
        "program": {"project", "portfolio", "initiative", "initiatives"},
        "project": {"program", "initiative", "initiatives"},
        "management": {"leadership", "oversight", "coordination", "directing", "governance", "managing", "managed", "led", "leading"},
        "leadership": {"management", "lead", "leading", "directing", "led", "directed", "oversaw"},

        # Collaboration
        "collaboration": {"teamwork", "coordination", "partnership", "cross-functional", "collaborative", "collaborating", "partnered"},
        "cross-team": {"cross-functional", "interdepartmental", "teams", "multiple teams"},
        "cross-functional": {"cross-team", "interdepartmental", "collaboration", "across teams"},
        "team": {"teams", "cross-team", "cross-functional"},
        "teams": {"team", "cross-team"},

        # Stakeholder/Communication (expanded)
        "stakeholder": {"client", "customer", "partner", "executive", "stakeholders", "executives", "leadership", "c-suite", "senior"},
        "stakeholders": {"stakeholder", "clients", "executives", "partners", "leadership"},
        "communication": {"presentation", "reporting", "articulation", "communicating", "communicated", "briefed", "briefing", "presented"},
        "presentation": {"presenting", "presented", "briefing", "briefed", "communication", "demo", "demonstration"},
        "presentations": {"presentation", "presenting", "presented", "briefings"},
        "executive": {"executives", "leadership", "c-suite", "senior", "vp", "director", "ceo", "cto", "cio"},
        "facilitation": {"facilitated", "facilitating", "led", "conducted", "moderated", "workshop"},
        "reporting": {"reports", "report", "dashboards", "status updates", "briefings"},

        # Vendor management
        "vendor": {"supplier", "partner", "third-party", "contractor", "vendors", "suppliers"},
        "evaluation": {"assessment", "analysis", "review", "selection", "evaluating", "evaluated", "assessed", "analyzed"},

        # Planning/Strategy
        "planning": {"strategy", "roadmap", "design", "planned", "plan", "designed", "architected"},
        "coordination": {"collaboration", "alignment", "orchestration", "management", "coordinating", "coordinated", "orchestrated"},
        "coordinated": {"coordination", "coordinating", "orchestrated", "managed"},
        "alignment": {"coordination", "collaboration", "synchronization", "aligned", "aligning"},
        "governance": {"management", "oversight", "compliance", "governing", "policies", "standards"},

        # Technical/Architecture
        "architecture": {"architected", "designed", "design", "architecting", "architectural"},
        "architected": {"architecture", "designed", "built"},
        "decisions": {"decision-making", "decided", "determining", "defined", "established"},

        # Requirements/Analysis
        "requirements": {"requirement", "specs", "specifications", "needs", "elicitation", "gathering"},
        "stories": {"story", "user stories", "requirements", "epics"},
        "user": {"customer", "client", "end-user"},
        "criteria": {"acceptance", "definition", "standards"},
        "acceptance": {"criteria", "validation", "verification"},
        "prototyping": {"prototype", "prototypes", "wireframes", "mockups", "poc", "proof of concept"},

        # Writing/Documentation
        "writing": {"documentation", "documenting", "documented", "authored", "wrote", "drafting"},
        "technical": {"technology", "tech", "engineering"},

        # Mentorship/Development
        "mentorship": {"mentoring", "mentored", "coaching", "coached", "training", "developed"},
        "mentoring": {"mentorship", "coaching", "training", "developing talent"},

        # Listening/Resolution
        "listening": {"understanding", "empathy", "receptive"},
        "resolution": {"resolving", "resolved", "solving", "mediation"},
        "conflict": {"disagreement", "disputes", "issues"},
    }

    # Make bidirectional - if A is synonym of B, B should also map to A
    bidirectional = {}
    for word, synonyms in base_synonyms.items():
        if word not in bidirectional:
            bidirectional[word] = set()
        bidirectional[word].update(synonyms)
        for syn in synonyms:
            if syn not in bidirectional:
                bidirectional[syn] = set()
            bidirectional[syn].add(word)

    return bidirectional


def map_bullets_to_cluster(
    cluster: CapabilityCluster,
    bullets: List[Bullet],
    similarity_threshold: float = 0.10,  # Lowered threshold
    min_keyword_matches: int = 2  # Minimum absolute matches to consider a bullet relevant
) -> Tuple[List[str], float, List[str]]:
    """
    Map bullets to a single cluster.

    Returns:
        Tuple of (matched_bullet_ids, match_percentage, gaps)
    """
    matched_bullet_ids = []
    component_matches = {cs.name: False for cs in cluster.component_skills}
    skill_synonyms = _get_skill_synonyms()

    # Build cluster keyword set
    cluster_keywords = set()
    cluster_keywords.add(cluster.name.lower())

    # Add keywords from component skills (full phrase + individual words)
    for comp in cluster.component_skills:
        cluster_keywords.add(comp.name.lower())
        for word in comp.name.lower().split():
            if len(word) >= 3:
                cluster_keywords.add(word)
                # Add synonyms
                if word in skill_synonyms:
                    cluster_keywords.update(skill_synonyms[word])

        # Add evidence skill keywords
        for ev in comp.evidence_skills:
            cluster_keywords.add(ev.name.lower())

    # Check ontology for additional keywords
    if cluster.name in CAPABILITY_ONTOLOGY:
        ontology_data = CAPABILITY_ONTOLOGY[cluster.name]
        for kw in ontology_data.get("evidence_keywords", []):
            cluster_keywords.add(kw.lower())
        # Also add component skills from ontology
        for comp_skill in ontology_data.get("component_skills", []):
            cluster_keywords.add(comp_skill.lower())
            for word in comp_skill.lower().split():
                if len(word) >= 3:
                    cluster_keywords.add(word)

    # Score each bullet against the cluster
    for bullet in bullets:
        bullet_keywords = extract_bullet_keywords(bullet)
        overlap_score = compute_keyword_overlap(cluster_keywords, bullet_keywords)

        # Calculate absolute keyword matches
        cluster_norm = {k.lower().strip() for k in cluster_keywords}
        bullet_norm = {k.lower().strip() for k in bullet_keywords}
        absolute_matches = len(cluster_norm & bullet_norm)

        # Match if either threshold met OR minimum absolute matches met
        if overlap_score >= similarity_threshold or absolute_matches >= min_keyword_matches:
            matched_bullet_ids.append(str(bullet.id))

            # Mark which component skills this bullet demonstrates
            for comp in cluster.component_skills:
                comp_keywords = {comp.name.lower()}
                for word in comp.name.lower().split():
                    if len(word) >= 3:
                        comp_keywords.add(word)
                        # Add synonyms for component matching
                        if word in skill_synonyms:
                            comp_keywords.update(skill_synonyms[word])
                for ev in comp.evidence_skills:
                    comp_keywords.add(ev.name.lower())

                # Check for word-level overlap, not just phrase overlap
                comp_overlap = compute_keyword_overlap(comp_keywords, bullet_keywords)
                # Also check if any significant word from component appears in bullet
                word_match = any(
                    w in bullet_keywords
                    for w in comp.name.lower().split()
                    if len(w) >= 4
                )
                # Check for synonym matches as well
                synonym_match = any(
                    syn in bullet_keywords
                    for w in comp.name.lower().split()
                    if len(w) >= 4 and w in skill_synonyms
                    for syn in skill_synonyms[w]
                )
                if comp_overlap >= 0.1 or word_match or synonym_match:  # Lowered threshold further
                    component_matches[comp.name] = True

    # Calculate match percentage
    matched_components = sum(1 for matched in component_matches.values() if matched)
    total_components = len(cluster.component_skills)
    match_percentage = (matched_components / total_components * 100) if total_components > 0 else 0.0

    # Identify gaps (unmatched required components)
    gaps = []
    for comp in cluster.component_skills:
        if comp.required and not component_matches.get(comp.name, False):
            gaps.append(comp.name)

    return matched_bullet_ids, match_percentage, gaps


def generate_positioning_strategy(
    cluster: CapabilityCluster,
    gaps: List[str],
    matched_count: int
) -> str:
    """
    Generate a positioning strategy for addressing cluster gaps.
    """
    if not gaps:
        return f"Strong alignment with {cluster.name}. Lead with this capability."

    gap_count = len(gaps)

    if cluster.importance == "critical":
        if gap_count == 1:
            return f"Minor gap in {gaps[0]}. Frame existing experience as foundation for rapid skill acquisition."
        elif gap_count <= 3:
            return f"Address gaps in {', '.join(gaps[:2])} by emphasizing transferable skills and learning trajectory."
        else:
            return f"Significant gaps in {cluster.name}. Consider framing as growth opportunity if other clusters are strong."

    elif cluster.importance == "important":
        if gap_count <= 2:
            return f"Moderate gaps in {', '.join(gaps)}. Mention awareness and willingness to develop."
        else:
            return f"Focus on stronger capability areas; acknowledge {cluster.name} as development area."

    else:  # nice-to-have
        return f"Gaps in {cluster.name} are acceptable for this role. Focus on critical capabilities."


async def map_bullets_to_clusters(
    clusters: List[CapabilityCluster],
    user_id: int,
    db: Session
) -> List[CapabilityCluster]:
    """
    Map user's bullets to capability clusters.

    Updates clusters in place with:
    - match_percentage
    - user_evidence (bullet IDs)
    - gaps
    - positioning
    - component_skills[].matched

    Returns updated clusters.
    """
    # Get user's bullets
    bullets = get_user_bullets(user_id, db)

    if not bullets:
        logger.warning(f"No bullets found for user {user_id}")
        # Return clusters with 0% match
        for cluster in clusters:
            cluster.match_percentage = 0.0
            cluster.gaps = [cs.name for cs in cluster.component_skills if cs.required]
            cluster.positioning = generate_positioning_strategy(cluster, cluster.gaps, 0)
        return clusters

    logger.info(f"Mapping {len(bullets)} bullets to {len(clusters)} clusters")

    for cluster in clusters:
        matched_ids, match_pct, gaps = map_bullets_to_cluster(cluster, bullets)

        cluster.user_evidence = matched_ids
        cluster.match_percentage = match_pct
        cluster.gaps = gaps
        cluster.positioning = generate_positioning_strategy(cluster, gaps, len(matched_ids))

        # Update component skill matched status
        bullet_keywords_combined = set()
        for bid in matched_ids:
            bullet = next((b for b in bullets if str(b.id) == bid), None)
            if bullet:
                bullet_keywords_combined.update(extract_bullet_keywords(bullet))

        skill_synonyms = _get_skill_synonyms()
        for comp in cluster.component_skills:
            comp_keywords = {comp.name.lower()}
            for word in comp.name.lower().split():
                if len(word) > 3:
                    comp_keywords.add(word)
                    # Add synonyms
                    if word in skill_synonyms:
                        comp_keywords.update(skill_synonyms[word])
            for ev in comp.evidence_skills:
                comp_keywords.add(ev.name.lower())

            overlap = compute_keyword_overlap(comp_keywords, bullet_keywords_combined)
            # Also check for direct synonym matches
            synonym_match = any(
                syn in bullet_keywords_combined
                for w in comp.name.lower().split()
                if len(w) >= 4 and w in skill_synonyms
                for syn in skill_synonyms[w]
            )
            comp.matched = overlap >= 0.15 or synonym_match  # Lowered threshold
            comp.match_strength = overlap

    # Sort clusters by importance then match percentage
    importance_order = {"critical": 0, "important": 1, "nice-to-have": 2}
    clusters.sort(key=lambda c: (importance_order.get(c.importance, 1), -c.match_percentage))

    return clusters


def calculate_overall_match_score(clusters: List[CapabilityCluster]) -> float:
    """
    Calculate overall match score across all clusters.
    Weighted by importance.
    """
    if not clusters:
        return 0.0

    weights = {"critical": 3.0, "important": 2.0, "nice-to-have": 1.0}

    total_weight = 0.0
    weighted_score = 0.0

    for cluster in clusters:
        weight = weights.get(cluster.importance, 1.0)
        total_weight += weight
        weighted_score += cluster.match_percentage * weight

    return weighted_score / total_weight if total_weight > 0 else 0.0


def determine_recommendation(overall_score: float, critical_gaps: int) -> str:
    """
    Determine match recommendation based on score and critical gaps.
    """
    if critical_gaps > 2:
        return "weak_match"
    elif overall_score >= 70 and critical_gaps == 0:
        return "strong_match"
    elif overall_score >= 50:
        return "moderate_match"
    elif overall_score >= 30:
        return "stretch_role"
    else:
        return "weak_match"


def generate_positioning_summary(
    clusters: List[CapabilityCluster],
    overall_score: float
) -> str:
    """
    Generate overall positioning summary for cover letter guidance.
    """
    # Find strongest clusters
    strong_clusters = [c for c in clusters if c.match_percentage >= 70]
    weak_clusters = [c for c in clusters if c.match_percentage < 40 and c.importance == "critical"]

    summary_parts = []

    if strong_clusters:
        names = [c.name for c in strong_clusters[:2]]
        summary_parts.append(f"Lead with strength in {' and '.join(names)}.")

    if weak_clusters:
        names = [c.name for c in weak_clusters[:2]]
        summary_parts.append(f"Address gaps in {' and '.join(names)} by emphasizing learning agility and transferable skills.")

    if overall_score >= 70:
        summary_parts.append("Strong overall fit - emphasize depth and readiness.")
    elif overall_score >= 50:
        summary_parts.append("Moderate fit - highlight strongest capabilities and growth mindset.")
    else:
        summary_parts.append("Position as stretch opportunity - focus on trajectory and potential.")

    return " ".join(summary_parts)


async def build_capability_analysis(
    clusters: List[CapabilityCluster],
    job_profile_id: int,
    user_id: int,
    db: Session
) -> CapabilityClusterAnalysis:
    """
    Build complete capability cluster analysis.

    This is the main entry point for evidence mapping.
    """
    # Map bullets to clusters
    mapped_clusters = await map_bullets_to_clusters(clusters, user_id, db)

    # Calculate overall score
    overall_score = calculate_overall_match_score(mapped_clusters)

    # Count critical gaps
    critical_gaps = sum(
        1 for c in mapped_clusters
        if c.importance == "critical" and len(c.gaps) > 0
    )

    # Determine recommendation
    recommendation = determine_recommendation(overall_score, critical_gaps)

    # Generate positioning summary
    positioning_summary = generate_positioning_summary(mapped_clusters, overall_score)

    # Extract key strengths (top 3 by match %)
    sorted_by_match = sorted(mapped_clusters, key=lambda c: c.match_percentage, reverse=True)
    key_strengths = [c.name for c in sorted_by_match[:3] if c.match_percentage >= 60]

    # Extract critical gaps
    all_critical_gaps = []
    for c in mapped_clusters:
        if c.importance == "critical":
            all_critical_gaps.extend(c.gaps)

    analysis = CapabilityClusterAnalysis(
        job_profile_id=job_profile_id,
        user_id=user_id,
        clusters=mapped_clusters,
        overall_match_score=overall_score,
        recommendation=recommendation,
        positioning_summary=positioning_summary,
        key_strengths=key_strengths,
        critical_gaps=all_critical_gaps[:5]  # Top 5 critical gaps
    )

    return analysis


def add_skill_to_user_profile(
    skill_name: str,
    user_id: int,
    evidence_mappings: List[EvidenceMapping],
    db: Session
) -> int:
    """
    Add a skill to user's profile by updating bullets and experiences.

    Args:
        skill_name: Name of skill to add (1-100 chars)
        user_id: User ID - all referenced entities must belong to this user
        evidence_mappings: List of experience/engagement/bullet mappings
        db: SQLAlchemy database session

    Logic:
    - If bullet_ids provided: add skill to each Bullet.tags
    - If no bullet_ids but engagement_id: add skill to all engagement bullets
    - If just experience_id: add skill to Experience.tools_and_technologies

    Returns: Number of entities updated

    Raises:
        ValueError: If experience, engagement, or bullet not found OR doesn't belong to user

    Note:
        This is currently a single-user demo app, but ownership validation is
        implemented for security best practices when multi-user auth is added.
    """
    entities_updated = 0

    for mapping in evidence_mappings:
        # Validate experience exists AND belongs to user (SECURITY: ownership check)
        experience = db.query(Experience).filter(
            Experience.id == mapping.experience_id,
            Experience.user_id == user_id
        ).first()
        if not experience:
            raise ValueError(f"Experience {mapping.experience_id} not found or unauthorized")

        # Case 1: Specific bullet IDs provided
        if mapping.bullet_ids:
            for bullet_id in mapping.bullet_ids:
                # SECURITY: Validate bullet belongs to user
                bullet = db.query(Bullet).filter(
                    Bullet.id == bullet_id,
                    Bullet.user_id == user_id
                ).first()
                if not bullet:
                    raise ValueError(f"Bullet {bullet_id} not found or unauthorized")

                # Add skill to bullet tags if not already present
                if bullet.tags is None:
                    bullet.tags = []
                if skill_name not in bullet.tags:
                    bullet.tags = bullet.tags + [skill_name]  # Create new list for SQLAlchemy to detect change
                    entities_updated += 1

        # Case 2: Engagement specified but no specific bullets
        elif mapping.engagement_id is not None:
            # Validate engagement exists AND belongs to the experience
            engagement = db.query(Engagement).filter(
                Engagement.id == mapping.engagement_id,
                Engagement.experience_id == experience.id
            ).first()
            if not engagement:
                raise ValueError(f"Engagement {mapping.engagement_id} not found or unauthorized")

            # Add skill to all bullets in this engagement (already owned by user via experience)
            engagement_bullets = db.query(Bullet).filter(
                Bullet.engagement_id == mapping.engagement_id,
                Bullet.user_id == user_id
            ).all()

            for bullet in engagement_bullets:
                if bullet.tags is None:
                    bullet.tags = []
                if skill_name not in bullet.tags:
                    bullet.tags = bullet.tags + [skill_name]
                    entities_updated += 1

        # Case 3: Just experience - add to tools_and_technologies
        else:
            if experience.tools_and_technologies is None:
                experience.tools_and_technologies = []
            if skill_name not in experience.tools_and_technologies:
                experience.tools_and_technologies = experience.tools_and_technologies + [skill_name]
                entities_updated += 1

    db.commit()
    return entities_updated


# Export
__all__ = [
    "get_user_bullets",
    "map_bullets_to_clusters",
    "build_capability_analysis",
    "calculate_overall_match_score",
    "determine_recommendation",
    "add_skill_to_user_profile"
]
