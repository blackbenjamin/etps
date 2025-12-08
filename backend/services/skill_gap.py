"""
Skill Gap Analysis Service

Analyzes skill gaps between user profiles and job requirements,
providing positioning strategies and evidence-based match scoring.

Enhanced with semantic matching, LLM-based categorization, and
job-specific positioning strategies.
"""

from datetime import datetime
from threading import Lock
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
import logging

from db.models import Bullet, Experience, JobProfile
from schemas.skill_gap import (
    SkillGapResponse,
    SkillMatch,
    SkillGap,
    WeakSignal,
    UserSkillProfile,
)
from services.embeddings import create_embedding_service, BaseEmbeddingService

# Logger for debugging
logger = logging.getLogger(__name__)


# Thread-safe singleton for embedding service
_embedding_service: Optional[BaseEmbeddingService] = None
_embedding_lock = Lock()


def get_embedding_service() -> BaseEmbeddingService:
    """Get or create the embedding service instance (thread-safe)."""
    global _embedding_service
    with _embedding_lock:
        if _embedding_service is None:
            _embedding_service = create_embedding_service(use_mock=True)
    return _embedding_service


# Mock LLM Service for development
class MockLLMService:
    """
    Mock LLM service for development without API calls.
    Returns heuristic-based responses for skill analysis.
    """

    async def classify_skill_importance(
        self,
        skill: str,
        jd_text: str,
        must_have_skills: List[str],
        nice_to_have_skills: List[str]
    ) -> str:
        """
        Classify skill importance based on JD context.

        Mock implementation uses keyword position and frequency.
        Real implementation would use LLM to understand context.

        Args:
            skill: The skill to classify
            jd_text: Full job description text
            must_have_skills: List of explicitly marked must-have skills
            nice_to_have_skills: List of explicitly marked nice-to-have skills

        Returns:
            Importance level: 'critical', 'important', or 'nice-to-have'
        """
        # Check explicit lists first
        skill_lower = skill.lower()
        if any(skill_lower in mh.lower() for mh in must_have_skills):
            return 'critical'
        if any(skill_lower in nth.lower() for nth in nice_to_have_skills):
            return 'nice-to-have'

        # Analyze JD position and context
        jd_lower = jd_text.lower()

        # Check if in requirements section (high importance)
        requirements_keywords = ['required', 'must have', 'essential', 'mandatory', 'minimum qualifications']
        nice_keywords = ['nice to have', 'preferred', 'bonus', 'plus', 'desired']

        # Find skill mentions
        skill_positions = []
        idx = 0
        while idx < len(jd_lower):
            idx = jd_lower.find(skill_lower, idx)
            if idx == -1:
                break
            skill_positions.append(idx)
            idx += len(skill_lower)

        if not skill_positions:
            return 'nice-to-have'

        # Check context around each mention
        critical_signals = 0
        nice_signals = 0

        for pos in skill_positions:
            # Check 200 chars before and after
            context_start = max(0, pos - 200)
            context_end = min(len(jd_lower), pos + 200)
            context = jd_lower[context_start:context_end]

            for keyword in requirements_keywords:
                if keyword in context:
                    critical_signals += 1

            for keyword in nice_keywords:
                if keyword in context:
                    nice_signals += 1

        # Determine importance
        if critical_signals > nice_signals:
            return 'critical'
        elif nice_signals > 0:
            return 'nice-to-have'
        elif skill_positions[0] < len(jd_lower) // 2:
            # Mentioned in first half - likely important
            return 'important'
        else:
            return 'nice-to-have'

    async def generate_positioning_strategy(
        self,
        skill: str,
        importance: str,
        user_skills: List[str],
        job_priorities: List[str]
    ) -> str:
        """
        Generate job-specific positioning strategy for a skill gap.

        Mock implementation uses template-based generation with context.
        Real implementation would use LLM for dynamic, nuanced strategies.

        Args:
            skill: The missing skill
            importance: Skill importance level
            user_skills: User's actual skills
            job_priorities: Job's core priorities

        Returns:
            Personalized positioning strategy
        """
        # Find related user skills
        related_user_skills = []
        skill_lower = skill.lower()

        for user_skill in user_skills[:10]:  # Top 10 user skills
            # Simple relatedness check
            user_skill_words = set(user_skill.lower().split())
            skill_words = set(skill_lower.split())

            if user_skill_words & skill_words:  # Has overlap
                related_user_skills.append(user_skill)

        # Get related skills from mapping
        mapped_related = get_related_skills(skill)
        related_in_user = [
            rs for rs in mapped_related
            if any(normalize_skill(rs) == normalize_skill(us) for us in user_skills)
        ]

        # Build context-aware strategy
        if importance == 'critical':
            if related_user_skills or related_in_user:
                foundation_skills = related_user_skills[:2] if related_user_skills else related_in_user[:2]
                return (
                    f"While you don't have direct {skill} experience, emphasize your strong foundation in "
                    f"{', '.join(foundation_skills)} which demonstrates the technical aptitude needed. "
                    f"Highlight your proven ability to quickly master new technologies and your commitment "
                    f"to rapidly developing {skill} expertise through dedicated learning and hands-on practice."
                )
            else:
                return (
                    f"Acknowledge the {skill} requirement directly and position it as a growth opportunity. "
                    f"Emphasize your track record of quickly acquiring new skills and your enthusiasm for "
                    f"expanding into {skill}. Consider completing relevant certifications or projects before applying."
                )

        elif importance == 'important':
            if related_user_skills or related_in_user:
                bridge_skills = related_user_skills[:2] if related_user_skills else related_in_user[:2]
                return (
                    f"Bridge to {skill} by emphasizing your hands-on experience with {', '.join(bridge_skills)}, "
                    f"which share key concepts and principles. Frame your background as providing a solid "
                    f"foundation that will accelerate your {skill} learning curve."
                )
            else:
                return (
                    f"Address the {skill} gap by highlighting transferable capabilities and demonstrating "
                    f"learning agility. Consider showcasing any side projects, coursework, or self-study "
                    f"related to {skill} to show genuine interest and initiative."
                )

        else:  # nice-to-have
            if related_user_skills or related_in_user:
                return (
                    f"Briefly mention familiarity with concepts related to {skill} through your work with "
                    f"{related_user_skills[0] if related_user_skills else related_in_user[0]}. "
                    f"Focus your narrative on stronger skill matches while noting {skill} as an area "
                    f"you're interested in developing further."
                )
            else:
                return (
                    f"Don't over-emphasize the {skill} gap. Instead, focus on your core strengths and "
                    f"unique value proposition. If relevant, mention {skill} as an area of professional "
                    f"interest you're exploring."
                )


# Thread-safe singleton for LLM service
_llm_service: Optional[MockLLMService] = None
_llm_lock = Lock()


def get_llm_service() -> MockLLMService:
    """Get or create the LLM service instance (thread-safe)."""
    global _llm_service
    with _llm_lock:
        if _llm_service is None:
            _llm_service = MockLLMService()
    return _llm_service


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
    'Data Governance': ['data governance', 'data-governance', 'information governance'],
    'Data Catalog': ['data catalog', 'data-catalog', 'data cataloging', 'enterprise data catalog'],
    'Collibra': ['collibra', 'collibra data catalog', 'collibra platform'],
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
    # Data Governance domain - these skills are highly related
    'Data Governance': ['Data Catalog', 'Data Quality', 'Data Stewardship', 'Metadata Management',
                        'Data Lineage', 'Collibra', 'Alation', 'Enterprise Data', 'Data Strategy'],
    'Data Catalog': ['Data Governance', 'Metadata Management', 'Data Lineage', 'Collibra',
                     'Alation', 'Data Stewardship', 'Enterprise Data'],
    'Collibra': ['Data Catalog', 'Data Governance', 'Data Quality', 'Metadata Management',
                 'Data Lineage', 'Data Stewardship', 'Enterprise Data'],
    'Data Quality': ['Data Governance', 'Data Stewardship', 'Data Catalog', 'ETL'],
    'Metadata Management': ['Data Catalog', 'Data Governance', 'Data Lineage', 'Collibra'],
    'Enterprise Data': ['Data Governance', 'Data Strategy', 'Data Architecture', 'Data Catalog'],
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


async def compute_semantic_skill_match(
    skill: str,
    user_skills: List[str],
    threshold: float = 0.6
) -> Optional[Tuple[str, float]]:
    """
    Find semantic match between a skill and user skills using embeddings.

    Uses embedding similarity to find matches beyond exact string matching.
    Falls back to simple word overlap if embedding service is unavailable.

    Args:
        skill: The job skill to match
        user_skills: List of user's skills
        threshold: Minimum similarity threshold (0-1)

    Returns:
        Tuple of (matched_user_skill, similarity_score) if found, None otherwise
    """
    if not user_skills:
        return None

    try:
        embedding_service = get_embedding_service()
        # Use find_best_semantic_match which handles embedding generation internally
        match_result = await embedding_service.find_best_semantic_match(
            query=skill,
            candidates=user_skills,
            threshold=threshold
        )
        if match_result:
            best_match, best_score = match_result
            logger.debug(f"Semantic match: '{skill}' -> '{best_match}' (score: {best_score:.2f})")
            return (best_match, best_score)

    except Exception as e:
        logger.warning(f"Semantic matching failed for '{skill}': {e}")

    return None


def find_skill_match_sync(skill: str, user_skills: List[str]) -> Optional[str]:
    """
    Find if skill matches any user skill (synchronous version - no semantic matching).

    Uses direct matching and synonym mapping only.
    For semantic matching, use the async version `find_skill_match`.

    Args:
        skill: The job skill to match
        user_skills: List of user's skills

    Returns:
        The matched user skill if found, None otherwise
    """
    normalized_skill = normalize_skill(skill)

    # Direct match
    for user_skill in user_skills:
        if normalize_skill(user_skill) == normalized_skill:
            return user_skill

    # Synonym match
    for canonical_skill, synonyms in SKILL_SYNONYMS.items():
        # Check if job skill is a synonym of canonical
        if normalized_skill in [normalize_skill(s) for s in synonyms]:
            # Check if user has the canonical skill
            for user_skill in user_skills:
                if normalize_skill(user_skill) in [normalize_skill(s) for s in [canonical_skill] + synonyms]:
                    return user_skill

    return None


async def find_skill_match(skill: str, user_skills: List[str]) -> Optional[str]:
    """
    Find if skill matches any user skill (including synonyms and semantic similarity).

    Enhanced with semantic matching when direct and synonym matching fails.

    Args:
        skill: The job skill to match
        user_skills: List of user's skills

    Returns:
        The matched user skill if found, None otherwise
    """
    # Try sync matching first (direct + synonyms)
    sync_match = find_skill_match_sync(skill, user_skills)
    if sync_match:
        return sync_match

    # Semantic match (Task 2.1) - lowered threshold from 0.7 to 0.6 for better matching
    semantic_match = await compute_semantic_skill_match(skill, user_skills, threshold=0.6)
    if semantic_match:
        matched_skill, _ = semantic_match
        return matched_skill

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


async def compute_matched_skills(
    job_skills: List[str],
    user_profile: UserSkillProfile,
    user_bullets: List[Bullet]
) -> List[SkillMatch]:
    """
    Compute matched skills between job requirements and user profile.

    For each job skill that matches, calculates match strength based on
    frequency and relevance scores, and finds supporting evidence.

    Enhanced with semantic matching support.
    """
    matched_skills: List[SkillMatch] = []
    user_skills = user_profile.skills + user_profile.capabilities + user_profile.bullet_tags

    for job_skill in job_skills:
        matched_user_skill = await find_skill_match(job_skill, user_skills)

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


async def classify_skill_importance_with_context(
    skill: str,
    jd_text: str,
    job_must_have: List[str],
    job_nice_to_have: List[str]
) -> str:
    """
    Classify skill importance using LLM with JD context analysis (Task 2.2).

    Analyzes skill position in JD (requirements vs nice-to-have sections),
    frequency, and contextual importance signals.

    Args:
        skill: The skill to classify
        jd_text: Full job description text
        job_must_have: Explicitly marked must-have skills
        job_nice_to_have: Explicitly marked nice-to-have skills

    Returns:
        Importance level: 'critical', 'important', or 'nice-to-have'
    """
    try:
        llm_service = get_llm_service()
        importance = await llm_service.classify_skill_importance(
            skill=skill,
            jd_text=jd_text,
            must_have_skills=job_must_have,
            nice_to_have_skills=job_nice_to_have
        )
        logger.debug(f"LLM classified '{skill}' as '{importance}'")
        return importance

    except Exception as e:
        logger.warning(f"LLM classification failed for '{skill}': {e}. Using fallback.")

        # Fallback to rule-based classification
        if any(normalize_skill(skill) == normalize_skill(mh) for mh in job_must_have):
            return 'critical'
        elif any(normalize_skill(skill) == normalize_skill(nth) for nth in job_nice_to_have):
            return 'nice-to-have'
        else:
            return 'important'


async def generate_job_specific_positioning(
    skill: str,
    importance: str,
    user_skills: List[str],
    job_priorities: List[str]
) -> str:
    """
    Generate job-specific positioning strategy using LLM (Task 2.3).

    Creates dynamic, context-aware positioning strategies that reference
    the user's actual skills and the job's specific priorities.

    Args:
        skill: The missing skill
        importance: Skill importance level
        user_skills: User's actual skills
        job_priorities: Job's core priorities

    Returns:
        Personalized positioning strategy
    """
    try:
        llm_service = get_llm_service()
        strategy = await llm_service.generate_positioning_strategy(
            skill=skill,
            importance=importance,
            user_skills=user_skills,
            job_priorities=job_priorities
        )
        logger.debug(f"Generated LLM positioning for '{skill}'")
        return strategy

    except Exception as e:
        logger.warning(f"LLM positioning generation failed for '{skill}': {e}. Using fallback.")

        # Fallback to template-based strategy
        related = get_related_skills(skill)
        templates = POSITIONING_TEMPLATES.get(importance, POSITIONING_TEMPLATES['important'])

        if related:
            return templates[0].format(
                related_skills=', '.join(related[:3]),
                skill_area=skill,
                skill=skill
            )
        else:
            return templates[1].format(
                related_skills='related experience',
                skill_area=skill,
                skill=skill
            )


async def compute_missing_skills(
    job_skills: List[str],
    job_must_have: List[str],
    job_nice_to_have: List[str],
    matched_skill_names: Set[str],
    jd_text: str = "",
    user_skills: List[str] = None,
    job_priorities: List[str] = None
) -> List[SkillGap]:
    """
    Compute missing skills not present in matched set.

    Enhanced with LLM-based importance classification and job-specific
    positioning strategies (Tasks 2.2, 2.3).

    Args:
        job_skills: All job skills
        job_must_have: Must-have capabilities
        job_nice_to_have: Nice-to-have capabilities
        matched_skill_names: Set of already matched skill names
        jd_text: Full job description text (for LLM context)
        user_skills: User's skills (for personalized positioning)
        job_priorities: Job's core priorities (for contextual strategies)

    Returns:
        List of skill gaps with enhanced categorization and positioning
    """
    missing_skills: List[SkillGap] = []
    user_skills = user_skills or []
    job_priorities = job_priorities or []

    for skill in job_skills:
        if normalize_skill(skill) not in {normalize_skill(s) for s in matched_skill_names}:
            # Enhanced importance classification (Task 2.2)
            if jd_text:
                importance = await classify_skill_importance_with_context(
                    skill=skill,
                    jd_text=jd_text,
                    job_must_have=job_must_have,
                    job_nice_to_have=job_nice_to_have
                )
            else:
                # Fallback to original logic
                if any(normalize_skill(skill) == normalize_skill(mh) for mh in job_must_have):
                    importance = 'critical'
                elif any(normalize_skill(skill) == normalize_skill(req) for req in job_skills[:len(job_skills)//2]):
                    importance = 'important'
                else:
                    importance = 'nice-to-have'

            # Job-specific positioning strategy (Task 2.3)
            if user_skills:
                strategy = await generate_job_specific_positioning(
                    skill=skill,
                    importance=importance,
                    user_skills=user_skills,
                    job_priorities=job_priorities
                )
            else:
                # Fallback to template-based strategy
                related = get_related_skills(skill)
                templates = POSITIONING_TEMPLATES.get(importance, POSITIONING_TEMPLATES['important'])

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


async def compute_weak_signals(
    job_skills: List[str],
    user_profile: UserSkillProfile,
    matched_skill_names: Set[str],
    missing_skill_names: Set[str],
    user_bullets: List[Bullet] = None
) -> List[WeakSignal]:
    """
    Identify weak signals: skills where user has related capability but not direct match.

    Enhanced with semantic similarity detection (Task 2.4):
    - Uses semantic matching to find adjacent capabilities
    - Extracts actual bullet text as evidence
    - Ranks weak signals by similarity score
    - Generates specific strengthening strategies

    Args:
        job_skills: All job skills
        user_profile: User's skill profile
        matched_skill_names: Already matched skills
        missing_skill_names: Skills with no match
        user_bullets: User's bullets for extracting evidence

    Returns:
        List of weak signals with ranked evidence and strategies
    """
    weak_signals: List[WeakSignal] = []
    user_skills = user_profile.skills + user_profile.capabilities
    user_bullets = user_bullets or []

    # Prepare embedding service for semantic matching
    embedding_service = get_embedding_service()

    for job_skill in job_skills:
        normalized_job_skill = normalize_skill(job_skill)

        # Skip if already matched
        if normalized_job_skill in {normalize_skill(s) for s in matched_skill_names}:
            continue

        # Only process missing skills
        if normalized_job_skill not in {normalize_skill(s) for s in missing_skill_names}:
            continue

        # Find related skills using both mapping and semantic similarity
        related_skills_mapping = get_related_skills(job_skill)
        user_related_from_mapping = [
            skill for skill in user_skills
            if any(normalize_skill(skill) == normalize_skill(rel) for rel in related_skills_mapping)
        ]

        # Semantic similarity with user skills (Task 2.4)
        semantic_matches = []
        try:
            # Use compute_text_similarity which checks predefined mappings first
            for user_skill in user_skills:
                similarity = await embedding_service.compute_text_similarity(job_skill, user_skill)
                if 0.4 <= similarity < 0.7:  # Weak signal range
                    semantic_matches.append((user_skill, similarity))

            # Sort by similarity score
            semantic_matches.sort(key=lambda x: x[1], reverse=True)

        except Exception as e:
            logger.warning(f"Semantic weak signal detection failed for '{job_skill}': {e}")

        # Combine mapping-based and semantic matches
        all_related = list(set(user_related_from_mapping + [skill for skill, _ in semantic_matches[:3]]))

        if all_related:
            # Extract actual bullet text as evidence (Task 2.4)
            current_evidence = []

            for related_skill in all_related[:3]:
                # Find bullets that mention this related skill
                related_bullets = [
                    bullet for bullet in user_bullets
                    if bullet.tags and related_skill in bullet.tags
                ]

                if related_bullets:
                    # Use actual bullet text (first bullet for this skill)
                    bullet = related_bullets[0]
                    # Handle None case safely
                    text = bullet.text or ""
                    truncated = text[:100] + "..." if len(text) > 100 else text
                    current_evidence.append(truncated)
                else:
                    # Fallback to generic evidence
                    current_evidence.append(f"Experience with {related_skill} (related to {job_skill})")

            # Generate specific strengthening strategy (Task 2.4)
            if semantic_matches:
                top_match_skill, top_similarity = semantic_matches[0]
                strengthening_strategy = (
                    f"Your experience with {top_match_skill} (similarity: {top_similarity:.0%}) provides "
                    f"a foundation for {job_skill}. To strengthen this connection: "
                    f"1) Add bullets that explicitly bridge from {top_match_skill} to {job_skill}-related work, "
                    f"2) Highlight transferable concepts and methodologies, "
                    f"3) Consider adding a side project or certification in {job_skill} to demonstrate commitment."
                )
            else:
                strengthening_strategy = (
                    f"Emphasize how experience with {', '.join(all_related[:2])} "
                    f"provides strong foundation for {job_skill}. Reframe existing bullets to "
                    f"explicitly connect these skills to {job_skill}-relevant outcomes. "
                    f"Add specific examples showing conceptual overlap and learning agility."
                )

            weak_signals.append(WeakSignal(
                skill=job_skill,
                current_evidence=current_evidence[:3],  # Top 3 evidence items
                strengthening_strategy=strengthening_strategy,
            ))

    # Rank weak signals by number of evidence items (more evidence = stronger weak signal)
    weak_signals.sort(key=lambda ws: len(ws.current_evidence), reverse=True)

    return weak_signals


def compute_skill_match_score(
    matched: List[SkillMatch],
    missing: List[SkillGap],
    weak: List[WeakSignal],
    job_must_have: List[str]
) -> float:
    """
    Calculate overall skill match score (0-100).

    Revised formula to better reflect actual qualification:
    - Overall match ratio: 50% weight (matched vs total requirements)
    - Match strength quality: 25% weight (average strength of matches)
    - Gap severity: 15% weight (fewer critical gaps = higher score)
    - Weak signals: 10% weight (adjacent capabilities)
    """
    total_requirements = len(matched) + len(missing)

    if total_requirements == 0:
        return 0.0

    # Overall match ratio (50% weight)
    # This is the primary indicator - what fraction of requirements are matched
    match_ratio = len(matched) / total_requirements
    match_ratio_score = match_ratio * 50.0

    # Match strength quality (25% weight)
    # Higher average match strength means better quality matches
    if matched:
        avg_match_strength = sum(m.match_strength for m in matched) / len(matched)
    else:
        avg_match_strength = 0.0
    quality_score = avg_match_strength * 25.0

    # Gap severity (15% weight)
    # Fewer critical gaps = higher score
    critical_gaps = len([g for g in missing if g.importance == 'critical'])
    important_gaps = len([g for g in missing if g.importance == 'important'])

    if not missing:
        gap_score = 15.0  # No gaps = full points
    else:
        # Weight critical gaps more heavily
        weighted_gaps = (critical_gaps * 2) + important_gaps
        max_weighted = len(missing) * 2  # Worst case: all critical
        gap_ratio = 1 - (weighted_gaps / max(max_weighted, 1))
        gap_score = gap_ratio * 15.0

    # Weak signals (10% weight)
    # Having weak signals shows adjacent capabilities
    if weak:
        weak_signal_score = min((len(weak) / max(len(missing), 1)) * 10.0, 10.0)
    else:
        weak_signal_score = 0.0

    total_score = match_ratio_score + quality_score + gap_score + weak_signal_score

    logger.debug(f"Score breakdown: match_ratio={match_ratio_score:.1f}, "
                 f"quality={quality_score:.1f}, gap={gap_score:.1f}, "
                 f"weak_signal={weak_signal_score:.1f}, total={total_score:.1f}")

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


def save_skill_gap_analysis(
    db: Session,
    job_profile_id: int,
    user_id: int,
    analysis: SkillGapResponse
) -> None:
    """
    Persist skill gap analysis to JobProfile.skill_gap_analysis JSON column.

    Stores the analysis results with timestamp for caching and retrieval.

    Args:
        db: Database session
        job_profile_id: ID of the job profile
        user_id: ID of the user
        analysis: Skill gap analysis result to save

    Raises:
        ValueError: If job profile not found
    """
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile:
        raise ValueError(f"Job profile {job_profile_id} not found")

    # Convert analysis to dict and add metadata
    analysis_dict = analysis.model_dump()
    analysis_dict['user_id'] = user_id
    analysis_dict['cached_at'] = datetime.utcnow().isoformat()

    # Initialize skill_gap_analysis as dict if None
    if job_profile.skill_gap_analysis is None:
        job_profile.skill_gap_analysis = {}

    # Store analysis keyed by user_id
    job_profile.skill_gap_analysis[str(user_id)] = analysis_dict

    db.commit()
    logger.info(f"Saved skill gap analysis for job_profile_id={job_profile_id}, user_id={user_id}")


def get_cached_skill_gap_analysis(
    db: Session,
    job_profile_id: int,
    user_id: int,
    max_age_hours: int = 24
) -> Optional[SkillGapResponse]:
    """
    Retrieve cached skill gap analysis from database if available and fresh.

    Args:
        db: Database session
        job_profile_id: ID of the job profile
        user_id: ID of the user
        max_age_hours: Maximum age of cached analysis in hours (default 24)

    Returns:
        SkillGapResponse if cached and fresh, None otherwise
    """
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile or not job_profile.skill_gap_analysis:
        return None

    # Get analysis for this user
    user_analysis = job_profile.skill_gap_analysis.get(str(user_id))
    if not user_analysis:
        return None

    # Check cache freshness
    cached_at_str = user_analysis.get('cached_at')
    if not cached_at_str:
        logger.warning(f"Cached analysis for job_profile_id={job_profile_id}, user_id={user_id} missing timestamp")
        return None

    try:
        cached_at = datetime.fromisoformat(cached_at_str)
        age_hours = (datetime.utcnow() - cached_at).total_seconds() / 3600

        if age_hours > max_age_hours:
            logger.info(f"Cached analysis expired (age: {age_hours:.1f}h > {max_age_hours}h)")
            return None

        # Reconstruct SkillGapResponse from cached dict
        # Remove only the cached_at metadata (keep user_id as it's part of schema)
        analysis_data = {k: v for k, v in user_analysis.items() if k != 'cached_at'}
        cached_analysis = SkillGapResponse(**analysis_data)

        logger.info(f"Retrieved cached skill gap analysis (age: {age_hours:.1f}h)")
        return cached_analysis

    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse cached analysis: {e}")
        return None


async def analyze_skill_gap(
    job_profile_id: int,
    user_id: int,
    db: Session,
    user_skill_profile: Optional[UserSkillProfile] = None,
    use_cache: bool = True
) -> SkillGapResponse:
    """
    Compute comprehensive skill gap analysis between job requirements and user profile.

    Main entry point for skill gap analysis. Analyzes matched skills, identifies gaps,
    detects weak signals, and generates positioning strategies.

    Enhanced with:
    - Semantic skill matching (Task 2.1)
    - LLM-based importance classification (Task 2.2)
    - Job-specific positioning strategies (Task 2.3)
    - Enhanced weak signal detection (Task 2.4)
    - Database caching (Task 2.6)

    Args:
        job_profile_id: ID of the job profile to analyze against
        user_id: ID of the user
        db: Database session
        user_skill_profile: Optional pre-built user skill profile (if None, will be built from DB)
        use_cache: Whether to use cached analysis if available (default True)

    Returns:
        SkillGapResponse with comprehensive analysis and positioning guidance

    Raises:
        ValueError: If job profile not found or missing required data
    """
    # Check for cached analysis first
    if use_cache:
        cached_analysis = get_cached_skill_gap_analysis(db, job_profile_id, user_id)
        if cached_analysis:
            logger.info(f"Using cached skill gap analysis for job_profile_id={job_profile_id}, user_id={user_id}")
            return cached_analysis

    # Fetch job profile
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile:
        raise ValueError(f"Job profile {job_profile_id} not found")

    # Extract job requirements
    job_skills = job_profile.extracted_skills or []
    job_must_have = job_profile.must_have_capabilities or []
    job_nice_to_have = job_profile.nice_to_have_capabilities or []
    job_priorities = job_profile.core_priorities or []
    jd_text = job_profile.raw_jd_text or ""

    # Use extracted skills for matching (these are actual skill names like "AI Strategy")
    # Note: must_have_capabilities contain full sentences (e.g., "3-6 years of experience...")
    # which don't match well against skill tags, so we only use extracted_skills
    all_job_requirements = list(set(job_skills))

    if not all_job_requirements:
        raise ValueError(f"Job profile {job_profile_id} has no extracted skills or capabilities")

    # Build user skill profile if not provided
    if user_skill_profile is None:
        user_skill_profile = await build_user_skill_profile(user_id, db)

    # Fetch user bullets for evidence
    user_bullets = db.query(Bullet).filter(
        Bullet.user_id == user_id,
        Bullet.retired == False
    ).all()

    # Compute matched skills (now async with semantic matching)
    # Use all_job_requirements to match against both extracted skills AND must-have capabilities
    matched_skills = await compute_matched_skills(all_job_requirements, user_skill_profile, user_bullets)
    matched_skill_names = {m.skill for m in matched_skills}

    logger.info(f"Skill gap analysis: {len(all_job_requirements)} job requirements, "
                f"{len(user_skill_profile.skills)} user skills, "
                f"{len(matched_skills)} matches found")

    # Compute missing skills (gaps) with enhanced categorization and positioning
    user_all_skills = user_skill_profile.skills + user_skill_profile.capabilities + user_skill_profile.bullet_tags
    missing_skills = await compute_missing_skills(
        job_skills=all_job_requirements,  # Use combined list for gap analysis
        job_must_have=job_must_have,
        job_nice_to_have=job_nice_to_have,
        matched_skill_names=matched_skill_names,
        jd_text=jd_text,
        user_skills=user_all_skills,
        job_priorities=job_priorities
    )
    missing_skill_names = {g.skill for g in missing_skills}

    # Compute weak signals with semantic similarity
    weak_signals = await compute_weak_signals(
        job_skills=all_job_requirements,  # Use combined list for weak signal detection
        user_profile=user_skill_profile,
        matched_skill_names=matched_skill_names,
        missing_skill_names=missing_skill_names,
        user_bullets=user_bullets
    )

    # Filter skill_gaps to exclude skills that are in weak_signals
    # This makes the two categories mutually exclusive:
    # - skill_gaps: missing skills with NO adjacent capabilities
    # - weak_signals: missing skills where user has related experience
    weak_signal_skill_names = {ws.skill for ws in weak_signals}
    missing_skills = [g for g in missing_skills if g.skill not in weak_signal_skill_names]

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
    analysis_result = SkillGapResponse(
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

    # Save analysis to database for caching
    try:
        save_skill_gap_analysis(db, job_profile_id, user_id, analysis_result)
    except Exception as e:
        logger.warning(f"Failed to cache skill gap analysis: {e}")
        # Don't fail the entire analysis if caching fails

    return analysis_result
