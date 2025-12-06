"""
Skill Gap Analysis Service

Analyzes skill gaps between user profiles and job requirements,
providing positioning strategies and evidence-based match scoring.
"""

from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from db.models import Bullet, Experience, JobProfile
from schemas.skill_gap import (
    SkillGapResponse,
    SkillMatch,
    SkillGap,
    WeakSignal,
    UserSkillProfile,
)


# Skill synonym mapping for flexible matching
SKILL_SYNONYMS: Dict[str, List[str]] = {
    # Programming & Frameworks
    'Python': ['python', 'py'],
    'JavaScript': ['javascript', 'js', 'ecmascript'],
    'TypeScript': ['typescript', 'ts'],
    'React': ['react', 'reactjs', 'react.js'],
    'Node.js': ['nodejs', 'node', 'node js'],
    'FastAPI': ['fastapi', 'fast api'],
    'Django': ['django'],
    'Flask': ['flask'],

    # AI/ML
    'Machine Learning': ['ml', 'machine learning', 'machine-learning'],
    'Deep Learning': ['dl', 'deep learning', 'deep-learning'],
    'Natural Language Processing': ['nlp', 'natural language processing'],
    'Computer Vision': ['cv', 'computer vision'],
    'TensorFlow': ['tensorflow', 'tf'],
    'PyTorch': ['pytorch', 'torch'],
    'scikit-learn': ['sklearn', 'scikit-learn', 'scikit learn'],
    'Hugging Face': ['huggingface', 'hugging face', 'hf'],
    'LangChain': ['langchain', 'lang chain'],
    'OpenAI': ['openai', 'open ai', 'gpt'],
    'MLOps': ['mlops', 'ml ops'],
    'LLM': ['llm', 'large language model', 'large language models'],
    'Generative AI': ['genai', 'gen ai', 'generative ai', 'generative-ai'],

    # Cloud Platforms
    'AWS': ['aws', 'amazon web services'],
    'Azure': ['azure', 'microsoft azure'],
    'GCP': ['gcp', 'google cloud platform', 'google cloud'],
    'Lambda': ['lambda', 'aws lambda'],
    'S3': ['s3', 'aws s3'],
    'EC2': ['ec2', 'aws ec2'],

    # DevOps & Infrastructure
    'Docker': ['docker', 'containerization'],
    'Kubernetes': ['kubernetes', 'k8s'],
    'Terraform': ['terraform', 'tf'],
    'CI/CD': ['ci/cd', 'cicd', 'continuous integration', 'continuous deployment'],
    'GitOps': ['gitops', 'git ops'],

    # Databases
    'PostgreSQL': ['postgresql', 'postgres', 'psql'],
    'MongoDB': ['mongodb', 'mongo'],
    'Redis': ['redis'],
    'MySQL': ['mysql'],
    'SQL': ['sql', 'structured query language'],

    # Data Engineering
    'Apache Spark': ['spark', 'apache spark', 'pyspark'],
    'Kafka': ['kafka', 'apache kafka'],
    'Airflow': ['airflow', 'apache airflow'],
    'ETL': ['etl', 'extract transform load'],

    # Governance & Strategy
    'AI Governance': ['ai governance', 'ai-governance', 'artificial intelligence governance'],
    'Data Governance': ['data governance', 'data-governance'],
    'Risk Management': ['risk management', 'risk-management'],
    'Compliance': ['compliance', 'regulatory compliance'],
    'Model Risk Management': ['model risk management', 'mrm', 'model risk'],

    # Business & Consulting
    'Strategy': ['strategy', 'strategic planning'],
    'Consulting': ['consulting', 'advisory'],
    'Product Management': ['product management', 'product', 'pm'],
    'Project Management': ['project management', 'pmp'],
    'Stakeholder Management': ['stakeholder management', 'stakeholder engagement'],
    'Change Management': ['change management', 'organizational change'],
}


# Related skills mapping for weak signal detection
RELATED_SKILLS: Dict[str, List[str]] = {
    # If user has the key skill, they might have adjacent capability for values
    'Python': ['Django', 'Flask', 'FastAPI', 'Data Engineering', 'Machine Learning'],
    'Machine Learning': ['Deep Learning', 'MLOps', 'Data Science', 'Statistics'],
    'Deep Learning': ['TensorFlow', 'PyTorch', 'Computer Vision', 'NLP'],
    'Data Science': ['Machine Learning', 'Statistics', 'Data Analysis', 'Python'],
    'AWS': ['Cloud Architecture', 'DevOps', 'Infrastructure', 'Terraform'],
    'Docker': ['Kubernetes', 'DevOps', 'Cloud', 'Microservices'],
    'Kubernetes': ['Docker', 'DevOps', 'Cloud Native', 'Helm'],
    'SQL': ['Database Design', 'Data Modeling', 'PostgreSQL', 'MySQL'],
    'Project Management': ['Agile', 'Scrum', 'Stakeholder Management', 'Program Management'],
    'AI Governance': ['Risk Management', 'Compliance', 'Model Risk Management', 'Ethics'],
    'Risk Management': ['Compliance', 'Audit', 'Governance', 'Controls'],
    'Consulting': ['Strategy', 'Stakeholder Management', 'Communication', 'Presentation'],
    'Leadership': ['People Management', 'Team Building', 'Strategy', 'Mentoring'],
    'Data Engineering': ['ETL', 'Spark', 'Airflow', 'Data Pipelines', 'Data Warehouse'],
    'React': ['JavaScript', 'TypeScript', 'Frontend', 'Web Development'],
    'Node.js': ['JavaScript', 'Backend', 'API Development', 'Express'],
    'TensorFlow': ['Deep Learning', 'Machine Learning', 'Neural Networks', 'Model Training'],
    'PyTorch': ['Deep Learning', 'Machine Learning', 'Neural Networks', 'Model Training'],
    'NLP': ['Machine Learning', 'Deep Learning', 'Text Analysis', 'LLM'],
    'LLM': ['NLP', 'Generative AI', 'OpenAI', 'LangChain'],
    'Generative AI': ['LLM', 'NLP', 'Machine Learning', 'OpenAI'],
}


# Positioning strategy templates
POSITIONING_TEMPLATES: Dict[str, List[str]] = {
    'critical': [
        "Address this gap directly by emphasizing transferable experience in {related_skills}",
        "Highlight rapid learning ability and recent upskilling efforts in {skill_area}",
        "Position adjacent experience with {related_skills} as strong foundation",
        "Emphasize willingness to quickly develop {skill} through dedicated training",
    ],
    'important': [
        "Demonstrate adjacent capability through {related_skills} experience",
        "Frame existing expertise as complementary and highlight learning agility",
        "Showcase portfolio/side projects demonstrating {skill} competency",
        "Emphasize transferable skills and proven ability to master new technologies",
    ],
    'nice-to-have': [
        "Note awareness of {skill} and complementary strengths in {related_skills}",
        "Briefly mention familiarity or interest without over-emphasizing",
        "Focus positioning on stronger, more relevant skills instead",
        "Consider mentioning if any exposure through adjacent work",
    ],
}


def normalize_skill(skill: str) -> str:
    """Normalize skill name for comparison."""
    return skill.lower().strip()


def find_skill_match(skill: str, user_skills: List[str]) -> Optional[str]:
    """
    Find if skill matches any user skill (including synonyms).

    Returns the matched user skill if found, None otherwise.
    """
    normalized_skill = normalize_skill(skill)

    # Direct match
    for user_skill in user_skills:
        if normalize_skill(user_skill) == normalized_skill:
            return user_skill

    # Synonym match
    for canonical_skill, synonyms in SKILL_SYNONYMS.items():
        normalized_canonical = normalize_skill(canonical_skill)

        # Check if job skill is a synonym of canonical
        if normalized_skill in [normalize_skill(s) for s in synonyms]:
            # Check if user has the canonical skill
            for user_skill in user_skills:
                if normalize_skill(user_skill) in [normalize_skill(s) for s in [canonical_skill] + synonyms]:
                    return user_skill

    return None


def get_related_skills(skill: str) -> List[str]:
    """Get list of skills related to the given skill."""
    normalized = normalize_skill(skill)

    for key_skill, related in RELATED_SKILLS.items():
        if normalize_skill(key_skill) == normalized:
            return related

    return []


async def build_user_skill_profile(user_id: int, db: Session) -> UserSkillProfile:
    """
    Build user skill profile from database records.

    Aggregates skills, capabilities, tags, seniority levels, and relevance scores
    from user's experiences and bullets.
    """
    # Query user's experiences and bullets
    experiences = db.query(Experience).filter(
        Experience.user_id == user_id
    ).all()

    bullets = db.query(Bullet).filter(
        Bullet.user_id == user_id,
        Bullet.retired == False
    ).all()

    # Aggregate unique skills from bullet tags
    all_skills: Set[str] = set()
    all_capabilities: Set[str] = set()
    all_tags: Set[str] = set()
    seniority_levels: Set[str] = set()
    relevance_scores: Dict[str, List[float]] = {}

    for bullet in bullets:
        # Collect tags
        if bullet.tags:
            for tag in bullet.tags:
                all_tags.add(tag)
                all_skills.add(tag)  # Tags often represent skills

        # Collect seniority level
        if bullet.seniority_level:
            seniority_levels.add(bullet.seniority_level)

        # Aggregate relevance scores
        if bullet.relevance_scores:
            for skill, score in bullet.relevance_scores.items():
                if skill not in relevance_scores:
                    relevance_scores[skill] = []
                relevance_scores[skill].append(score)

    # Extract capabilities from experience descriptions
    for exp in experiences:
        if exp.description:
            # Simple capability extraction (could be enhanced with NLP)
            all_capabilities.add(exp.job_title)

    # Average relevance scores
    avg_relevance_scores = {
        skill: sum(scores) / len(scores)
        for skill, scores in relevance_scores.items()
    }

    return UserSkillProfile(
        skills=list(all_skills),
        capabilities=list(all_capabilities),
        bullet_tags=list(all_tags),
        seniority_levels=list(seniority_levels),
        relevance_scores=avg_relevance_scores,
    )


def compute_matched_skills(
    job_skills: List[str],
    user_profile: UserSkillProfile,
    user_bullets: List[Bullet]
) -> List[SkillMatch]:
    """
    Compute matched skills between job requirements and user profile.

    For each job skill that matches, calculates match strength based on
    frequency and relevance scores, and finds supporting evidence.
    """
    matched_skills: List[SkillMatch] = []
    user_skills = user_profile.skills + user_profile.capabilities + user_profile.bullet_tags

    for job_skill in job_skills:
        matched_user_skill = find_skill_match(job_skill, user_skills)

        if matched_user_skill:
            # Calculate match strength based on relevance and frequency
            relevance = user_profile.relevance_scores.get(matched_user_skill, 0.5)

            # Count frequency across bullets
            frequency = sum(
                1 for bullet in user_bullets
                if bullet.tags and matched_user_skill in bullet.tags
            )

            # Normalize frequency (cap at 5 bullets)
            frequency_score = min(frequency / 5.0, 1.0)

            # Weighted match strength: 60% relevance, 40% frequency
            match_strength = (0.6 * relevance) + (0.4 * frequency_score)

            # Find evidence bullets
            evidence = [
                f"Bullet {bullet.id}: {bullet.text}"
                for bullet in user_bullets
                if bullet.tags and matched_user_skill in bullet.tags
            ][:3]  # Top 3 evidence bullets

            matched_skills.append(SkillMatch(
                skill=job_skill,
                match_strength=round(match_strength, 2),
                evidence=evidence,
            ))

    return matched_skills


def compute_missing_skills(
    job_skills: List[str],
    job_must_have: List[str],
    job_nice_to_have: List[str],
    matched_skill_names: Set[str]
) -> List[SkillGap]:
    """
    Compute missing skills not present in matched set.

    Assigns importance level and generates positioning strategy for each gap.
    """
    missing_skills: List[SkillGap] = []

    for skill in job_skills:
        if normalize_skill(skill) not in {normalize_skill(s) for s in matched_skill_names}:
            # Determine importance
            if any(normalize_skill(skill) == normalize_skill(mh) for mh in job_must_have):
                importance = 'critical'
            elif any(normalize_skill(skill) == normalize_skill(req) for req in job_skills[:len(job_skills)//2]):
                importance = 'important'
            else:
                importance = 'nice-to-have'

            # Generate positioning strategy
            related = get_related_skills(skill)
            templates = POSITIONING_TEMPLATES.get(importance, POSITIONING_TEMPLATES['important'])

            # Select appropriate template
            if related:
                strategy = templates[0].format(
                    related_skills=', '.join(related[:3]),
                    skill_area=skill,
                    skill=skill
                )
            else:
                strategy = templates[1].format(
                    related_skills='related experience',
                    skill_area=skill,
                    skill=skill
                )

            missing_skills.append(SkillGap(
                skill=skill,
                importance=importance,
                positioning_strategy=strategy,
            ))

    return missing_skills


def compute_weak_signals(
    job_skills: List[str],
    user_profile: UserSkillProfile,
    matched_skill_names: Set[str],
    missing_skill_names: Set[str]
) -> List[WeakSignal]:
    """
    Identify weak signals: skills where user has related capability but not direct match.

    Uses RELATED_SKILLS mapping to find adjacent capabilities.
    """
    weak_signals: List[WeakSignal] = []
    user_skills = user_profile.skills + user_profile.capabilities

    for job_skill in job_skills:
        normalized_job_skill = normalize_skill(job_skill)

        # Skip if already matched or missing
        if normalized_job_skill in {normalize_skill(s) for s in matched_skill_names}:
            continue
        if normalized_job_skill in {normalize_skill(s) for s in missing_skill_names}:
            # Check for adjacent capabilities
            related_skills = get_related_skills(job_skill)
            user_related = [
                skill for skill in user_skills
                if any(normalize_skill(skill) == normalize_skill(rel) for rel in related_skills)
            ]

            if user_related:
                current_evidence = [
                    f"Experience with {skill} (related to {job_skill})"
                    for skill in user_related[:3]
                ]

                strengthening_strategy = (
                    f"Emphasize how experience with {', '.join(user_related[:2])} "
                    f"provides strong foundation for {job_skill}. Consider adding specific examples "
                    f"of how these skills were applied in ways relevant to {job_skill}."
                )

                weak_signals.append(WeakSignal(
                    skill=job_skill,
                    current_evidence=current_evidence,
                    strengthening_strategy=strengthening_strategy,
                ))

    return weak_signals


def compute_skill_match_score(
    matched: List[SkillMatch],
    missing: List[SkillGap],
    weak: List[WeakSignal],
    job_must_have: List[str]
) -> float:
    """
    Calculate overall skill match score (0-100).

    Weighted formula:
    - Must-have skills matched: 60% weight
    - Nice-to-have skills matched: 20% weight
    - Weak signals: 15% weight
    - Match strength quality: 5% weight
    """
    if not matched and not weak:
        return 0.0

    # Identify must-have matches
    must_have_normalized = {normalize_skill(s) for s in job_must_have}
    must_have_matches = [
        m for m in matched
        if normalize_skill(m.skill) in must_have_normalized
    ]

    # Must-have coverage (60% weight)
    must_have_score = 0.0
    if job_must_have:
        must_have_score = (len(must_have_matches) / len(job_must_have)) * 60.0
    else:
        must_have_score = 60.0  # No must-haves specified

    # Nice-to-have coverage (20% weight)
    other_matches = [m for m in matched if m not in must_have_matches]
    nice_to_have_score = min((len(other_matches) / max(len(matched), 1)) * 20.0, 20.0)

    # Weak signals (15% weight)
    weak_signal_score = min((len(weak) / max((len(matched) + len(missing)), 1)) * 15.0, 15.0)

    # Match strength quality (5% weight)
    avg_match_strength = sum(m.match_strength for m in matched) / len(matched) if matched else 0.0
    quality_score = avg_match_strength * 5.0

    total_score = must_have_score + nice_to_have_score + weak_signal_score + quality_score

    return round(min(total_score, 100.0), 1)


def generate_positioning_strategies(
    missing: List[SkillGap],
    weak: List[WeakSignal],
    matched: List[SkillMatch]
) -> List[str]:
    """
    Generate 3-5 actionable positioning strategies.

    Prioritizes addressing critical gaps and leveraging strengths.
    """
    strategies: List[str] = []

    # Address critical gaps first
    critical_gaps = [g for g in missing if g.importance == 'critical']
    if critical_gaps:
        strategies.append(
            f"Proactively address critical skill gap in {critical_gaps[0].skill} by "
            f"emphasizing transferable experience and learning agility"
        )

    # Leverage strongest matches
    strong_matches = sorted(matched, key=lambda m: m.match_strength, reverse=True)[:3]
    if strong_matches:
        top_skills = ', '.join(m.skill for m in strong_matches)
        strategies.append(
            f"Lead with strongest matches: {top_skills}. Use these as anchor points "
            f"in resume and cover letter"
        )

    # Strengthen weak signals
    if weak:
        strategies.append(
            f"Bridge skill gaps by explicitly connecting experience with {weak[0].skill}-adjacent "
            f"work. Reframe bullets to highlight relevant aspects"
        )

    # Address multiple gaps strategically
    if len(missing) > 3:
        strategies.append(
            "Position as 'learning-oriented' candidate with proven track record of quickly "
            "mastering new technologies and domains"
        )

    # Emphasize unique differentiators
    if matched:
        strategies.append(
            "Differentiate by emphasizing unique combination of skills and cross-functional "
            "experience that brings fresh perspective"
        )

    return strategies[:5]  # Return top 5 strategies


def determine_recommendation(score: float, critical_gaps: int) -> Tuple[str, float]:
    """
    Determine overall recommendation and confidence.

    Returns tuple of (recommendation, confidence).
    """
    if score >= 80 and critical_gaps <= 1:
        return ('strong_match', 0.9)
    elif score >= 60 and critical_gaps <= 2:
        return ('moderate_match', 0.75)
    elif score >= 40:
        return ('stretch_role', 0.6)
    else:
        return ('weak_match', 0.5)


async def analyze_skill_gap(
    job_profile_id: int,
    user_id: int,
    db: Session,
    user_skill_profile: Optional[UserSkillProfile] = None
) -> SkillGapResponse:
    """
    Compute comprehensive skill gap analysis between job requirements and user profile.

    Main entry point for skill gap analysis. Analyzes matched skills, identifies gaps,
    detects weak signals, and generates positioning strategies.

    Args:
        job_profile_id: ID of the job profile to analyze against
        user_id: ID of the user
        db: Database session
        user_skill_profile: Optional pre-built user skill profile (if None, will be built from DB)

    Returns:
        SkillGapResponse with comprehensive analysis and positioning guidance

    Raises:
        ValueError: If job profile not found or missing required data
    """
    # Fetch job profile
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile:
        raise ValueError(f"Job profile {job_profile_id} not found")

    # Extract job requirements
    job_skills = job_profile.extracted_skills or []
    job_must_have = job_profile.must_have_capabilities or []
    job_nice_to_have = job_profile.nice_to_have_capabilities or []

    if not job_skills:
        raise ValueError(f"Job profile {job_profile_id} has no extracted skills")

    # Build user skill profile if not provided
    if user_skill_profile is None:
        user_skill_profile = await build_user_skill_profile(user_id, db)

    # Fetch user bullets for evidence
    user_bullets = db.query(Bullet).filter(
        Bullet.user_id == user_id,
        Bullet.retired == False
    ).all()

    # Compute matched skills
    matched_skills = compute_matched_skills(job_skills, user_skill_profile, user_bullets)
    matched_skill_names = {m.skill for m in matched_skills}

    # Compute missing skills (gaps)
    missing_skills = compute_missing_skills(
        job_skills,
        job_must_have,
        job_nice_to_have,
        matched_skill_names
    )
    missing_skill_names = {g.skill for g in missing_skills}

    # Compute weak signals
    weak_signals = compute_weak_signals(
        job_skills,
        user_skill_profile,
        matched_skill_names,
        missing_skill_names
    )

    # Calculate overall match score
    skill_match_score = compute_skill_match_score(
        matched_skills,
        missing_skills,
        weak_signals,
        job_must_have
    )

    # Generate positioning strategies
    key_positioning_angles = generate_positioning_strategies(
        missing_skills,
        weak_signals,
        matched_skills
    )

    # Determine recommendation
    critical_gaps = len([g for g in missing_skills if g.importance == 'critical'])
    recommendation, confidence = determine_recommendation(skill_match_score, critical_gaps)

    # Build bullet selection guidance
    bullet_selection_guidance = {
        'prioritize_tags': [m.skill for m in sorted(matched_skills, key=lambda x: x.match_strength, reverse=True)[:5]],
        'emphasize_capabilities': user_skill_profile.capabilities[:3],
        'target_seniority': list(user_skill_profile.seniority_levels)[:1] if user_skill_profile.seniority_levels else [],
    }

    # Generate cover letter hooks
    cover_letter_hooks = []
    if matched_skills:
        top_match = max(matched_skills, key=lambda m: m.match_strength)
        cover_letter_hooks.append(
            f"Open with strong expertise in {top_match.skill} and track record of impact"
        )
    if weak_signals:
        cover_letter_hooks.append(
            f"Address {weak_signals[0].skill} by highlighting adjacent experience and learning agility"
        )
    if critical_gaps == 0:
        cover_letter_hooks.append(
            "Emphasize comprehensive skill alignment and readiness to contribute immediately"
        )

    # Identify user advantages
    user_advantages = []
    strong_matches = [m for m in matched_skills if m.match_strength >= 0.75]
    if strong_matches:
        user_advantages.append(
            f"Strong expertise in {len(strong_matches)} key required skills"
        )
    if len(user_skill_profile.capabilities) > 3:
        user_advantages.append(
            "Diverse cross-functional experience bringing multiple perspectives"
        )
    if user_skill_profile.seniority_levels:
        user_advantages.append(
            f"Proven experience at {', '.join(list(user_skill_profile.seniority_levels)[:2])} level"
        )

    # Identify potential concerns
    potential_concerns = []
    mitigation_strategies = {}

    if critical_gaps > 0:
        critical_gap_skills = [g.skill for g in missing_skills if g.importance == 'critical']
        concern = f"Missing critical skill(s): {', '.join(critical_gap_skills)}"
        potential_concerns.append(concern)
        mitigation_strategies[concern] = (
            "Emphasize rapid learning ability and similar skill acquisition in past. "
            "Provide specific examples of mastering new technologies quickly."
        )

    if len(missing_skills) > len(matched_skills):
        concern = "Skill gap breadth may raise questions"
        potential_concerns.append(concern)
        mitigation_strategies[concern] = (
            "Focus on depth of matched skills and transferable capabilities. "
            "Frame as opportunity to bring fresh perspective."
        )

    # Build response
    return SkillGapResponse(
        job_profile_id=job_profile_id,
        user_id=user_id,
        skill_match_score=skill_match_score,
        recommendation=recommendation,
        confidence=confidence,
        matched_skills=matched_skills,
        skill_gaps=missing_skills,
        weak_signals=weak_signals,
        key_positioning_angles=key_positioning_angles,
        bullet_selection_guidance=bullet_selection_guidance,
        cover_letter_hooks=cover_letter_hooks,
        user_advantages=user_advantages,
        potential_concerns=potential_concerns,
        mitigation_strategies=mitigation_strategies,
        analysis_timestamp=datetime.utcnow().isoformat(),
    )
