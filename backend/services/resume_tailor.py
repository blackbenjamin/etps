"""
Resume Tailoring Service

Intelligently selects and optimizes resume content (bullets, skills, summary)
to maximize alignment with specific job requirements.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from db.models import Bullet, Experience, JobProfile, User
from schemas.resume_tailor import (
    SelectedBullet,
    SelectedRole,
    SelectedSkill,
    TailoredResume,
    TailoringRationale,
)
from schemas.skill_gap import SkillGapResponse
from services.skill_gap import (
    SKILL_SYNONYMS,
    analyze_skill_gap,
    normalize_skill,
    find_skill_match,
)
from services.llm.base import BaseLLM


# Banned phrases that should be removed from generated summaries
BANNED_PHRASES = [
    "seasoned professional",
    "results-oriented",
    "proven track record",
    "dynamic",
    "synergy",
    "leverage",
    "best-in-class",
    "world-class",
    "cutting-edge",
    "innovative thinker",
    "go-getter",
    "team player",
    "detail-oriented",
    "hard-working",
    "passionate about",
]


def select_bullets_for_role(
    experience: Experience,
    bullets: List[Bullet],
    job_profile: JobProfile,
    skill_gap_result: SkillGapResponse,
    max_bullets: int = 4
) -> List[SelectedBullet]:
    """
    Select optimal bullets for a role based on multi-factor scoring.

    Scoring formula:
    - Tag matching (40%): How well bullet tags align with job skills
    - Relevance score (30%): Pre-computed relevance scores for bullets
    - Usage/recency (20%): Prefer less-used bullets for freshness
    - Type diversity (10%): Bonus for diverse bullet types

    Args:
        experience: The experience/role to select bullets for
        bullets: List of all bullets for this experience
        job_profile: Target job profile
        skill_gap_result: Skill gap analysis for guidance
        max_bullets: Maximum number of bullets to select

    Returns:
        List of selected bullets with scoring metadata
    """
    if not bullets:
        return []

    # Filter out retired bullets
    active_bullets = [b for b in bullets if not b.retired]
    if not active_bullets:
        return []

    # Extract job skills and matched skills for scoring
    job_skills = job_profile.extracted_skills or []
    matched_skills = {m.skill for m in skill_gap_result.matched_skills}
    priority_tags = skill_gap_result.bullet_selection_guidance.get('prioritize_tags', [])

    # Score each bullet
    scored_bullets: List[Tuple[Bullet, float, str]] = []

    for bullet in active_bullets:
        # 1. Tag matching score (40%)
        tag_score = 0.0
        matching_tags = []
        if bullet.tags:
            for tag in bullet.tags:
                # Check against matched skills
                for job_skill in job_skills:
                    if find_skill_match(job_skill, [tag]):
                        tag_score += 1.0
                        matching_tags.append(tag)
                        break

                # Bonus for priority tags
                if tag in priority_tags:
                    tag_score += 0.5
                    if tag not in matching_tags:
                        matching_tags.append(tag)

        # Normalize tag score (cap at 1.0)
        tag_score = min(tag_score / max(len(job_skills), 1), 1.0) * 0.4

        # 2. Relevance score (30%)
        relevance_score = 0.0
        if bullet.relevance_scores:
            # Average relevance for matched skills
            relevant_scores = [
                score for skill, score in bullet.relevance_scores.items()
                if any(find_skill_match(ms, [skill]) for ms in matched_skills)
            ]
            if relevant_scores:
                relevance_score = (sum(relevant_scores) / len(relevant_scores)) * 0.3
            else:
                # Use max relevance if no matched skills
                relevance_score = max(bullet.relevance_scores.values(), default=0.5) * 0.3
        else:
            relevance_score = 0.5 * 0.3  # Default mid-range score

        # 3. Usage/recency score (20%) - prefer less used bullets
        usage_score = 0.0
        if bullet.usage_count == 0:
            usage_score = 1.0 * 0.2  # Never used - highest score
        else:
            # Exponential decay - more used = lower score
            usage_score = (1.0 / (1.0 + bullet.usage_count * 0.5)) * 0.2

        # 4. Type diversity bonus (10%)
        type_score = 0.1  # Default
        if bullet.bullet_type:
            # Slight preference for achievement and metric_impact types
            if bullet.bullet_type in ['achievement', 'metric_impact']:
                type_score = 0.15
            elif bullet.bullet_type == 'responsibility':
                type_score = 0.08

        # Calculate total score
        total_score = tag_score + relevance_score + usage_score + type_score

        # Build selection reason
        reason_parts = []
        if matching_tags:
            reason_parts.append(f"Matches key skills: {', '.join(matching_tags[:3])}")
        if bullet.bullet_type in ['achievement', 'metric_impact']:
            reason_parts.append(f"Strong {bullet.bullet_type} statement")
        if bullet.usage_count == 0:
            reason_parts.append("Fresh content (not recently used)")

        selection_reason = "; ".join(reason_parts) if reason_parts else "Relevant experience"

        scored_bullets.append((bullet, total_score, selection_reason))

    # Sort by score descending
    scored_bullets.sort(key=lambda x: x[1], reverse=True)

    # Select top N bullets, ensuring type diversity
    selected: List[SelectedBullet] = []
    type_counts: Dict[str, int] = {}

    for bullet, score, reason in scored_bullets:
        if len(selected) >= max_bullets:
            break

        # Encourage type diversity (no more than max_bullets - 1 of same type)
        bullet_type = bullet.bullet_type or 'general'
        if type_counts.get(bullet_type, 0) >= max_bullets - 1:
            continue

        selected.append(SelectedBullet(
            bullet_id=bullet.id,
            text=bullet.text,
            relevance_score=round(score, 2),
            was_rewritten=False,  # No rewriting in initial implementation
            original_text=None,
            tags=bullet.tags or [],
            selection_reason=reason,
        ))

        type_counts[bullet_type] = type_counts.get(bullet_type, 0) + 1

    # If we didn't get enough, fill with remaining bullets
    if len(selected) < max_bullets:
        remaining_bullets = [
            (b, s, r) for b, s, r in scored_bullets
            if not any(sb.bullet_id == b.id for sb in selected)
        ]
        for bullet, score, reason in remaining_bullets[:max_bullets - len(selected)]:
            selected.append(SelectedBullet(
                bullet_id=bullet.id,
                text=bullet.text,
                relevance_score=round(score, 2),
                was_rewritten=False,
                original_text=None,
                tags=bullet.tags or [],
                selection_reason=reason,
            ))

    return selected


def select_and_order_skills(
    user_bullets: List[Bullet],
    job_profile: JobProfile,
    skill_gap_result: SkillGapResponse,
    max_skills: int = 12
) -> List[SelectedSkill]:
    """
    Select and order skills for resume skills section using tier-based approach.

    Tier-based selection:
    - Tier 1: Critical matched skills (high match strength)
    - Tier 2: Strong matched skills (match_strength >= 0.7)
    - Tier 3: Important job requirements (even if weak match)
    - Tier 4: Weak signals and transferable skills

    Args:
        user_bullets: User's bullet points with tags
        job_profile: Target job profile
        skill_gap_result: Skill gap analysis result
        max_skills: Maximum number of skills to include

    Returns:
        Ordered list of selected skills with metadata
    """
    selected_skills: List[SelectedSkill] = []
    selected_skill_names: Set[str] = set()

    # Tier 1: Critical matched skills (match_strength >= 0.75)
    critical_matches = [
        m for m in skill_gap_result.matched_skills
        if m.match_strength >= 0.75
    ]
    for match in sorted(critical_matches, key=lambda m: m.match_strength, reverse=True):
        if len(selected_skills) >= max_skills:
            break

        normalized = normalize_skill(match.skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=match.skill,
                priority_score=match.match_strength,
                match_type="direct_match",
                source="job_requirements",
            ))
            selected_skill_names.add(normalized)

    # Tier 2: Strong matched skills (0.5 <= match_strength < 0.75)
    strong_matches = [
        m for m in skill_gap_result.matched_skills
        if 0.5 <= m.match_strength < 0.75
    ]
    for match in sorted(strong_matches, key=lambda m: m.match_strength, reverse=True):
        if len(selected_skills) >= max_skills:
            break

        normalized = normalize_skill(match.skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=match.skill,
                priority_score=match.match_strength,
                match_type="direct_match",
                source="job_requirements",
            ))
            selected_skill_names.add(normalized)

    # Tier 3: Important job requirements (from job profile)
    job_skills = job_profile.extracted_skills or []
    must_have = job_profile.must_have_capabilities or []

    for skill in must_have[:max_skills - len(selected_skills)]:
        normalized = normalize_skill(skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=skill,
                priority_score=0.7,  # Moderate priority
                match_type="adjacent_skill",
                source="job_requirements",
            ))
            selected_skill_names.add(normalized)

    # Tier 4: Weak signals (adjacent capabilities)
    weak_signals = skill_gap_result.weak_signals
    for weak in weak_signals[:max_skills - len(selected_skills)]:
        normalized = normalize_skill(weak.skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=weak.skill,
                priority_score=0.5,
                match_type="transferable",
                source="user_master_resume",
            ))
            selected_skill_names.add(normalized)

    # If still under max_skills, add remaining matched skills
    remaining_matches = [
        m for m in skill_gap_result.matched_skills
        if normalize_skill(m.skill) not in selected_skill_names
    ]
    for match in sorted(remaining_matches, key=lambda m: m.match_strength, reverse=True):
        if len(selected_skills) >= max_skills:
            break

        normalized = normalize_skill(match.skill)
        if normalized not in selected_skill_names:
            selected_skills.append(SelectedSkill(
                skill=match.skill,
                priority_score=match.match_strength,
                match_type="direct_match",
                source="job_requirements",
            ))
            selected_skill_names.add(normalized)

    return selected_skills[:max_skills]


async def generate_tailored_summary(
    user_name: str,
    experiences: List[Experience],
    job_profile: JobProfile,
    skill_gap_result: SkillGapResponse,
    selected_skills: List[SelectedSkill],
    llm: BaseLLM
) -> str:
    """
    Generate tailored executive summary optimized for target job.

    Uses LLM to generate 60-80 word summary emphasizing matched skills,
    relevant seniority, and key achievements aligned with job priorities.

    Args:
        user_name: User's full name
        experiences: User's work experiences
        job_profile: Target job profile
        skill_gap_result: Skill gap analysis
        selected_skills: Skills selected for resume
        llm: LLM instance for generation

    Returns:
        Tailored professional summary (60-80 words)
    """
    # Extract key information for summary
    top_skills = [s.skill for s in selected_skills[:5]]
    matched_skills = [m.skill for m in skill_gap_result.matched_skills[:3]]
    seniority = job_profile.seniority or "experienced"
    job_title = job_profile.job_title

    # Calculate years of experience
    years_exp = 0
    if experiences:
        for exp in experiences:
            years = (exp.end_date or datetime.now().date()).year - exp.start_date.year
            years_exp += max(years, 0)

    # Build context for LLM
    context = {
        'job_title': job_title,
        'seniority': seniority,
        'top_skills': top_skills,
        'matched_skills': matched_skills,
        'years_experience': years_exp,
        'job_priorities': job_profile.core_priorities or [],
    }

    # Generate summary using LLM
    prompt = f"""Generate a professional resume summary (60-80 words) for a candidate targeting this role:

Job Title: {job_title}
Seniority: {seniority}

The candidate has {years_exp}+ years of experience with strong expertise in:
{', '.join(top_skills[:5])}

Key skills that match job requirements:
{', '.join(matched_skills)}

Job priorities to address:
{', '.join(job_profile.core_priorities[:3]) if job_profile.core_priorities else 'N/A'}

Write a compelling summary that:
1. Emphasizes matched skills and relevant experience
2. Aligns with job seniority level
3. Addresses 1-2 key job priorities
4. Is concrete and achievement-focused (avoid generic phrases)
5. Is exactly 60-80 words

Summary:"""

    # For MockLLM, use template-based generation
    if llm.__class__.__name__ == 'MockLLM':
        summary = _generate_mock_summary(
            seniority=seniority,
            years_exp=years_exp,
            top_skills=top_skills,
            matched_skills=matched_skills,
            job_title=job_title,
        )
    else:
        summary = await llm.generate_text(prompt, max_tokens=200)

    # Post-process: remove banned phrases using word-boundary regex
    # Note: This is a basic cleanup for summaries. More rigorous enforcement
    # should be applied during cover letter generation (PRD Section 3.5)
    for phrase in BANNED_PHRASES:
        # Use word boundaries to avoid partial matches (e.g., "passionate" in "compassionate")
        pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
        summary = pattern.sub('', summary)

    # Clean up extra spaces and formatting
    summary = " ".join(summary.split())

    return summary.strip()


def _generate_mock_summary(
    seniority: str,
    years_exp: int,
    top_skills: List[str],
    matched_skills: List[str],
    job_title: str,
) -> str:
    """
    Generate mock summary using template for development/testing.

    Args:
        seniority: Seniority level
        years_exp: Years of experience
        top_skills: Top skills to highlight
        matched_skills: Matched skills
        job_title: Target job title

    Returns:
        Template-based summary
    """
    # Determine role type
    role_descriptor = "professional"
    if "director" in seniority.lower() or "vp" in seniority.lower():
        role_descriptor = "leader"
    elif "senior" in seniority.lower():
        role_descriptor = "specialist"

    # Build summary
    skills_str = ", ".join(matched_skills[:3]) if matched_skills else ", ".join(top_skills[:3])

    summary = (
        f"{role_descriptor.capitalize()} with {years_exp}+ years of experience "
        f"specializing in {skills_str}. Demonstrated expertise in delivering "
        f"impactful solutions through technical excellence and strategic execution. "
        f"Proven ability to drive results in complex environments requiring "
        f"{top_skills[0] if top_skills else 'technical expertise'}."
    )

    return summary


async def tailor_resume(
    job_profile_id: int,
    user_id: int,
    db: Session,
    max_bullets_per_role: int = 4,
    max_skills: int = 12,
    custom_instructions: Optional[str] = None,
    llm: Optional[BaseLLM] = None,
) -> TailoredResume:
    """
    Main orchestrator: Generate complete tailored resume for specific job.

    Workflow:
    1. Fetch job profile and user data
    2. Analyze skill gaps
    3. Select optimal bullets for each role
    4. Select and order skills
    5. Generate tailored summary
    6. Build comprehensive rationale
    7. Validate constraints

    Args:
        job_profile_id: ID of target job profile
        user_id: User ID
        db: Database session
        max_bullets_per_role: Maximum bullets per experience (2-8)
        max_skills: Maximum skills in skills section (5-20)
        custom_instructions: Optional user instructions for tailoring
        llm: Optional LLM instance (will use MockLLM if not provided)

    Returns:
        Complete tailored resume with rationale

    Raises:
        ValueError: If job profile or user not found, or invalid parameters
    """
    # Validate parameters
    if not 2 <= max_bullets_per_role <= 8:
        raise ValueError("max_bullets_per_role must be between 2 and 8")
    if not 5 <= max_skills <= 20:
        raise ValueError("max_skills must be between 5 and 20")

    # Fetch job profile
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile:
        raise ValueError(f"Job profile {job_profile_id} not found")

    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Fetch user's experiences (ordered by order field, then by start_date desc)
    experiences = db.query(Experience).filter(
        Experience.user_id == user_id
    ).order_by(
        Experience.order.asc(),
        Experience.start_date.desc()
    ).all()

    if not experiences:
        raise ValueError(f"User {user_id} has no experiences")

    # Fetch all user's bullets
    all_bullets = db.query(Bullet).filter(
        Bullet.user_id == user_id,
        Bullet.retired == False
    ).all()

    # Analyze skill gap
    skill_gap_result = await analyze_skill_gap(
        job_profile_id=job_profile_id,
        user_id=user_id,
        db=db,
    )

    # Select bullets for each role
    selected_roles: List[SelectedRole] = []
    role_emphasis: Dict[int, str] = {}

    for experience in experiences:
        # Get bullets for this experience
        exp_bullets = [b for b in all_bullets if b.experience_id == experience.id]

        if not exp_bullets:
            # Skip experiences with no bullets
            continue

        # Select optimal bullets
        selected_bullets = select_bullets_for_role(
            experience=experience,
            bullets=exp_bullets,
            job_profile=job_profile,
            skill_gap_result=skill_gap_result,
            max_bullets=max_bullets_per_role,
        )

        if not selected_bullets:
            continue

        # Build rationale for this role
        bullet_reasons = [sb.selection_reason for sb in selected_bullets]
        role_rationale = (
            f"Selected {len(selected_bullets)} bullets emphasizing: "
            f"{'; '.join(set([r.split(';')[0] for r in bullet_reasons]))}"
        )

        # Determine role emphasis
        if experience.start_date and experience.end_date:
            months_ago = (datetime.now().date() - experience.end_date).days / 30
            if months_ago < 24:
                emphasis = "Recent relevant experience"
            else:
                emphasis = "Earlier career foundation"
        else:
            emphasis = "Current role (high priority)"

        role_emphasis[experience.id] = emphasis

        # Build selected role
        selected_roles.append(SelectedRole(
            experience_id=experience.id,
            job_title=experience.job_title,  # IMMUTABLE
            employer_name=experience.employer_name,  # IMMUTABLE
            location=experience.location,  # IMMUTABLE
            start_date=experience.start_date.isoformat(),
            end_date=experience.end_date.isoformat() if experience.end_date else None,
            selected_bullets=selected_bullets,
            bullet_selection_rationale=role_rationale,
        ))

    # Select and order skills
    selected_skills = select_and_order_skills(
        user_bullets=all_bullets,
        job_profile=job_profile,
        skill_gap_result=skill_gap_result,
        max_skills=max_skills,
    )

    # Generate tailored summary
    if llm is None:
        from services.llm.mock_llm import MockLLM
        llm = MockLLM()

    tailored_summary = await generate_tailored_summary(
        user_name=user.full_name,
        experiences=experiences,
        job_profile=job_profile,
        skill_gap_result=skill_gap_result,
        selected_skills=selected_skills,
        llm=llm,
    )

    # Build comprehensive rationale
    rationale = TailoringRationale(
        summary_approach=(
            f"Generated summary emphasizing {len(selected_skills[:5])} top matched skills "
            f"({', '.join([s.skill for s in selected_skills[:3]])}) aligned with "
            f"{job_profile.seniority or 'target'} seniority level and job priorities"
        ),
        bullet_selection_strategy=(
            f"Multi-factor scoring (40% tag matching, 30% relevance, 20% freshness, 10% diversity). "
            f"Selected {sum(len(r.selected_bullets) for r in selected_roles)} total bullets "
            f"across {len(selected_roles)} roles, prioritizing matched skills: "
            f"{', '.join(skill_gap_result.bullet_selection_guidance.get('prioritize_tags', [])[:5])}"
        ),
        skills_ordering_logic=(
            f"Tier-based selection: Tier 1 (critical matches), Tier 2 (strong matches), "
            f"Tier 3 (must-have requirements), Tier 4 (transferable skills). "
            f"Selected {len(selected_skills)} skills with {len([s for s in selected_skills if s.match_type == 'direct_match'])} "
            f"direct matches"
        ),
        role_emphasis=role_emphasis,
        gaps_addressed=[
            f"{gap.skill} ({gap.importance}): {gap.positioning_strategy[:100]}..."
            for gap in skill_gap_result.skill_gaps[:3]
        ],
        strengths_highlighted=[
            f"{match.skill} (strength: {match.match_strength:.2f})"
            for match in sorted(skill_gap_result.matched_skills, key=lambda m: m.match_strength, reverse=True)[:5]
        ],
    )

    # Calculate match score (use skill gap score + adjustments)
    base_match_score = skill_gap_result.skill_match_score

    # Bonus for having enough bullets and skills
    content_bonus = 0.0
    if len(selected_roles) >= 2 and sum(len(r.selected_bullets) for r in selected_roles) >= 8:
        content_bonus += 5.0
    if len(selected_skills) >= max_skills * 0.8:
        content_bonus += 3.0

    match_score = min(base_match_score + content_bonus, 100.0)

    # Validate constraints
    constraints_validated = True
    for role in selected_roles:
        # Check immutable fields are preserved
        exp = next((e for e in experiences if e.id == role.experience_id), None)
        if exp:
            if role.job_title != exp.job_title:
                constraints_validated = False
            if role.employer_name != exp.employer_name:
                constraints_validated = False
            if role.location != exp.location:
                constraints_validated = False

        # Check bullet count constraint
        if len(role.selected_bullets) > max_bullets_per_role:
            constraints_validated = False

    # Check skills count constraint
    if len(selected_skills) > max_skills:
        constraints_validated = False

    # Build final response
    return TailoredResume(
        job_profile_id=job_profile_id,
        user_id=user_id,
        application_id=None,  # Not linked to application yet
        tailored_summary=tailored_summary,
        selected_roles=selected_roles,
        selected_skills=selected_skills,
        rationale=rationale,
        ats_score_estimate=None,  # TODO: Implement ATS scoring
        match_score=round(match_score, 1),
        generated_at=datetime.utcnow().isoformat(),
        constraints_validated=constraints_validated,
    )


async def tailor_resume_with_critic(
    job_profile_id: int,
    user_id: int,
    db: Session,
    max_bullets_per_role: int = 4,
    max_skills: int = 12,
    custom_instructions: Optional[str] = None,
    llm: Optional[BaseLLM] = None,
    max_iterations: int = 3,
    strict_mode: bool = False,
) -> Tuple[TailoredResume, "ResumeCriticResult"]:
    """
    Generate tailored resume with critic-in-the-loop evaluation.

    Implements PRD 4.1-4.5 critic loop:
    1. Generate tailored resume
    2. Run resume critic evaluation
    3. If critic fails, adjust parameters and regenerate (up to max_iterations)
    4. Return best result with critic evaluation

    Adjustment strategy on failure:
    - Iteration 2: Expand bullet selection, prioritize metrics
    - Iteration 3: Relax constraints, focus on must-have requirements

    Args:
        job_profile_id: ID of target job profile
        user_id: User ID
        db: Database session
        max_bullets_per_role: Maximum bullets per experience (2-8)
        max_skills: Maximum skills in skills section (5-20)
        custom_instructions: Optional user instructions for tailoring
        llm: Optional LLM instance
        max_iterations: Maximum critic iterations (default 3)
        strict_mode: If True, treat warnings as errors

    Returns:
        Tuple of (TailoredResume, ResumeCriticResult)

    Raises:
        ValueError: If job profile or user not found
    """
    from schemas.critic import ResumeCriticResult
    from services.critic import evaluate_resume

    # Fetch job profile for critic
    job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
    if not job_profile:
        raise ValueError(f"Job profile {job_profile_id} not found")

    best_resume: Optional[TailoredResume] = None
    best_critic_result: Optional[ResumeCriticResult] = None
    best_quality_score: float = 0.0

    for iteration in range(1, max_iterations + 1):
        # Adjust parameters based on iteration
        iter_max_bullets = max_bullets_per_role
        iter_max_skills = max_skills
        iter_instructions = custom_instructions

        if iteration == 2:
            # Expand bullet selection on second attempt
            iter_max_bullets = min(max_bullets_per_role + 1, 8)
            iter_instructions = (
                f"{custom_instructions or ''} "
                f"Focus on bullets with quantifiable metrics and strong action verbs. "
                f"Prioritize achievement statements."
            ).strip()

        elif iteration == 3:
            # Final attempt: maximize coverage
            iter_max_bullets = min(max_bullets_per_role + 2, 8)
            iter_max_skills = min(max_skills + 2, 20)
            iter_instructions = (
                f"{custom_instructions or ''} "
                f"Maximize coverage of must-have requirements. "
                f"Include all high-impact achievements with metrics."
            ).strip()

        # Generate tailored resume
        try:
            resume = await tailor_resume(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                max_bullets_per_role=iter_max_bullets,
                max_skills=iter_max_skills,
                custom_instructions=iter_instructions,
                llm=llm,
            )
        except ValueError as e:
            # Re-raise validation errors
            raise

        # Run critic evaluation
        resume_dict = resume.model_dump()
        critic_result = await evaluate_resume(
            resume_json=resume_dict,
            job_profile=job_profile,
            db=db,
            user_id=user_id,
            llm=llm,
            strict_mode=strict_mode,
            iteration=iteration,
        )

        # Track best result
        if critic_result.quality_score > best_quality_score:
            best_quality_score = critic_result.quality_score
            best_resume = resume
            best_critic_result = critic_result

        # If passed, return immediately
        if critic_result.passed:
            return resume, critic_result

        # Log iteration for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Resume critic iteration {iteration}/{max_iterations}: "
            f"passed={critic_result.passed}, "
            f"errors={critic_result.error_count}, "
            f"warnings={critic_result.warning_count}, "
            f"quality={critic_result.quality_score}"
        )

        # Check if we should continue
        if not critic_result.should_retry:
            break

    # Return best result (even if not passing)
    if best_resume is None or best_critic_result is None:
        # This shouldn't happen, but handle edge case
        raise ValueError("Failed to generate any resume")

    return best_resume, best_critic_result


async def log_critic_result(
    db: Session,
    application_id: Optional[int],
    critic_result: "ResumeCriticResult",
    resume_json: Dict,
) -> None:
    """
    Log critic evaluation result to database for tracking and analysis.

    Stores the critic result in the application's critic_scores field
    and creates a log entry for auditing.

    Args:
        db: Database session
        application_id: Application ID (if linked)
        critic_result: Critic evaluation result
        resume_json: Resume JSON that was evaluated
    """
    from db.models import Application, LogEntry

    if application_id:
        # Update application with critic scores
        application = db.query(Application).filter(
            Application.id == application_id
        ).first()

        if application:
            # Merge critic scores into existing scores
            existing_scores = application.critic_scores or {}
            existing_scores['resume'] = {
                'passed': critic_result.passed,
                'quality_score': critic_result.quality_score,
                'alignment_score': critic_result.alignment_score,
                'clarity_score': critic_result.clarity_score,
                'impact_score': critic_result.impact_score,
                'tone_score': critic_result.tone_score,
                'ats_overall': critic_result.ats_score.overall_score,
                'error_count': critic_result.error_count,
                'warning_count': critic_result.warning_count,
                'iteration': critic_result.iteration,
                'evaluated_at': critic_result.evaluated_at,
            }
            application.critic_scores = existing_scores
            application.ats_score = critic_result.ats_score.overall_score

            # Create log entry
            log_entry = LogEntry(
                user_id=application.user_id,
                application_id=application_id,
                action='resume_critic',
                details={
                    'passed': critic_result.passed,
                    'quality_score': critic_result.quality_score,
                    'iteration': critic_result.iteration,
                    'issues_count': len(critic_result.issues),
                    'summary': critic_result.evaluation_summary,
                },
            )
            db.add(log_entry)
            db.commit()


def get_critic_feedback_for_revision(
    critic_result: "ResumeCriticResult"
) -> Dict[str, any]:
    """
    Extract actionable feedback from critic result for resume revision.

    Converts critic issues into structured guidance for the next
    tailoring iteration.

    Args:
        critic_result: Critic evaluation result

    Returns:
        Dict with revision guidance:
        - priority_fixes: List of blocking issues to fix
        - suggestions: List of non-blocking improvements
        - weak_areas: Areas needing attention
        - strong_areas: Areas performing well
    """
    priority_fixes = []
    suggestions = []
    weak_areas = []
    strong_areas = []

    # Categorize issues
    for issue in critic_result.issues:
        if issue.severity == 'error':
            priority_fixes.append({
                'type': issue.issue_type,
                'section': issue.section,
                'message': issue.message,
                'fix': issue.recommended_fix,
            })
        elif issue.severity == 'warning':
            suggestions.append({
                'type': issue.issue_type,
                'section': issue.section,
                'message': issue.message,
                'fix': issue.recommended_fix,
            })

    # Identify weak areas based on scores
    if critic_result.alignment_score < 70:
        weak_areas.append('JD alignment - missing key requirements')
    if critic_result.clarity_score < 70:
        weak_areas.append('Bullet clarity - restructure for conciseness')
    if critic_result.impact_score < 50:
        weak_areas.append('Impact orientation - add more metrics and achievements')
    if critic_result.tone_score < 80:
        weak_areas.append('Tone - adjust to be more professional/executive')

    # Identify strong areas
    if critic_result.alignment_score >= 85:
        strong_areas.append(f'Strong JD alignment ({critic_result.alignment_score})')
    if critic_result.clarity_score >= 85:
        strong_areas.append(f'Clear and concise bullets ({critic_result.clarity_score})')
    if critic_result.impact_score >= 70:
        strong_areas.append(f'Good impact orientation ({critic_result.impact_score})')
    if critic_result.ats_score.overall_score >= 80:
        strong_areas.append(f'Strong ATS score ({critic_result.ats_score.overall_score})')

    return {
        'priority_fixes': priority_fixes,
        'suggestions': suggestions[:5],  # Limit to top 5
        'weak_areas': weak_areas,
        'strong_areas': strong_areas,
        'metrics_coverage': f"{critic_result.bullets_with_metrics}/{critic_result.bullets_total} bullets with metrics",
        'weak_verb_count': critic_result.weak_verb_count,
    }
