"""
Test script for resume critic service.

Tests the PRD 4.3 resume rubric evaluation including:
- JD alignment scoring
- Clarity and conciseness scoring
- Impact orientation scoring
- Tone validation
- Hallucination detection
- Critic iteration loop
"""

import asyncio
import pytest
from datetime import date, datetime
from typing import Dict, List
from sqlalchemy.orm import Session

from db.database import get_db, engine
from db.models import Base, User, Experience, Bullet, JobProfile
from services.critic import (
    evaluate_resume,
    check_bullet_action_verbs,
    check_bullet_metrics,
    check_bullet_clarity,
    calculate_jd_alignment_score,
    calculate_impact_score,
    check_hallucination,
    extract_bullets_from_resume,
    RESUME_STRONG_VERBS,
    RESUME_WEAK_VERBS,
)
from services.resume_tailor import (
    tailor_resume,
    tailor_resume_with_critic,
    get_critic_feedback_for_revision,
)
from services.llm.mock_llm import MockLLM
from schemas.critic import ResumeCriticResult


def setup_test_data(db: Session) -> tuple[int, int]:
    """
    Create test data for critic testing.

    Returns:
        Tuple of (user_id, job_profile_id)
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]

    # Create test user
    user = User(
        username=f"critic_test_{unique_id}",
        email=f"critic_{unique_id}@example.com",
        full_name="Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create test experience
    exp = Experience(
        user_id=user.id,
        job_title="Senior AI Consultant",
        employer_name="Consulting Corp",
        location="New York, NY",
        start_date=date(2020, 1, 1),
        end_date=None,
        description="AI consulting work",
        order=0,
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    # Create test bullets with various qualities
    bullets = [
        Bullet(
            user_id=user.id,
            experience_id=exp.id,
            text="Led cross-functional team of 12 engineers to deliver enterprise AI governance framework, reducing compliance risk by 45% and saving $2.5M annually",
            tags=["ai_governance", "leadership", "compliance"],
            seniority_level="senior",
            bullet_type="achievement",
            relevance_scores={"ai_governance": 0.95},
            usage_count=0,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp.id,
            text="Architected scalable ML pipeline processing 10M+ daily predictions with 99.9% uptime, enabling real-time fraud detection",
            tags=["ml_engineering", "architecture"],
            seniority_level="senior",
            bullet_type="metric_impact",
            relevance_scores={"ml_engineering": 0.90},
            usage_count=0,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp.id,
            text="Helped with various data projects and assisted in stakeholder meetings",
            tags=["data", "communication"],
            seniority_level="mid",
            bullet_type="responsibility",
            relevance_scores={"data": 0.50},
            usage_count=2,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp.id,
            text="Worked on improving team processes",
            tags=["process"],
            seniority_level="mid",
            bullet_type="responsibility",
            relevance_scores={},
            usage_count=3,
        ),
    ]
    db.add_all(bullets)
    db.commit()

    # Create test job profile
    job_profile = JobProfile(
        user_id=user.id,
        raw_jd_text="""
        Senior AI Governance Director

        We are looking for an experienced leader to drive AI governance initiatives.

        Requirements:
        - 10+ years in AI/ML or governance
        - Experience with regulatory compliance
        - Strong leadership and stakeholder management
        - Technical background in machine learning

        Responsibilities:
        - Develop AI governance frameworks
        - Lead cross-functional teams
        - Ensure regulatory compliance
        - Drive strategic AI initiatives
        """,
        job_title="Senior AI Governance Director",
        seniority="director",
        extracted_skills=["AI Governance", "Machine Learning", "Compliance", "Leadership", "Stakeholder Management"],
        core_priorities=["AI governance framework development", "Regulatory compliance", "Cross-functional leadership"],
        must_have_capabilities=["AI governance experience", "Leadership", "Compliance"],
        tone_style="formal_corporate",
    )
    db.add(job_profile)
    db.commit()
    db.refresh(job_profile)

    return user.id, job_profile.id


def create_sample_resume_json(user_id: int, experience_id: int, bullet_ids: List[int]) -> Dict:
    """Create a sample TailoredResume JSON for testing."""
    return {
        "job_profile_id": 1,
        "user_id": user_id,
        "tailored_summary": "Experienced AI governance leader with 10+ years specializing in compliance frameworks and cross-functional team leadership. Proven expertise in ML systems.",
        "selected_roles": [
            {
                "experience_id": experience_id,
                "job_title": "Senior AI Consultant",
                "employer_name": "Consulting Corp",
                "location": "New York, NY",
                "start_date": "2020-01-01",
                "end_date": None,
                "selected_bullets": [
                    {
                        "bullet_id": bullet_ids[0] if len(bullet_ids) > 0 else None,
                        "text": "Led cross-functional team of 12 engineers to deliver enterprise AI governance framework, reducing compliance risk by 45% and saving $2.5M annually",
                        "relevance_score": 0.95,
                    },
                    {
                        "bullet_id": bullet_ids[1] if len(bullet_ids) > 1 else None,
                        "text": "Architected scalable ML pipeline processing 10M+ daily predictions with 99.9% uptime, enabling real-time fraud detection",
                        "relevance_score": 0.90,
                    },
                ],
            }
        ],
        "selected_skills": [
            {"skill_name": "AI Governance", "priority_score": 0.95},
            {"skill_name": "Machine Learning", "priority_score": 0.90},
            {"skill_name": "Compliance", "priority_score": 0.85},
            {"skill_name": "Leadership", "priority_score": 0.80},
            {"skill_name": "Python", "priority_score": 0.75},
        ],
        "constraints_validated": True,
    }


class TestBulletActionVerbs:
    """Test action verb detection in bullets."""

    def test_strong_verb_detection(self):
        """Bullets with strong verbs should not be flagged."""
        bullets = [
            {"text": "Led cross-functional team to deliver results", "bullet_id": 1},
            {"text": "Architected scalable solution for enterprise needs", "bullet_id": 2},
            {"text": "Delivered 50% improvement in processing speed", "bullet_id": 3},
        ]
        weak_count, total, issues = check_bullet_action_verbs(bullets)
        assert weak_count == 0
        assert total == 3
        assert len(issues) == 0

    def test_weak_verb_detection(self):
        """Bullets with weak verbs should be flagged."""
        bullets = [
            {"text": "Helped with various projects", "bullet_id": 1},
            {"text": "Assisted in stakeholder meetings", "bullet_id": 2},
            {"text": "Worked on improving processes", "bullet_id": 3},
        ]
        weak_count, total, issues = check_bullet_action_verbs(bullets)
        assert weak_count == 3
        assert total == 3
        assert len(issues) == 3
        assert all(i.severity == "warning" for i in issues)


class TestBulletMetrics:
    """Test metrics detection in bullets."""

    def test_metrics_detection(self):
        """Bullets with metrics should be detected."""
        bullets = [
            {"text": "Reduced costs by 45% through optimization", "bullet_id": 1},
            {"text": "Generated $2.5M in annual savings", "bullet_id": 2},
            {"text": "Led team of 12 engineers", "bullet_id": 3},
        ]
        metrics_count, issues = check_bullet_metrics(bullets)
        assert metrics_count == 3

    def test_no_metrics_flagged(self):
        """Bullets without metrics should generate info issues."""
        bullets = [
            {"text": "Improved team processes", "bullet_id": 1},
            {"text": "Enhanced collaboration with stakeholders", "bullet_id": 2},
        ]
        metrics_count, issues = check_bullet_metrics(bullets)
        assert metrics_count == 0
        assert len(issues) == 2
        assert all(i.severity == "info" for i in issues)


class TestBulletClarity:
    """Test bullet clarity and conciseness scoring."""

    def test_good_length_bullets(self):
        """Bullets with appropriate length should score well."""
        bullets = [
            {"text": "Led cross-functional team of 12 engineers to deliver enterprise AI governance framework, reducing compliance risk by 45%", "bullet_id": 1},
        ]
        clarity_score, issues = check_bullet_clarity(bullets)
        assert clarity_score >= 80  # Good clarity score
        assert len([i for i in issues if i.severity == "warning"]) == 0

    def test_too_short_bullet(self):
        """Very short bullets should be flagged."""
        bullets = [
            {"text": "Led team", "bullet_id": 1},
        ]
        clarity_score, issues = check_bullet_clarity(bullets)
        assert clarity_score < 100
        assert any("too short" in i.message.lower() for i in issues)

    def test_too_long_bullet(self):
        """Very long bullets should be flagged."""
        long_text = " ".join(["word"] * 50)  # 50 words
        bullets = [{"text": long_text, "bullet_id": 1}]
        clarity_score, issues = check_bullet_clarity(bullets)
        assert clarity_score < 100
        assert any("too long" in i.message.lower() for i in issues)


class TestImpactScore:
    """Test impact orientation scoring."""

    def test_high_impact_bullets(self):
        """Bullets with metrics and achievements should score high."""
        bullets = [
            {"text": "Delivered 45% reduction in compliance risk", "bullet_id": 1},
            {"text": "Generated $2.5M in cost savings", "bullet_id": 2},
            {"text": "Achieved 99.9% uptime for critical systems", "bullet_id": 3},
        ]
        impact_score = calculate_impact_score(bullets)
        assert impact_score >= 50

    def test_low_impact_bullets(self):
        """Bullets without metrics should score lower."""
        bullets = [
            {"text": "Worked on various projects", "bullet_id": 1},
            {"text": "Participated in meetings", "bullet_id": 2},
        ]
        impact_score = calculate_impact_score(bullets)
        assert impact_score < 50


class TestHallucinationDetection:
    """Test hallucination detection functionality."""

    def test_valid_resume_passes(self):
        """Resume with valid references should pass."""
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            # Get actual experience and bullet IDs
            exp = db.query(Experience).filter(Experience.user_id == user_id).first()
            bullets = db.query(Bullet).filter(Bullet.user_id == user_id).all()

            resume_json = {
                "selected_roles": [
                    {
                        "experience_id": exp.id,
                        "job_title": exp.job_title,  # Must match
                        "employer_name": exp.employer_name,  # Must match
                        "selected_bullets": [
                            {"bullet_id": bullets[0].id, "text": bullets[0].text}
                        ],
                    }
                ]
            }

            passed, concerns = check_hallucination(resume_json, db, user_id)
            assert passed is True
            assert len(concerns) == 0
        finally:
            db.rollback()

    def test_mismatched_job_title_fails(self):
        """Resume with modified job title should fail."""
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            exp = db.query(Experience).filter(Experience.user_id == user_id).first()

            resume_json = {
                "selected_roles": [
                    {
                        "experience_id": exp.id,
                        "job_title": "MODIFIED TITLE",  # Hallucinated
                        "employer_name": exp.employer_name,
                        "selected_bullets": [],
                    }
                ]
            }

            passed, concerns = check_hallucination(resume_json, db, user_id)
            assert passed is False
            assert any("Job title mismatch" in c for c in concerns)
        finally:
            db.rollback()


class TestEvaluateResume:
    """Integration tests for full resume evaluation."""

    @pytest.mark.asyncio
    async def test_good_resume_passes(self):
        """Well-crafted resume should pass critic evaluation."""
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
            exp = db.query(Experience).filter(Experience.user_id == user_id).first()
            bullets = db.query(Bullet).filter(Bullet.user_id == user_id).all()

            # Use only the strong bullets (first two)
            resume_json = create_sample_resume_json(
                user_id,
                exp.id,
                [bullets[0].id, bullets[1].id]
            )

            llm = MockLLM()
            result = await evaluate_resume(
                resume_json=resume_json,
                job_profile=job_profile,
                db=db,
                user_id=user_id,
                llm=llm,
            )

            assert isinstance(result, ResumeCriticResult)
            assert result.content_type == "resume"
            assert result.quality_score > 0
            # Good resume should have reasonable scores
            assert result.clarity_score >= 50
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_critic_scores_alignment(self):
        """Critic should score alignment with JD requirements."""
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
            exp = db.query(Experience).filter(Experience.user_id == user_id).first()
            bullets = db.query(Bullet).filter(Bullet.user_id == user_id).all()

            resume_json = create_sample_resume_json(
                user_id,
                exp.id,
                [bullets[0].id, bullets[1].id]
            )

            llm = MockLLM()
            result = await evaluate_resume(
                resume_json=resume_json,
                job_profile=job_profile,
                db=db,
                user_id=user_id,
                llm=llm,
            )

            # Should have alignment score
            assert hasattr(result, 'alignment_score')
            assert 0 <= result.alignment_score <= 100
        finally:
            db.rollback()


class TestCriticIterationLoop:
    """Test the critic iteration loop functionality."""

    @pytest.mark.asyncio
    async def test_iteration_loop_runs(self):
        """Critic loop should run and return results."""
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            llm = MockLLM()
            resume, critic_result = await tailor_resume_with_critic(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                llm=llm,
                max_iterations=2,
            )

            assert resume is not None
            assert critic_result is not None
            assert isinstance(critic_result, ResumeCriticResult)
            assert critic_result.iteration >= 1
        finally:
            db.rollback()


class TestCriticFeedback:
    """Test critic feedback extraction."""

    @pytest.mark.asyncio
    async def test_feedback_extraction(self):
        """Should extract actionable feedback from critic result."""
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
            exp = db.query(Experience).filter(Experience.user_id == user_id).first()
            bullets = db.query(Bullet).filter(Bullet.user_id == user_id).all()

            resume_json = create_sample_resume_json(
                user_id,
                exp.id,
                [bullets[0].id, bullets[1].id]
            )

            llm = MockLLM()
            result = await evaluate_resume(
                resume_json=resume_json,
                job_profile=job_profile,
                db=db,
                user_id=user_id,
                llm=llm,
            )

            feedback = get_critic_feedback_for_revision(result)

            assert 'priority_fixes' in feedback
            assert 'suggestions' in feedback
            assert 'weak_areas' in feedback
            assert 'strong_areas' in feedback
            assert 'metrics_coverage' in feedback
        finally:
            db.rollback()


def run_tests():
    """Run all tests synchronously."""
    print("=" * 60)
    print("Resume Critic Test Suite")
    print("=" * 60)

    # Test action verbs
    print("\nTesting action verb detection...")
    test_verbs = TestBulletActionVerbs()
    test_verbs.test_strong_verb_detection()
    test_verbs.test_weak_verb_detection()
    print("  ✓ Action verb tests passed")

    # Test metrics detection
    print("\nTesting metrics detection...")
    test_metrics = TestBulletMetrics()
    test_metrics.test_metrics_detection()
    test_metrics.test_no_metrics_flagged()
    print("  ✓ Metrics detection tests passed")

    # Test clarity scoring
    print("\nTesting clarity scoring...")
    test_clarity = TestBulletClarity()
    test_clarity.test_good_length_bullets()
    test_clarity.test_too_short_bullet()
    test_clarity.test_too_long_bullet()
    print("  ✓ Clarity scoring tests passed")

    # Test impact scoring
    print("\nTesting impact scoring...")
    test_impact = TestImpactScore()
    test_impact.test_high_impact_bullets()
    test_impact.test_low_impact_bullets()
    print("  ✓ Impact scoring tests passed")

    # Test hallucination detection
    print("\nTesting hallucination detection...")
    test_hallucination = TestHallucinationDetection()
    test_hallucination.test_valid_resume_passes()
    test_hallucination.test_mismatched_job_title_fails()
    print("  ✓ Hallucination detection tests passed")

    # Test full evaluation (async)
    print("\nTesting full resume evaluation...")
    async def run_async_tests():
        test_eval = TestEvaluateResume()
        await test_eval.test_good_resume_passes()
        await test_eval.test_critic_scores_alignment()

        test_loop = TestCriticIterationLoop()
        await test_loop.test_iteration_loop_runs()

        test_feedback = TestCriticFeedback()
        await test_feedback.test_feedback_extraction()

    asyncio.run(run_async_tests())
    print("  ✓ Full evaluation tests passed")

    print("\n" + "=" * 60)
    print("All resume critic tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
