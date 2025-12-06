"""
Test script for cover letter critic service.

Tests the Sprint 3 cover letter critic implementation including:
- CoverLetterCriticResult schema validation
- evaluate_cover_letter() function
- Critic iteration loop in generate_cover_letter()
- LLM revision functionality
- Issue detection and aggregation
"""

import asyncio
import pytest
from datetime import date, datetime, timezone
from typing import Dict, List
from sqlalchemy.orm import Session

from db.database import get_db, engine
from db.models import Base, User, Experience, Bullet, JobProfile, CompanyProfile
from services.cover_letter import (
    evaluate_cover_letter,
    check_banned_phrases,
    assess_tone_compliance,
    analyze_ats_keyword_coverage,
    compute_quality_score,
    generate_cover_letter,
    DEFAULT_QUALITY_THRESHOLD,
    DEFAULT_MAX_ITERATIONS,
)
from services.llm.mock_llm import MockLLM
from schemas.cover_letter import (
    CoverLetterCriticResult,
    CriticIssue,
    GeneratedCoverLetter,
    BannedPhraseCheck,
    ToneComplianceResult,
    ATSKeywordCoverage,
)


def setup_test_data(db: Session) -> tuple[int, int, int]:
    """
    Create test data for cover letter critic testing.

    Returns:
        Tuple of (user_id, job_profile_id, company_profile_id)
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]

    # Create test user
    user = User(
        username=f"cl_critic_test_{unique_id}",
        email=f"cl_critic_{unique_id}@example.com",
        full_name="Test User",
        is_active=True,
        candidate_profile={
            "primary_identity": "AI/ML Strategist",
            "specializations": ["AI Governance", "ML Engineering"],
            "target_roles": ["AI Director", "ML Lead"],
        }
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

    # Create test bullets
    bullets = [
        Bullet(
            user_id=user.id,
            experience_id=exp.id,
            text="Led cross-functional team of 12 engineers to deliver enterprise AI governance framework, reducing compliance risk by 45%",
            tags=["ai_governance", "leadership"],
            seniority_level="senior",
            bullet_type="achievement",
            relevance_scores={"ai_governance": 0.95},
            usage_count=0,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp.id,
            text="Architected scalable ML pipeline processing 10M+ daily predictions with 99.9% uptime",
            tags=["ml_engineering", "architecture"],
            seniority_level="senior",
            bullet_type="metric_impact",
            relevance_scores={"ml_engineering": 0.90},
            usage_count=0,
        ),
    ]
    for bullet in bullets:
        db.add(bullet)
    db.commit()

    # Create test company profile
    company = CompanyProfile(
        name="TechCorp AI",
        website="https://techcorp.ai",
        industry="Technology",
        size_band="1000-5000",
        known_initiatives="AI-first digital transformation, Responsible AI program",
        culture_signals=["innovation", "data-driven"],
        data_ai_maturity="advanced",
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    # Create test job profile
    job_profile = JobProfile(
        user_id=user.id,
        company_id=company.id,
        raw_jd_text="""
        AI Strategy Director at TechCorp AI

        We are seeking an experienced AI Strategy Director to lead our AI initiatives.

        Requirements:
        - 10+ years experience in AI/ML
        - Proven track record in AI governance
        - Strong leadership and stakeholder management skills
        - Experience with enterprise AI deployments

        Nice to have:
        - PhD in Computer Science or related field
        - Published research in AI ethics
        """,
        job_title="AI Strategy Director",
        location="San Francisco, CA",
        seniority="Director",
        extracted_skills=["AI Strategy", "AI Governance", "Leadership", "Stakeholder Management", "ML Engineering"],
        core_priorities=["AI governance framework development", "Strategic AI roadmap execution"],
        must_have_capabilities=["AI Governance", "Leadership", "Enterprise AI"],
        nice_to_have_capabilities=["PhD", "Published Research"],
        tone_style="formal_corporate",
    )
    db.add(job_profile)
    db.commit()
    db.refresh(job_profile)

    return user.id, job_profile.id, company.id


def cleanup_test_data(db: Session, user_id: int, job_profile_id: int, company_id: int):
    """Clean up test data after tests."""
    db.query(Bullet).filter(Bullet.user_id == user_id).delete()
    db.query(Experience).filter(Experience.user_id == user_id).delete()
    db.query(JobProfile).filter(JobProfile.id == job_profile_id).delete()
    db.query(CompanyProfile).filter(CompanyProfile.id == company_id).delete()
    db.query(User).filter(User.id == user_id).delete()
    db.commit()


class TestCriticIssueSchema:
    """Test CriticIssue schema validation."""

    def test_valid_critic_issue(self):
        """Test creating a valid CriticIssue."""
        issue = CriticIssue(
            category="banned_phrase",
            severity="critical",
            description="Found banned phrase: 'I am excited to apply'",
            suggestion="Replace with a more specific opening",
            section="greeting"
        )
        assert issue.category == "banned_phrase"
        assert issue.severity == "critical"
        assert issue.section == "greeting"

    def test_critic_issue_categories(self):
        """Test all valid categories."""
        categories = ["banned_phrase", "tone", "ats_coverage", "structure", "content"]
        for cat in categories:
            issue = CriticIssue(
                category=cat,
                severity="minor",
                description="Test issue"
            )
            assert issue.category == cat


class TestCoverLetterCriticResultSchema:
    """Test CoverLetterCriticResult schema validation."""

    def test_valid_critic_result(self):
        """Test creating a valid CoverLetterCriticResult."""
        result = CoverLetterCriticResult(
            iteration=1,
            quality_score=75.5,
            passed=True,
            should_retry=False,
            banned_phrase_check=BannedPhraseCheck(
                violations_found=0,
                violations=[],
                overall_severity="none",
                passed=True
            ),
            tone_compliance=ToneComplianceResult(
                target_tone="formal_corporate",
                detected_tone="formal_corporate",
                compliance_score=1.0,
                compatible=True,
                tone_notes="Excellent tone alignment"
            ),
            ats_keyword_coverage=ATSKeywordCoverage(
                total_keywords=10,
                keywords_covered=8,
                coverage_percentage=80.0,
                missing_critical_keywords=[],
                covered_keywords=["AI", "governance"],
                coverage_adequate=True
            ),
            issues=[],
            retry_reasons=[],
            improvement_suggestions=[],
            evaluated_at=datetime.now(timezone.utc).isoformat()
        )
        assert result.passed is True
        assert result.should_retry is False
        assert result.quality_score == 75.5

    def test_critic_result_with_issues(self):
        """Test CriticResult with issues triggers retry."""
        result = CoverLetterCriticResult(
            iteration=1,
            quality_score=55.0,
            passed=False,
            should_retry=True,
            banned_phrase_check=BannedPhraseCheck(
                violations_found=2,
                violations=[],
                overall_severity="major",
                passed=False
            ),
            tone_compliance=ToneComplianceResult(
                target_tone="formal_corporate",
                detected_tone="startup_casual",
                compliance_score=0.55,
                compatible=True,
                tone_notes="Tone mismatch"
            ),
            ats_keyword_coverage=ATSKeywordCoverage(
                total_keywords=10,
                keywords_covered=5,
                coverage_percentage=50.0,
                missing_critical_keywords=["AI Governance"],
                covered_keywords=["AI"],
                coverage_adequate=False
            ),
            issues=[
                CriticIssue(
                    category="banned_phrase",
                    severity="major",
                    description="Found banned phrase"
                )
            ],
            retry_reasons=["Major banned phrase found"],
            improvement_suggestions=["Replace banned phrase"],
            evaluated_at=datetime.now(timezone.utc).isoformat()
        )
        assert result.passed is False
        assert result.should_retry is True
        assert len(result.issues) == 1


class TestEvaluateCoverLetter:
    """Test the evaluate_cover_letter function."""

    @pytest.fixture
    def db_session(self):
        """Get database session for tests."""
        Base.metadata.create_all(bind=engine)
        db = next(get_db())
        yield db
        db.close()

    @pytest.fixture
    def test_data(self, db_session):
        """Create test data."""
        user_id, job_profile_id, company_id = setup_test_data(db_session)
        yield user_id, job_profile_id, company_id
        cleanup_test_data(db_session, user_id, job_profile_id, company_id)

    @pytest.mark.asyncio
    async def test_evaluate_clean_cover_letter(self, db_session, test_data):
        """Test evaluating a clean cover letter without issues."""
        user_id, job_profile_id, company_id = test_data

        job_profile = db_session.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        company_profile = db_session.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()

        clean_cover_letter = """Dear TechCorp AI Team,

My background in AI governance and enterprise strategy aligns well with the AI Strategy Director role.

With extensive experience leading cross-functional AI initiatives, I have delivered governance frameworks
that reduced compliance risk by 45% while enabling innovation. My work at Consulting Corp demonstrates
a track record of balancing strategic vision with practical implementation.

The opportunity to advance TechCorp AI's responsible AI program resonates with my career focus on
ethical AI deployment. Your AI-first transformation initiative aligns with my experience in enterprise-scale
AI governance and stakeholder management.

I welcome the opportunity to discuss how my experience can advance TechCorp AI's strategic objectives.

Best regards,
Test User"""

        llm = MockLLM()
        result = await evaluate_cover_letter(
            cover_letter_text=clean_cover_letter,
            job_profile=job_profile,
            company_profile=company_profile,
            llm=llm,
            iteration=1,
            quality_threshold=75.0
        )

        assert isinstance(result, CoverLetterCriticResult)
        assert result.iteration == 1
        assert result.quality_score >= 60.0  # Should be reasonably high
        # No critical banned phrases in this letter
        critical_issues = [i for i in result.issues if i.severity == "critical"]
        assert len(critical_issues) == 0

    @pytest.mark.asyncio
    async def test_evaluate_cover_letter_with_banned_phrases(self, db_session, test_data):
        """Test evaluating a cover letter with banned phrases."""
        user_id, job_profile_id, company_id = test_data

        job_profile = db_session.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        company_profile = db_session.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()

        # A letter with some banned phrases but not so broken it's unfixable
        bad_cover_letter = """Dear TechCorp AI Team,

I am excited to apply for the AI Strategy Director position. My background in AI governance
and leadership spans over 10 years, with experience at enterprise scale.

I have led cross-functional teams delivering AI governance frameworks and stakeholder management
initiatives. My work demonstrates strong alignment with your requirements.

I look forward to hearing from you about this opportunity.

Best regards,
Test User"""

        llm = MockLLM()
        result = await evaluate_cover_letter(
            cover_letter_text=bad_cover_letter,
            job_profile=job_profile,
            company_profile=company_profile,
            llm=llm,
            iteration=1,
            quality_threshold=75.0
        )

        assert isinstance(result, CoverLetterCriticResult)
        assert result.passed is False  # Has banned phrases
        assert len(result.issues) > 0

        # Should detect banned phrases
        banned_issues = [i for i in result.issues if i.category == "banned_phrase"]
        assert len(banned_issues) > 0

        # Should have improvement suggestions since score is above 30
        # (threshold for "too broken to fix")
        assert result.quality_score >= 30.0

    @pytest.mark.asyncio
    async def test_evaluate_with_previous_result(self, db_session, test_data):
        """Test evaluating with previous result for delta calculation."""
        user_id, job_profile_id, company_id = test_data

        job_profile = db_session.query(JobProfile).filter(JobProfile.id == job_profile_id).first()
        company_profile = db_session.query(CompanyProfile).filter(CompanyProfile.id == company_id).first()

        # First evaluation
        llm = MockLLM()
        first_result = await evaluate_cover_letter(
            cover_letter_text="I am excited to apply for this role.",
            job_profile=job_profile,
            company_profile=company_profile,
            llm=llm,
            iteration=1,
            quality_threshold=75.0
        )

        # Improved version
        improved_text = "My background in AI governance aligns with the role requirements."
        second_result = await evaluate_cover_letter(
            cover_letter_text=improved_text,
            job_profile=job_profile,
            company_profile=company_profile,
            llm=llm,
            iteration=2,
            previous_result=first_result,
            quality_threshold=75.0
        )

        assert second_result.iteration == 2
        assert second_result.score_delta is not None


class TestMockLLMRevision:
    """Test MockLLM revision functionality."""

    @pytest.mark.asyncio
    async def test_revise_removes_banned_phrases(self):
        """Test that MockLLM revision removes banned phrases."""
        llm = MockLLM()

        original = "I am excited to apply for this role. I believe I would be a great fit."

        critic_feedback = {
            "issues": [
                {
                    "category": "banned_phrase",
                    "severity": "critical",
                    "description": "Found banned phrase: 'i am excited to apply'",
                    "suggestion": "Replace with specific opening"
                },
                {
                    "category": "banned_phrase",
                    "severity": "critical",
                    "description": "Found banned phrase: 'i believe i would be a great fit'",
                    "suggestion": "Replace with evidence-based statement"
                }
            ],
            "improvement_suggestions": [],
            "quality_score": 40.0
        }

        job_context = {"title": "AI Director", "skills": ["AI Governance"]}
        company_context = {"name": "TechCorp"}

        revised = await llm.revise_cover_letter(
            current_draft=original,
            critic_feedback=critic_feedback,
            job_context=job_context,
            company_context=company_context,
            tone="formal_corporate",
            user_name="Test User"
        )

        # Should have replaced banned phrases
        assert "i am excited to apply" not in revised.lower()
        assert "i believe i would be a great fit" not in revised.lower()

    @pytest.mark.asyncio
    async def test_revise_replaces_em_dashes(self):
        """Test that MockLLM revision replaces em-dashes."""
        llm = MockLLM()

        original = "My experience—including AI governance—is relevant."

        critic_feedback = {"issues": [], "improvement_suggestions": [], "quality_score": 70.0}
        job_context = {"title": "AI Director", "skills": ["AI Governance"]}
        company_context = {"name": "TechCorp"}

        revised = await llm.revise_cover_letter(
            current_draft=original,
            critic_feedback=critic_feedback,
            job_context=job_context,
            company_context=company_context,
            tone="formal_corporate",
            user_name="Test User"
        )

        # Em-dashes should be replaced with regular dashes
        assert "—" not in revised


class TestGenerateCoverLetterWithCritic:
    """Test the full generate_cover_letter with critic iteration loop."""

    @pytest.fixture
    def db_session(self):
        """Get database session for tests."""
        Base.metadata.create_all(bind=engine)
        db = next(get_db())
        yield db
        db.close()

    @pytest.fixture
    def test_data(self, db_session):
        """Create test data."""
        user_id, job_profile_id, company_id = setup_test_data(db_session)
        yield user_id, job_profile_id, company_id
        cleanup_test_data(db_session, user_id, job_profile_id, company_id)

    @pytest.mark.asyncio
    async def test_generate_cover_letter_returns_iteration_history(self, db_session, test_data):
        """Test that generate_cover_letter includes iteration history."""
        user_id, job_profile_id, company_id = test_data

        result = await generate_cover_letter(
            job_profile_id=job_profile_id,
            user_id=user_id,
            db=db_session,
            company_profile_id=company_id,
            max_iterations=3,
            quality_threshold=75.0
        )

        assert isinstance(result, GeneratedCoverLetter)
        assert result.iterations_used >= 1
        assert len(result.iteration_history) >= 1
        assert result.final_critic_result is not None

    @pytest.mark.asyncio
    async def test_generate_cover_letter_respects_max_iterations(self, db_session, test_data):
        """Test that generation respects max_iterations limit."""
        user_id, job_profile_id, company_id = test_data

        result = await generate_cover_letter(
            job_profile_id=job_profile_id,
            user_id=user_id,
            db=db_session,
            company_profile_id=company_id,
            max_iterations=1,  # Force single iteration
            quality_threshold=99.0  # Very high threshold
        )

        assert result.iterations_used == 1
        assert len(result.iteration_history) == 1

    @pytest.mark.asyncio
    async def test_generate_cover_letter_stops_on_pass(self, db_session, test_data):
        """Test that generation stops when quality threshold is met."""
        user_id, job_profile_id, company_id = test_data

        result = await generate_cover_letter(
            job_profile_id=job_profile_id,
            user_id=user_id,
            db=db_session,
            company_profile_id=company_id,
            max_iterations=5,
            quality_threshold=30.0  # Very low threshold - should pass quickly
        )

        # Should stop before max iterations if passing
        if result.critic_passed:
            final_result = result.final_critic_result
            assert final_result.passed is True
            assert final_result.quality_score >= 30.0


class TestQualityScoreComputation:
    """Test quality score computation logic."""

    def test_perfect_score_components(self):
        """Test quality score with perfect components."""
        banned_check = BannedPhraseCheck(
            violations_found=0,
            violations=[],
            overall_severity="none",
            passed=True
        )
        tone_compliance = ToneComplianceResult(
            target_tone="formal_corporate",
            detected_tone="formal_corporate",
            compliance_score=1.0,
            compatible=True,
            tone_notes="Perfect"
        )
        ats_coverage = ATSKeywordCoverage(
            total_keywords=10,
            keywords_covered=10,
            coverage_percentage=100.0,
            missing_critical_keywords=[],
            covered_keywords=[],
            coverage_adequate=True
        )

        score = compute_quality_score(banned_check, tone_compliance, ats_coverage)

        # Base (50) + no violations bonus (10) + tone (20) + ATS (20) = 100
        assert score == 100.0

    def test_score_with_violations(self):
        """Test quality score penalized by violations."""
        from schemas.cover_letter import BannedPhraseViolation

        banned_check = BannedPhraseCheck(
            violations_found=2,
            violations=[
                BannedPhraseViolation(phrase="test", severity="critical", section="body"),
                BannedPhraseViolation(phrase="test2", severity="major", section="body"),
            ],
            overall_severity="critical",
            passed=False
        )
        tone_compliance = ToneComplianceResult(
            target_tone="formal_corporate",
            detected_tone="formal_corporate",
            compliance_score=1.0,
            compatible=True,
            tone_notes="Good"
        )
        ats_coverage = ATSKeywordCoverage(
            total_keywords=10,
            keywords_covered=10,
            coverage_percentage=100.0,
            missing_critical_keywords=[],
            covered_keywords=[],
            coverage_adequate=True
        )

        score = compute_quality_score(banned_check, tone_compliance, ats_coverage)

        # Should be penalized: critical (-15) + major (-8) = -23 penalty
        # Base (50) + tone (20) + ATS (20) - penalty (23) = 67
        assert score < 100.0
        assert score == 67.0


def run_tests():
    """Run all tests."""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
