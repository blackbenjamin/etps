"""
Test script for resume tailoring service.

Demonstrates the usage of the resume tailoring functionality with realistic data.
"""

import asyncio
from datetime import date, datetime
from sqlalchemy.orm import Session

from db.database import get_db, engine
from db.models import Base, User, Experience, Bullet, JobProfile
from services.resume_tailor import (
    select_bullets_for_role,
    select_and_order_skills,
    generate_tailored_summary,
    tailor_resume,
)
from services.llm.mock_llm import MockLLM
from schemas.skill_gap import SkillGapResponse, SkillMatch, SkillGap, WeakSignal


def setup_test_data(db: Session) -> tuple[int, int]:
    """
    Create test data for resume tailoring.

    Returns:
        Tuple of (user_id, job_profile_id)
    """
    # Create test user with unique email
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        full_name="Jane Smith",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create test experiences
    exp1 = Experience(
        user_id=user.id,
        job_title="Senior AI Governance Consultant",
        employer_name="Tech Consulting Firm",
        location="San Francisco, CA",
        start_date=date(2021, 1, 1),
        end_date=None,  # Current role
        description="Leading AI governance initiatives",
        order=0,
    )

    exp2 = Experience(
        user_id=user.id,
        job_title="Machine Learning Engineer",
        employer_name="Startup AI Inc",
        location="New York, NY",
        start_date=date(2018, 6, 1),
        end_date=date(2020, 12, 31),
        description="Built ML models and infrastructure",
        order=1,
    )

    db.add_all([exp1, exp2])
    db.commit()
    db.refresh(exp1)
    db.refresh(exp2)

    # Create test bullets for exp1
    bullets_exp1 = [
        Bullet(
            user_id=user.id,
            experience_id=exp1.id,
            text="Developed comprehensive AI governance framework for Fortune 500 clients, ensuring compliance with regulatory requirements and reducing risk by 40%",
            tags=["ai_governance", "consulting", "compliance", "risk_management"],
            seniority_level="senior",
            bullet_type="achievement",
            relevance_scores={"ai_governance": 0.95, "consulting": 0.90, "compliance": 0.85},
            usage_count=0,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp1.id,
            text="Led cross-functional workshops with C-suite executives to align stakeholders on ethical AI principles and implementation roadmap",
            tags=["stakeholder_management", "leadership", "ai_ethics", "consulting"],
            seniority_level="senior",
            bullet_type="achievement",
            relevance_scores={"stakeholder_management": 0.92, "leadership": 0.88},
            usage_count=1,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp1.id,
            text="Conducted risk assessments for 15+ AI/ML systems, identifying vulnerabilities and recommending mitigation strategies",
            tags=["risk_management", "ai_governance", "assessment"],
            seniority_level="senior",
            bullet_type="metric_impact",
            relevance_scores={"risk_management": 0.90, "ai_governance": 0.85},
            usage_count=0,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp1.id,
            text="Managed client relationships and consulting engagements across multiple industries including healthcare, finance, and technology",
            tags=["consulting", "client_management", "industry_knowledge"],
            seniority_level="senior",
            bullet_type="responsibility",
            relevance_scores={"consulting": 0.80, "client_management": 0.85},
            usage_count=2,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp1.id,
            text="Published thought leadership articles on AI governance best practices, establishing firm as industry authority",
            tags=["thought_leadership", "writing", "ai_governance"],
            seniority_level="senior",
            bullet_type="achievement",
            relevance_scores={"thought_leadership": 0.75, "ai_governance": 0.70},
            usage_count=3,
        ),
    ]

    # Create test bullets for exp2
    bullets_exp2 = [
        Bullet(
            user_id=user.id,
            experience_id=exp2.id,
            text="Architected and deployed production ML pipeline processing 1M+ records daily using Python, TensorFlow, and AWS",
            tags=["machine_learning", "python", "tensorflow", "aws", "data_engineering"],
            seniority_level="mid",
            bullet_type="metric_impact",
            relevance_scores={"machine_learning": 0.95, "python": 0.90, "aws": 0.85},
            usage_count=0,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp2.id,
            text="Improved model accuracy by 25% through feature engineering and hyperparameter optimization",
            tags=["machine_learning", "model_optimization", "data_science"],
            seniority_level="mid",
            bullet_type="achievement",
            relevance_scores={"machine_learning": 0.88, "data_science": 0.85},
            usage_count=1,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp2.id,
            text="Collaborated with product team to define ML requirements and success metrics for recommendation system",
            tags=["cross_functional", "product_management", "machine_learning"],
            seniority_level="mid",
            bullet_type="responsibility",
            relevance_scores={"cross_functional": 0.80, "product_management": 0.75},
            usage_count=0,
        ),
    ]

    db.add_all(bullets_exp1 + bullets_exp2)
    db.commit()

    # Create test job profile
    job_profile = JobProfile(
        user_id=user.id,
        raw_jd_text="""
        Director of AI Governance

        We are seeking a strategic leader to build and scale our AI governance function.
        You will define policies, conduct risk assessments, and ensure responsible AI
        practices across our organization.

        Requirements:
        - 8+ years experience in AI/ML governance, risk management, or compliance
        - Deep understanding of AI technologies and ethical implications
        - Strong consulting and stakeholder management skills
        - Experience with policy development and regulatory frameworks
        - Excellent written and verbal communication skills

        Nice to have:
        - Technical background in machine learning or data science
        - Experience in highly regulated industries
        - Published thought leadership on AI ethics
        """,
        jd_url="https://example.com/job/123",
        job_title="Director of AI Governance",
        location="Remote",
        seniority="director",
        responsibilities="Build AI governance framework, conduct risk assessments, stakeholder management",
        requirements="AI governance, risk management, consulting, policy development",
        nice_to_haves="ML background, regulated industries, thought leadership",
        extracted_skills=[
            "AI Governance",
            "Risk Management",
            "Compliance",
            "Policy Development",
            "Stakeholder Management",
            "Machine Learning",
            "Consulting",
            "Communication",
        ],
        core_priorities=[
            "AI governance framework development",
            "Risk assessment and mitigation",
            "Stakeholder alignment and policy adoption",
        ],
        must_have_capabilities=[
            "AI Governance",
            "Risk Management",
            "Stakeholder Management",
        ],
        nice_to_have_capabilities=[
            "Machine Learning",
            "Thought Leadership",
        ],
    )

    db.add(job_profile)
    db.commit()
    db.refresh(job_profile)

    return user.id, job_profile.id


async def test_select_bullets():
    """Test bullet selection for a single role."""
    print("=" * 70)
    print("TEST: select_bullets_for_role()")
    print("=" * 70)

    db = next(get_db())
    user_id = None
    try:
        user_id, job_profile_id = setup_test_data(db)

        # Fetch data
        job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        experience = db.query(Experience).filter(Experience.user_id == user_id).first()
        bullets = db.query(Bullet).filter(Bullet.experience_id == experience.id).all()

        # Create mock skill gap result
        skill_gap_result = SkillGapResponse(
            job_profile_id=job_profile_id,
            user_id=user_id,
            skill_match_score=85.0,
            recommendation="strong_match",
            confidence=0.9,
            matched_skills=[
                SkillMatch(skill="AI Governance", match_strength=0.95, evidence=["bullet 1"]),
                SkillMatch(skill="Risk Management", match_strength=0.90, evidence=["bullet 3"]),
                SkillMatch(skill="Consulting", match_strength=0.88, evidence=["bullet 2"]),
            ],
            skill_gaps=[],
            weak_signals=[],
            key_positioning_angles=["Lead with AI governance expertise"],
            bullet_selection_guidance={
                "prioritize_tags": ["ai_governance", "risk_management", "consulting"],
                "emphasize_capabilities": ["AI Governance"],
                "target_seniority": ["senior"],
            },
            cover_letter_hooks=["Open with governance expertise"],
            user_advantages=["Strong governance background"],
            potential_concerns=[],
            mitigation_strategies={},
            analysis_timestamp=datetime.utcnow().isoformat(),
        )

        # Select bullets
        selected = select_bullets_for_role(
            experience=experience,
            bullets=bullets,
            job_profile=job_profile,
            skill_gap_result=skill_gap_result,
            max_bullets=4,
        )

        print(f"\nSelected {len(selected)} bullets from {len(bullets)} available:\n")
        for i, bullet in enumerate(selected, 1):
            print(f"{i}. [{bullet.relevance_score:.2f}] {bullet.text[:80]}...")
            print(f"   Tags: {', '.join(bullet.tags[:5])}")
            print(f"   Reason: {bullet.selection_reason}\n")

        print("✓ Test passed!")

    finally:
        # Cleanup
        if user_id is not None:
            db.query(Bullet).filter(Bullet.user_id == user_id).delete()
            db.query(Experience).filter(Experience.user_id == user_id).delete()
            db.query(JobProfile).filter(JobProfile.user_id == user_id).delete()
            db.query(User).filter(User.id == user_id).delete()
            db.commit()
        db.close()


async def test_select_skills():
    """Test skill selection and ordering."""
    print("\n" + "=" * 70)
    print("TEST: select_and_order_skills()")
    print("=" * 70)

    db = next(get_db())
    user_id = None
    try:
        user_id, job_profile_id = setup_test_data(db)

        # Fetch data
        job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        bullets = db.query(Bullet).filter(Bullet.user_id == user_id).all()

        # Create mock skill gap result
        skill_gap_result = SkillGapResponse(
            job_profile_id=job_profile_id,
            user_id=user_id,
            skill_match_score=85.0,
            recommendation="strong_match",
            confidence=0.9,
            matched_skills=[
                SkillMatch(skill="AI Governance", match_strength=0.95, evidence=[]),
                SkillMatch(skill="Risk Management", match_strength=0.90, evidence=[]),
                SkillMatch(skill="Consulting", match_strength=0.88, evidence=[]),
                SkillMatch(skill="Compliance", match_strength=0.82, evidence=[]),
                SkillMatch(skill="Machine Learning", match_strength=0.78, evidence=[]),
                SkillMatch(skill="Python", match_strength=0.75, evidence=[]),
            ],
            skill_gaps=[
                SkillGap(
                    skill="Policy Development",
                    importance="important",
                    positioning_strategy="Emphasize framework development experience",
                ),
            ],
            weak_signals=[
                WeakSignal(
                    skill="Communication",
                    current_evidence=["Stakeholder management"],
                    strengthening_strategy="Highlight presentation and writing",
                ),
            ],
            key_positioning_angles=[],
            bullet_selection_guidance={},
            cover_letter_hooks=[],
            user_advantages=[],
            potential_concerns=[],
            mitigation_strategies={},
            analysis_timestamp=datetime.utcnow().isoformat(),
        )

        # Select skills
        selected = select_and_order_skills(
            user_bullets=bullets,
            job_profile=job_profile,
            skill_gap_result=skill_gap_result,
            max_skills=12,
        )

        print(f"\nSelected {len(selected)} skills:\n")
        for i, skill in enumerate(selected, 1):
            print(f"{i}. {skill.skill} [{skill.match_type}] (priority: {skill.priority_score:.2f})")

        print("\n✓ Test passed!")

    finally:
        # Cleanup
        db.query(Bullet).filter(Bullet.user_id == user_id).delete()
        db.query(Experience).filter(Experience.user_id == user_id).delete()
        db.query(JobProfile).filter(JobProfile.user_id == user_id).delete()
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
        db.close()


async def test_generate_summary():
    """Test tailored summary generation."""
    print("\n" + "=" * 70)
    print("TEST: generate_tailored_summary()")
    print("=" * 70)

    db = next(get_db())
    user_id = None
    try:
        user_id, job_profile_id = setup_test_data(db)

        # Fetch data
        job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        experiences = db.query(Experience).filter(Experience.user_id == user_id).all()

        # Create mock data
        selected_skills = [
            {"skill": "AI Governance", "priority_score": 0.95},
            {"skill": "Risk Management", "priority_score": 0.90},
            {"skill": "Consulting", "priority_score": 0.88},
        ]

        skill_gap_result = SkillGapResponse(
            job_profile_id=job_profile_id,
            user_id=user_id,
            skill_match_score=85.0,
            recommendation="strong_match",
            confidence=0.9,
            matched_skills=[
                SkillMatch(skill="AI Governance", match_strength=0.95, evidence=[]),
                SkillMatch(skill="Risk Management", match_strength=0.90, evidence=[]),
            ],
            skill_gaps=[],
            weak_signals=[],
            key_positioning_angles=[],
            bullet_selection_guidance={},
            cover_letter_hooks=[],
            user_advantages=[],
            potential_concerns=[],
            mitigation_strategies={},
            analysis_timestamp=datetime.utcnow().isoformat(),
        )

        from schemas.resume_tailor import SelectedSkill
        selected_skills_typed = [
            SelectedSkill(
                skill="AI Governance",
                priority_score=0.95,
                match_type="direct_match",
                source="job_requirements",
            ),
            SelectedSkill(
                skill="Risk Management",
                priority_score=0.90,
                match_type="direct_match",
                source="job_requirements",
            ),
        ]

        # Generate summary
        llm = MockLLM()
        summary = await generate_tailored_summary(
            user_name=user.full_name,
            experiences=experiences,
            job_profile=job_profile,
            skill_gap_result=skill_gap_result,
            selected_skills=selected_skills_typed,
            llm=llm,
        )

        print(f"\nGenerated summary ({len(summary.split())} words):\n")
        print(f'"{summary}"')
        print("\n✓ Test passed!")

    finally:
        # Cleanup
        db.query(Bullet).filter(Bullet.user_id == user_id).delete()
        db.query(Experience).filter(Experience.user_id == user_id).delete()
        db.query(JobProfile).filter(JobProfile.user_id == user_id).delete()
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
        db.close()


async def test_tailor_resume_full():
    """Test full resume tailoring orchestration."""
    print("\n" + "=" * 70)
    print("TEST: tailor_resume() - Full Integration")
    print("=" * 70)

    db = next(get_db())
    user_id = None
    try:
        user_id, job_profile_id = setup_test_data(db)

        # Tailor resume
        result = await tailor_resume(
            job_profile_id=job_profile_id,
            user_id=user_id,
            db=db,
            max_bullets_per_role=4,
            max_skills=12,
            llm=MockLLM(),
        )

        print(f"\n✓ Tailored resume generated successfully!")
        print(f"\nMatch Score: {result.match_score}/100")
        print(f"Constraints Validated: {result.constraints_validated}")
        print(f"\nSummary:\n{result.tailored_summary}")
        print(f"\nSelected {len(result.selected_roles)} roles:")
        for role in result.selected_roles:
            print(f"  - {role.job_title} at {role.employer_name} ({len(role.selected_bullets)} bullets)")

        print(f"\nSelected {len(result.selected_skills)} skills:")
        for skill in result.selected_skills[:5]:
            print(f"  - {skill.skill} [{skill.match_type}]")

        print(f"\nRationale:")
        print(f"  Summary: {result.rationale.summary_approach[:100]}...")
        print(f"  Bullets: {result.rationale.bullet_selection_strategy[:100]}...")
        print(f"  Skills: {result.rationale.skills_ordering_logic[:100]}...")

        print("\n✓ Full integration test passed!")

    finally:
        # Cleanup
        db.query(Bullet).filter(Bullet.user_id == user_id).delete()
        db.query(Experience).filter(Experience.user_id == user_id).delete()
        db.query(JobProfile).filter(JobProfile.user_id == user_id).delete()
        db.query(User).filter(User.id == user_id).delete()
        db.commit()
        db.close()


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("RESUME TAILORING SERVICE TEST SUITE")
    print("=" * 70 + "\n")

    # Initialize database
    Base.metadata.create_all(bind=engine)

    # Run tests
    await test_select_bullets()
    await test_select_skills()
    await test_generate_summary()
    await test_tailor_resume_full()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
