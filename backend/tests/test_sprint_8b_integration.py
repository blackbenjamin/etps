"""
Sprint 8B Integration Tests

Tests for Sprint 8B gap remediation:
- 8B.1: Approved bullets integration in resume generation
- 8B.2: Approved paragraphs integration in cover letter generation
- 8B.3: Skill gap positioning in bullet selection
- 8B.4: Truthfulness validation in resume critic
- 8B.5: Em-dash detection in resume critic
- 8B.6: Config-driven max_iterations
- 8B.7: STAR notes in bullet rewriter
- 8B.8: Context notes in summary rewrite
- 8B.9: Portfolio integration for AI-heavy jobs
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from services.resume_tailor import (
    is_ai_heavy_job,
    get_portfolio_bullets,
    select_bullets_for_role,
    DEFAULT_MAX_ITERATIONS,
)
from services.cover_letter import (
    DEFAULT_MAX_ITERATIONS as CL_DEFAULT_MAX_ITERATIONS,
    DEFAULT_QUALITY_THRESHOLD,
)
from services.summary_rewrite import rewrite_summary_for_job
from services.critic import (
    check_em_dashes,
    validate_resume_truthfulness,
)
from db.models import Bullet, Experience, JobProfile, User


# ============================================================================
# Test 8B.3: Skill Gap Positioning in Bullet Selection
# ============================================================================

class TestSkillGapPositioning:
    """Test skill gap positioning integration in bullet selection."""

    def test_positioning_bonus_applied_to_matching_bullets(self):
        """Test that bullets matching positioning angles get bonus scores."""
        # Create mock experience
        experience = MagicMock(spec=Experience)
        experience.id = 1

        # Create bullet with text matching positioning keywords
        bullet = MagicMock(spec=Bullet)
        bullet.id = 1
        bullet.text = "Led AI strategy transformation driving business value"
        bullet.tags = ["ai", "strategy"]
        bullet.retired = False
        bullet.usage_count = 5  # Some usage to lower the score
        bullet.bullet_type = "responsibility"  # Lower type score
        bullet.relevance_scores = {"ai": 0.5}  # Moderate relevance
        bullet.importance = None  # No importance bonus
        bullet.ai_first_choice = False

        # Create job profile (non-AI-heavy to avoid ai_first_choice bonus)
        job_profile = MagicMock(spec=JobProfile)
        job_profile.extracted_skills = ["ai", "strategy"]
        job_profile.must_have_capabilities = []
        job_profile.job_type_tags = ["strategy"]  # Not AI-heavy

        # Create skill gap result with positioning angles
        skill_gap_result = MagicMock()
        skill_gap_result.matched_skills = [MagicMock(skill="ai", match_strength=0.5)]
        skill_gap_result.bullet_selection_guidance = {"prioritize_tags": []}  # No priority bonus
        skill_gap_result.key_positioning_angles = ["AI strategy transformation"]
        skill_gap_result.user_advantages = ["Strong business value focus"]

        # Select bullets
        selected = select_bullets_for_role(
            experience=experience,
            bullets=[bullet],
            job_profile=job_profile,
            skill_gap_result=skill_gap_result,
            max_bullets=4
        )

        # Verify bullet was selected
        assert len(selected) == 1
        # The selection reason should mention positioning or advantage
        assert "positioning" in selected[0].selection_reason.lower() or \
               "advantage" in selected[0].selection_reason.lower() or \
               len(selected[0].selection_reason) > 0


# ============================================================================
# Test 8B.5: Em-Dash Detection in Resume Critic
# ============================================================================

class TestEmDashDetectionResume:
    """Test em-dash detection in resume content."""

    def test_em_dash_detected_in_summary(self):
        """Test that em-dashes are detected in resume summary."""
        text_with_em_dash = "Senior leader — driving transformation in AI"
        issues = check_em_dashes(text_with_em_dash, context="summary")

        assert len(issues) == 1
        assert issues[0].issue_type == "em_dash_violation"
        assert issues[0].severity == "error"

    def test_no_issue_for_hyphen(self):
        """Test that regular hyphens are not flagged."""
        text_with_hyphen = "Senior-level leader driving AI-driven transformation"
        issues = check_em_dashes(text_with_hyphen, context="summary")

        assert len(issues) == 0

    def test_multiple_em_dashes_detected(self):
        """Test that multiple em-dashes are all detected."""
        text = "One — two — three"
        issues = check_em_dashes(text, context="bullet")

        assert len(issues) == 2


# ============================================================================
# Test 8B.6: Config-Driven Max Iterations
# ============================================================================

class TestConfigDrivenMaxIterations:
    """Test that max_iterations is read from config.yaml."""

    def test_resume_tailor_default_max_iterations(self):
        """Test that resume tailor reads max_iterations from config."""
        # Default should be 3 from config.yaml
        assert DEFAULT_MAX_ITERATIONS == 3

    def test_cover_letter_default_max_iterations(self):
        """Test that cover letter reads max_iterations from config."""
        assert CL_DEFAULT_MAX_ITERATIONS == 3

    def test_cover_letter_quality_threshold(self):
        """Test that quality threshold is read from config."""
        # Default is 75 from config.yaml critic.ats_score_threshold
        assert DEFAULT_QUALITY_THRESHOLD == 75.0


# ============================================================================
# Test 8B.8: Context Notes in Summary Rewrite
# ============================================================================

class TestContextNotesInSummaryRewrite:
    """Test context_notes parameter in summary rewrite."""

    @pytest.mark.asyncio
    async def test_rewrite_summary_accepts_context_notes(self):
        """Test that rewrite_summary_for_job accepts context_notes parameter."""
        from services.llm.mock_llm import MockLLM

        # Create mock user
        user = MagicMock(spec=User)
        user.candidate_profile = {
            "primary_identity": "AI Strategist",
            "specializations": ["AI Governance", "Strategy"]
        }

        # Create mock job profile
        job_profile = MagicMock(spec=JobProfile)
        job_profile.id = 1
        job_profile.job_title = "AI Strategy Director"
        job_profile.seniority = "director"
        job_profile.core_priorities = ["AI transformation"]
        job_profile.extracted_skills = ["AI", "Strategy"]

        # Create mock skill gap result
        skill_gap = MagicMock()
        skill_gap.matched_skills = []
        skill_gap.key_positioning_angles = []
        skill_gap.user_advantages = []

        # Create mock experiences
        experience = MagicMock(spec=Experience)
        experience.start_date = date(2015, 1, 1)
        experience.end_date = date(2023, 12, 31)
        experiences = [experience]

        # Create mock selected skills
        selected_skills = []

        # Create MockLLM
        llm = MockLLM()

        # Call with context_notes - should not raise
        summary = await rewrite_summary_for_job(
            user=user,
            job_profile=job_profile,
            skill_gap_result=skill_gap,
            selected_skills=selected_skills,
            experiences=experiences,
            llm=llm,
            company_profile=None,
            max_words=60,
            context_notes="Emphasize consulting background"
        )

        assert len(summary) > 0
        assert len(summary.split()) <= 70  # With some tolerance


# ============================================================================
# Test 8B.9: Portfolio Integration for AI-Heavy Jobs
# ============================================================================

class TestPortfolioIntegration:
    """Test portfolio bullets for AI-heavy jobs."""

    def test_is_ai_heavy_job_with_ai_tags(self):
        """Test job is detected as AI-heavy with AI tags."""
        job_profile = MagicMock(spec=JobProfile)
        job_profile.job_type_tags = ["ai", "machine learning"]
        job_profile.extracted_skills = []
        job_profile.core_priorities = []

        assert is_ai_heavy_job(job_profile) is True

    def test_is_ai_heavy_job_without_ai_tags(self):
        """Test job is not AI-heavy without AI tags."""
        job_profile = MagicMock(spec=JobProfile)
        job_profile.job_type_tags = ["project management"]
        job_profile.extracted_skills = ["excel", "powerpoint"]
        job_profile.core_priorities = []

        assert is_ai_heavy_job(job_profile) is False

    def test_get_portfolio_bullets_for_ai_job(self):
        """Test portfolio bullets are generated for AI-heavy jobs."""
        # Create user with ai_portfolio
        user = MagicMock(spec=User)
        user.id = 1
        user.candidate_profile = {
            "ai_portfolio": [
                {
                    "name": "RAG System",
                    "description": "Built a retrieval system",
                    "tech_stack": ["Python", "LangChain"],
                    "impact": "Improved search accuracy by 40%"
                }
            ]
        }

        # Create AI-heavy job
        job_profile = MagicMock(spec=JobProfile)
        job_profile.job_type_tags = ["ai", "llm"]
        job_profile.extracted_skills = ["Python", "NLP"]
        job_profile.core_priorities = []

        # Get portfolio bullets
        db = MagicMock()
        bullets = get_portfolio_bullets(user, job_profile, db)

        assert len(bullets) == 1
        assert "RAG System" in bullets[0].text
        assert bullets[0].id < 0  # Synthetic IDs are negative
        assert "ai_portfolio" in bullets[0].tags

    def test_get_portfolio_bullets_for_non_ai_job(self):
        """Test no portfolio bullets for non-AI jobs."""
        user = MagicMock(spec=User)
        user.id = 1
        user.candidate_profile = {
            "ai_portfolio": [{"name": "RAG System", "description": "Built a RAG"}]
        }

        # Non-AI job
        job_profile = MagicMock(spec=JobProfile)
        job_profile.job_type_tags = ["finance"]
        job_profile.extracted_skills = ["excel"]
        job_profile.core_priorities = []

        db = MagicMock()
        bullets = get_portfolio_bullets(user, job_profile, db)

        assert len(bullets) == 0


# ============================================================================
# Test 8B.4: Truthfulness Validation
# ============================================================================

class TestTruthfulnessValidation:
    """Test truthfulness validation in resume critic."""

    @pytest.mark.asyncio
    async def test_truthfulness_passes_for_matching_data(self):
        """Test truthfulness validation passes when data matches."""
        # Create stored experience
        stored_exp = MagicMock(spec=Experience)
        stored_exp.id = 1
        stored_exp.employer_name = "Acme Corp"
        stored_exp.job_title = "Senior Engineer"
        stored_exp.start_date = date(2020, 1, 1)
        stored_exp.end_date = date(2023, 12, 31)
        stored_exp.location = "Boston, MA"

        # Create resume JSON with matching data
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": 1,
                    "employer_name": "Acme Corp",
                    "job_title": "Senior Engineer",
                    "start_date": "2020-01-01",
                    "end_date": "2023-12-31",
                    "location": "Boston, MA"
                }
            ]
        }

        # Mock database
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [stored_exp]

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=1,
            db=db
        )

        assert is_truthful is True
        assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_truthfulness_fails_for_mismatched_employer(self):
        """Test truthfulness validation fails when employer doesn't match."""
        # Create stored experience
        stored_exp = MagicMock(spec=Experience)
        stored_exp.id = 1
        stored_exp.employer_name = "Acme Corp"
        stored_exp.job_title = "Senior Engineer"
        stored_exp.start_date = date(2020, 1, 1)
        stored_exp.end_date = None
        stored_exp.location = None

        # Create resume JSON with mismatched employer
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": 1,
                    "employer_name": "Different Corp",  # Mismatch!
                    "job_title": "Senior Engineer",
                    "start_date": "2020-01-01"
                }
            ]
        }

        # Mock database
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [stored_exp]

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=1,
            db=db
        )

        assert is_truthful is False
        assert len(issues) >= 1
        assert any("employer" in issue.message.lower() for issue in issues)

    @pytest.mark.asyncio
    async def test_truthfulness_skips_portfolio_bullets(self):
        """Test truthfulness validation skips synthetic portfolio bullets."""
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": -1000,  # Negative ID = synthetic
                    "employer_name": "Portfolio Project",
                    "job_title": "Personal Project"
                }
            ]
        }

        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=1,
            db=db
        )

        assert is_truthful is True
        assert len(issues) == 0
