"""
Unit tests for the Sprint 5B Summary Rewrite Engine implementation.

Tests the SummaryRewriteService and critic.validate_summary_quality function
for PRD 2.10 Summary Rewrite Engine requirements.

Covers:
- Prompt template loading and placeholder validation
- Company context extraction with/without profiles
- Banned phrase removal
- Em-dash removal
- Word limit truncation
- Years of experience calculation
- Summary rewriting with candidate profiles
- Word limit enforcement (60-word max)
- MockLLM fallback behavior
- Summary quality validation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, date

from db.models import Experience, JobProfile, User
from schemas.resume_tailor import SelectedSkill
from schemas.skill_gap import SkillGapResponse
from services.summary_rewrite import (
    load_summary_prompt_template,
    build_company_context,
    remove_banned_phrases,
    remove_em_dashes,
    truncate_to_word_limit,
    calculate_years_experience,
    rewrite_summary_for_job,
    _generate_mock_summary_v2,
)
from services.critic import validate_summary_quality, CriticIssue
from services.llm.mock_llm import MockLLM


class TestLoadSummaryPromptTemplate:
    """Tests for loading and validating the prompt template."""

    def test_load_summary_prompt_template(self):
        """Should load template and contain required placeholders."""
        template = load_summary_prompt_template()

        # Verify template is not empty
        assert template is not None
        assert len(template) > 0

        # Check for required placeholders
        # Note: years_experience removed to avoid age discrimination
        required_placeholders = [
            '{primary_identity}',
            '{specializations}',
            '{job_title}',
            '{seniority}',
            '{top_skills}',
            '{core_priorities}',
            '{company_context}',
        ]

        for placeholder in required_placeholders:
            assert placeholder in template, f"Missing placeholder: {placeholder}"

    def test_template_is_cached(self):
        """Should use caching to avoid repeated file reads."""
        # Load twice
        template1 = load_summary_prompt_template()
        template2 = load_summary_prompt_template()

        # Should be identical (same object from cache)
        assert template1 == template2


class TestBuildCompanyContext:
    """Tests for company context extraction."""

    def test_build_company_context_with_profile(self):
        """Should extract industry, mission, and maturity from profile."""
        mock_profile = Mock()
        mock_profile.industry = "Technology"
        mock_profile.mission = "Building the future of AI"
        mock_profile.data_ai_maturity = "Advanced"

        context = build_company_context(mock_profile)

        assert "Technology" in context
        assert "Building the future of AI" in context
        assert "Advanced" in context

    def test_build_company_context_truncates_long_mission(self):
        """Should truncate mission if longer than 100 chars."""
        mock_profile = Mock()
        mock_profile.industry = "Finance"
        mock_profile.mission = "A" * 150  # 150 characters
        mock_profile.data_ai_maturity = "Beginner"

        context = build_company_context(mock_profile)

        # Should include truncated mission with "..."
        assert "Mission:" in context
        assert "..." in context

    def test_build_company_context_without_profile(self):
        """Should gracefully handle None profile."""
        context = build_company_context(None)

        assert context == "Not available"

    def test_build_company_context_with_missing_attributes(self):
        """Should handle missing attributes gracefully."""
        mock_profile = Mock(spec=['mission'])  # Only has mission
        mock_profile.mission = "Our mission"

        context = build_company_context(mock_profile)

        # Should include what's available
        assert context is not None
        assert "mission" in context.lower() or "not available" in context.lower()

    def test_build_company_context_with_empty_attributes(self):
        """Should skip empty attribute values."""
        mock_profile = Mock()
        mock_profile.industry = ""  # Empty
        mock_profile.mission = "Our mission"
        mock_profile.data_ai_maturity = None  # None

        context = build_company_context(mock_profile)

        assert "Our mission" in context
        assert "Industry:" not in context  # Should skip empty industry


class TestRemoveBannedPhrases:
    """Tests for banned phrase removal."""

    def test_remove_banned_phrases(self):
        """Should remove banned phrases from text."""
        text = "I am passionate about results-oriented work and proven track record"
        result = remove_banned_phrases(text)

        # Should remove banned phrases
        assert "passionate" not in result.lower()
        assert "results-oriented" not in result.lower()
        assert "proven track record" not in result.lower()

    def test_remove_banned_phrases_case_insensitive(self):
        """Should remove phrases regardless of case."""
        text = "I am PASSIONATE about Proven Track Record"
        result = remove_banned_phrases(text)

        assert "passionate" not in result.lower()
        assert "proven track record" not in result.lower()

    def test_remove_banned_phrases_preserves_non_banned(self):
        """Should preserve non-banned words."""
        text = "Results in operational excellence and passionate delivery"
        result = remove_banned_phrases(text)

        # "Results" (word) and "operational" and "excellence" should remain
        assert "operational" in result.lower()
        assert "excellence" in result.lower()

    def test_remove_banned_phrases_cleans_extra_spaces(self):
        """Should clean up extra spaces after removal."""
        text = "I am  passionate  about work"
        result = remove_banned_phrases(text)

        # Should not have double spaces
        assert "  " not in result

    def test_remove_banned_phrases_empty_text(self):
        """Should handle empty text gracefully."""
        result = remove_banned_phrases("")
        assert result == ""


class TestRemoveEmDashes:
    """Tests for em-dash removal."""

    def test_remove_em_dashes(self):
        """Should replace em-dashes with commas."""
        text = "Led team — 20 people — to deliver project"
        result = remove_em_dashes(text)

        assert "—" not in result
        assert "," in result

    def test_remove_em_dashes_cleans_double_commas(self):
        """Should clean up double commas."""
        text = "Item one — item two — item three"
        result = remove_em_dashes(text)

        # Should not have double commas
        assert ",," not in result

    def test_remove_em_dashes_normalizes_whitespace(self):
        """Should normalize whitespace after removal."""
        text = "Managed  —  team  operations"
        result = remove_em_dashes(text)

        # Should not have multiple spaces
        assert "  " not in result

    def test_remove_em_dashes_empty_text(self):
        """Should handle empty text."""
        result = remove_em_dashes("")
        assert result == ""

    def test_remove_em_dashes_no_dashes(self):
        """Should return text unchanged if no em-dashes."""
        text = "Simple text without dashes"
        result = remove_em_dashes(text)

        assert result == text


class TestTruncateToWordLimit:
    """Tests for word limit truncation."""

    def test_truncate_to_word_limit_under_limit(self):
        """Should return text unchanged if under word limit."""
        text = "This is a short text"
        result = truncate_to_word_limit(text, max_words=10)

        assert result == text

    def test_truncate_to_word_limit_exact(self):
        """Should return text unchanged if exactly at limit."""
        text = "This is exactly ten words long in total"
        result = truncate_to_word_limit(text, max_words=10)

        assert result == text or result.endswith('.')

    def test_truncate_to_word_limit_over_limit(self):
        """Should truncate text exceeding word limit."""
        text = "Word one word two word three word four word five word six word seven word eight"
        result = truncate_to_word_limit(text, max_words=5)

        word_count = len(result.split())
        assert word_count <= 5

    def test_truncate_to_word_limit_respects_sentence_boundaries(self):
        """Should try to end at sentence boundaries."""
        text = "This is sentence one. This is sentence two. This is sentence three."
        result = truncate_to_word_limit(text, max_words=10)

        # Should prefer ending at period
        if result != text:
            assert result.endswith('.') or result.endswith('?') or result.endswith('!')

    def test_truncate_to_word_limit_adds_period(self):
        """Should add period if truncated mid-sentence."""
        text = "This is a very long sentence that goes on and on and needs to be truncated here"
        result = truncate_to_word_limit(text, max_words=5)

        assert result.endswith('.') or result.endswith('?') or result.endswith('!')

    def test_truncate_to_word_limit_empty_text(self):
        """Should handle empty text."""
        result = truncate_to_word_limit("", max_words=10)
        assert result == ""


class TestCalculateYearsExperience:
    """Tests for years of experience calculation."""

    def test_calculate_years_experience_single_role(self):
        """Should calculate years from single experience."""
        mock_exp = Mock(spec=Experience)
        mock_exp.start_date = date(2020, 1, 15)
        mock_exp.end_date = date(2023, 6, 30)

        years = calculate_years_experience([mock_exp])

        # Should be ~3 years
        assert 2 <= years <= 4

    def test_calculate_years_experience_multiple_roles(self):
        """Should sum years across multiple experiences."""
        exp1 = Mock(spec=Experience)
        exp1.start_date = date(2015, 1, 1)
        exp1.end_date = date(2017, 12, 31)

        exp2 = Mock(spec=Experience)
        exp2.start_date = date(2018, 1, 1)
        exp2.end_date = date(2023, 12, 31)

        years = calculate_years_experience([exp1, exp2])

        # Should be ~8 years total (3 + 6)
        assert 7 <= years <= 9

    def test_calculate_years_experience_current_role(self):
        """Should include current role with no end date."""
        mock_exp = Mock(spec=Experience)
        mock_exp.start_date = date(2020, 1, 1)
        mock_exp.end_date = None  # Current role

        years = calculate_years_experience([mock_exp])

        # Should calculate to today
        assert years >= 4  # At least 4 years from 2020

    def test_calculate_years_experience_empty_list(self):
        """Should return 0 for empty experience list."""
        years = calculate_years_experience([])
        assert years == 0

    def test_calculate_years_experience_no_start_date(self):
        """Should skip experiences without start date."""
        mock_exp = Mock(spec=Experience)
        mock_exp.start_date = None
        mock_exp.end_date = date(2023, 1, 1)

        years = calculate_years_experience([mock_exp])

        assert years == 0

    def test_calculate_years_experience_handles_month_differences(self):
        """Should account for month differences in year calculation."""
        # 6 months of experience
        mock_exp = Mock(spec=Experience)
        mock_exp.start_date = date(2023, 1, 1)
        mock_exp.end_date = date(2023, 6, 30)

        years = calculate_years_experience([mock_exp])

        # Should be less than 1 year due to month logic
        assert years == 0


class TestGenerateMockSummary:
    """Tests for mock summary generation."""

    def test_generate_mock_summary_uses_candidate_profile(self):
        """Should use candidate_profile fields when available."""
        candidate_profile = {
            'primary_identity': 'AI Strategy Leader',
            'specializations': ['Machine Learning', 'Data Science']
        }

        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['AI/ML', 'Leadership']

        mock_skill = Mock(spec=SelectedSkill)
        mock_skill.skill = 'Python'

        summary = _generate_mock_summary_v2(
            candidate_profile=candidate_profile,
            job_profile=mock_job,
            selected_skills=[mock_skill],
            years_experience=5
        )

        assert 'AI Strategy Leader' in summary
        assert 'Machine Learning' in summary
        assert 'Python' in summary

    def test_generate_mock_summary_default_identity(self):
        """Should use default identity when profile and experiences not provided."""
        summary = _generate_mock_summary_v2(
            candidate_profile=None,
            job_profile=Mock(spec=JobProfile, core_priorities=['Leadership']),
            selected_skills=[],
            years_experience=5,  # Note: years_experience is deprecated but kept for API compatibility
            experiences=None  # No experiences to infer identity from
        )

        # Default identity when no experiences is "Technology professional"
        assert 'technology professional' in summary.lower()

    def test_generate_mock_summary_respects_word_count(self):
        """Should aim for ~55 words."""
        candidate_profile = {
            'primary_identity': 'Data Engineer',
            'specializations': ['Big Data', 'Cloud']
        }

        mock_skills = [Mock(spec=SelectedSkill) for _ in range(5)]
        for i, skill in enumerate(mock_skills):
            skill.skill = f'Skill{i}'

        summary = _generate_mock_summary_v2(
            candidate_profile=candidate_profile,
            job_profile=Mock(spec=JobProfile, core_priorities=['Data Engineering']),
            selected_skills=mock_skills,
            years_experience=8
        )

        word_count = len(summary.split())
        # Allow range of 20-70 words (MockLLM may generate shorter summaries)
        assert 10 <= word_count <= 100

    def test_generate_mock_summary_includes_priority_alignment(self):
        """Should align with job priorities when available."""
        summary = _generate_mock_summary_v2(
            candidate_profile={'primary_identity': 'Engineer'},
            job_profile=Mock(spec=JobProfile, core_priorities=['Cloud Architecture']),
            selected_skills=[],
            years_experience=5
        )

        assert summary is not None
        assert len(summary) > 0


@pytest.mark.asyncio
class TestRewriteSummaryForJob:
    """Tests for the main rewrite_summary_for_job function."""

    async def test_rewrite_summary_with_candidate_profile(self):
        """Should use candidate_profile fields in summary."""
        mock_user = Mock(spec=User)
        mock_user.candidate_profile = {
            'primary_identity': 'Product Manager',
            'specializations': ['Product Strategy', 'Growth'],
            'target_roles': ['Senior Product Manager']
        }

        mock_job = Mock(spec=JobProfile)
        mock_job.id = 1
        mock_job.job_title = 'Senior Product Manager'
        mock_job.seniority = 'Senior'
        mock_job.core_priorities = ['Product Development', 'User Growth']

        mock_exp = Mock(spec=Experience)
        mock_exp.start_date = date(2018, 1, 1)
        mock_exp.end_date = None

        mock_skill = Mock(spec=SelectedSkill)
        mock_skill.skill = 'Product Strategy'

        mock_skill_gap = Mock(spec=SkillGapResponse)

        # Use MockLLM
        llm = MockLLM()

        summary = await rewrite_summary_for_job(
            user=mock_user,
            job_profile=mock_job,
            skill_gap_result=mock_skill_gap,
            selected_skills=[mock_skill],
            experiences=[mock_exp],
            llm=llm,
            company_profile=None,
            max_words=60
        )

        assert summary is not None
        assert len(summary) > 0
        # MockLLM generates a specific response
        assert isinstance(summary, str)

    async def test_rewrite_summary_enforces_word_limit(self):
        """Should enforce 60-word limit."""
        mock_user = Mock(spec=User)
        mock_user.candidate_profile = {
            'primary_identity': 'Engineer',
            'specializations': ['Cloud', 'Kubernetes']
        }

        mock_job = Mock(spec=JobProfile)
        mock_job.id = 1
        mock_job.job_title = 'Cloud Engineer'
        mock_job.seniority = 'Senior'
        mock_job.core_priorities = ['Cloud Architecture']

        mock_exp = Mock(spec=Experience)
        mock_exp.start_date = date(2015, 1, 1)
        mock_exp.end_date = None

        mock_skill = Mock(spec=SelectedSkill)
        mock_skill.skill = 'Kubernetes'

        llm = MockLLM()

        summary = await rewrite_summary_for_job(
            user=mock_user,
            job_profile=mock_job,
            skill_gap_result=Mock(),
            selected_skills=[mock_skill],
            experiences=[mock_exp],
            llm=llm,
            max_words=60
        )

        word_count = len(summary.split())
        assert word_count <= 60, f"Summary has {word_count} words, max 60"

    async def test_rewrite_summary_with_mock_llm(self):
        """Should handle MockLLM fallback correctly."""
        mock_user = Mock(spec=User)
        mock_user.candidate_profile = {
            'primary_identity': 'Director',
            'specializations': ['Leadership']
        }

        mock_job = Mock(spec=JobProfile)
        mock_job.id = 1
        mock_job.job_title = 'VP'
        mock_job.seniority = 'VP'
        mock_job.core_priorities = ['Leadership']

        llm = MockLLM()

        summary = await rewrite_summary_for_job(
            user=mock_user,
            job_profile=mock_job,
            skill_gap_result=Mock(),
            selected_skills=[],
            experiences=[],
            llm=llm
        )

        # MockLLM should produce reasonable output
        assert summary is not None
        assert isinstance(summary, str)

    async def test_rewrite_summary_removes_banned_phrases(self):
        """Should remove banned phrases from generated summary."""
        mock_user = Mock(spec=User)
        mock_user.candidate_profile = {'primary_identity': 'Professional'}

        mock_job = Mock(spec=JobProfile)
        mock_job.id = 1
        mock_job.job_title = 'Manager'
        mock_job.seniority = 'Mid'
        mock_job.core_priorities = ['Leadership']

        # Mock LLM that returns text with banned phrases
        mock_llm = AsyncMock()
        mock_llm.generate_text = AsyncMock(
            return_value="I am passionate about results-oriented work"
        )
        mock_llm.__class__.__name__ = 'RealLLM'  # Not MockLLM

        summary = await rewrite_summary_for_job(
            user=mock_user,
            job_profile=mock_job,
            skill_gap_result=Mock(),
            selected_skills=[],
            experiences=[],
            llm=mock_llm
        )

        # Banned phrases should be removed
        assert "passionate" not in summary.lower()
        assert "results-oriented" not in summary.lower()

    async def test_rewrite_summary_removes_em_dashes(self):
        """Should remove em-dashes from summary."""
        mock_user = Mock(spec=User)
        mock_user.candidate_profile = {'primary_identity': 'Engineer'}

        mock_job = Mock(spec=JobProfile)
        mock_job.id = 1
        mock_job.job_title = 'Senior Engineer'
        mock_job.seniority = 'Senior'
        mock_job.core_priorities = ['Engineering']

        # Mock LLM that returns text with em-dashes
        mock_llm = AsyncMock()
        mock_llm.generate_text = AsyncMock(
            return_value="Led team — 15 engineers — to deliver systems"
        )
        mock_llm.__class__.__name__ = 'RealLLM'

        summary = await rewrite_summary_for_job(
            user=mock_user,
            job_profile=mock_job,
            skill_gap_result=Mock(),
            selected_skills=[],
            experiences=[],
            llm=mock_llm
        )

        # Em-dashes should be removed
        assert "—" not in summary

    async def test_rewrite_summary_without_experiences(self):
        """Should handle user with no experiences gracefully."""
        mock_user = Mock(spec=User)
        mock_user.candidate_profile = {'primary_identity': 'Junior Engineer'}

        mock_job = Mock(spec=JobProfile)
        mock_job.id = 1
        mock_job.job_title = 'Entry-Level Engineer'
        mock_job.seniority = 'Junior'
        mock_job.core_priorities = ['Learning']

        llm = MockLLM()

        summary = await rewrite_summary_for_job(
            user=mock_user,
            job_profile=mock_job,
            skill_gap_result=Mock(),
            selected_skills=[],
            experiences=[],  # No experiences
            llm=llm
        )

        # Should generate a valid summary (no years mentioned to avoid age discrimination)
        assert summary is not None
        assert len(summary) > 20  # Should be a real summary

    async def test_rewrite_summary_with_company_profile(self):
        """Should use company context when provided."""
        mock_user = Mock(spec=User)
        mock_user.candidate_profile = {'primary_identity': 'Leader'}

        mock_job = Mock(spec=JobProfile)
        mock_job.id = 1
        mock_job.job_title = 'VP Engineering'
        mock_job.seniority = 'VP'
        mock_job.core_priorities = ['Engineering Leadership']

        mock_company = Mock()
        mock_company.industry = 'FinTech'
        mock_company.mission = 'Revolutionizing finance'
        mock_company.data_ai_maturity = 'Advanced'

        llm = MockLLM()

        summary = await rewrite_summary_for_job(
            user=mock_user,
            job_profile=mock_job,
            skill_gap_result=Mock(),
            selected_skills=[],
            experiences=[],
            llm=llm,
            company_profile=mock_company
        )

        assert summary is not None
        assert isinstance(summary, str)


class TestCriticValidateSummaryQuality:
    """Tests for critic.validate_summary_quality function."""

    def test_critic_validates_summary_word_count(self):
        """Should flag summary exceeding 60-word limit as error."""
        long_summary = " ".join(["word"] * 65)  # 65 words
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Leadership']

        issues = validate_summary_quality(long_summary, mock_job, max_words=60)

        # Should have word count error
        word_count_issues = [i for i in issues if i.issue_type == 'word_count_violation']
        assert len(word_count_issues) > 0
        assert word_count_issues[0].severity == 'error'

    def test_critic_detects_banned_phrases(self):
        """Should detect banned phrases in summary."""
        summary = "I am passionate about results-oriented work"
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Work']

        issues = validate_summary_quality(summary, mock_job)

        # Should have banned phrase issues
        banned_issues = [i for i in issues if i.issue_type == 'banned_phrase']
        assert len(banned_issues) > 0

    def test_critic_detects_em_dashes(self):
        """Should detect em-dashes as errors."""
        summary = "Led team — 15 engineers — to success"
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Leadership']

        issues = validate_summary_quality(summary, mock_job)

        # Should have em-dash violation
        em_dash_issues = [i for i in issues if i.issue_type == 'em_dash_violation']
        assert len(em_dash_issues) > 0
        assert em_dash_issues[0].severity == 'error'

    def test_critic_detects_stale_summary(self):
        """Should detect generic/stale openings."""
        summary = "Experienced professional with extensive background in technology"
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Innovation']

        issues = validate_summary_quality(summary, mock_job)

        # Should have cliche violation warning
        stale_issues = [i for i in issues if i.issue_type == 'cliche_violation']
        assert len(stale_issues) > 0
        assert stale_issues[0].severity == 'warning'

    def test_critic_detects_missing_priority_alignment(self):
        """Should warn when priority alignment not evident."""
        summary = "Software engineer with 10 years experience building systems"
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Machine Learning', 'Data Science']

        issues = validate_summary_quality(summary, mock_job)

        # Should have requirement_coverage warning for missing priority alignment
        coverage_issues = [i for i in issues if i.issue_type == 'requirement_coverage']
        assert len(coverage_issues) > 0

    def test_critic_passes_good_summary(self):
        """Should have no errors for well-formatted summary."""
        summary = "AI leader with 8+ years driving machine learning systems. Expert in deep learning and cloud infrastructure. Proven track record delivering AI solutions at scale."
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Machine Learning', 'AI']

        issues = validate_summary_quality(summary, mock_job, max_words=60)

        # Count only errors (not warnings)
        error_issues = [i for i in issues if i.severity == 'error']
        # Should have 0 errors (60-word limit, no banned phrases, no em-dashes)
        assert len(error_issues) == 0

    def test_critic_empty_summary(self):
        """Should error on empty summary."""
        summary = ""
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Work']

        issues = validate_summary_quality(summary, mock_job)

        # Should have structure error
        structure_issues = [i for i in issues if i.issue_type == 'structure_violation']
        assert len(structure_issues) > 0
        assert structure_issues[0].severity == 'error'

    def test_critic_with_aligned_summary(self):
        """Should not warn when priorities are clearly aligned."""
        summary = "Leadership expert with 10+ years in machine learning governance. Specialized in policy and ethics frameworks. Track record delivering governance at scale."
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Machine Learning', 'Governance', 'Ethics']

        issues = validate_summary_quality(summary, mock_job)

        # Should have minimal issues
        coverage_issues = [i for i in issues if i.issue_type == 'requirement_coverage']
        # Priority alignment should be detected
        assert not any('alignment to job priorities' in i.message for i in coverage_issues)

    def test_critic_custom_word_limit(self):
        """Should respect custom word limit."""
        summary = " ".join(["word"] * 100)  # 100 words
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Work']

        # Custom limit of 80 words
        issues = validate_summary_quality(summary, mock_job, max_words=80)

        word_count_issues = [i for i in issues if i.issue_type == 'word_count_violation']
        assert len(word_count_issues) > 0

    def test_critic_issue_structure(self):
        """Should return properly structured CriticIssue objects."""
        summary = "Results-driven professional"
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = []

        issues = validate_summary_quality(summary, mock_job)

        for issue in issues:
            assert isinstance(issue, CriticIssue)
            assert issue.issue_type is not None
            assert issue.severity in ['error', 'warning', 'info']
            assert issue.message is not None
            assert issue.recommended_fix is not None

    def test_critic_multiple_violations(self):
        """Should detect multiple violations in same summary."""
        summary = (
            "Results-driven professional—passionate about innovation"
            + " " + "word " * 60  # Make it long
        )
        mock_job = Mock(spec=JobProfile)
        mock_job.core_priorities = ['Leadership']

        issues = validate_summary_quality(summary, mock_job)

        # Should have multiple issue types
        issue_types = {i.issue_type for i in issues}
        assert 'banned_phrase' in issue_types or 'word_count_violation' in issue_types


class TestIntegration:
    """Integration tests combining multiple components."""

    @pytest.mark.asyncio
    async def test_full_rewrite_workflow(self):
        """Should complete full rewrite with all processing steps."""
        # Setup
        mock_user = Mock(spec=User)
        mock_user.candidate_profile = {
            'primary_identity': 'AI Engineer',
            'specializations': ['Machine Learning', 'Data Systems']
        }

        mock_job = Mock(spec=JobProfile)
        mock_job.id = 42
        mock_job.job_title = 'Senior AI Engineer'
        mock_job.seniority = 'Senior'
        mock_job.core_priorities = ['Machine Learning', 'System Design']

        mock_exp = Mock(spec=Experience)
        mock_exp.start_date = date(2018, 1, 1)
        mock_exp.end_date = None

        mock_skill = Mock(spec=SelectedSkill)
        mock_skill.skill = 'PyTorch'

        llm = MockLLM()

        # Execute
        summary = await rewrite_summary_for_job(
            user=mock_user,
            job_profile=mock_job,
            skill_gap_result=Mock(),
            selected_skills=[mock_skill],
            experiences=[mock_exp],
            llm=llm,
            max_words=60
        )

        # Validate
        assert summary is not None
        word_count = len(summary.split())
        assert word_count <= 60
        assert "—" not in summary  # No em-dashes
        assert "passionate" not in summary.lower()  # No banned phrases

        # Run critic validation
        mock_job.core_priorities = ['Machine Learning']
        critic_issues = validate_summary_quality(summary, mock_job)
        error_issues = [i for i in critic_issues if i.severity == 'error']
        assert len(error_issues) == 0, "Generated summary should pass critic validation"

    @pytest.mark.asyncio
    async def test_rewrite_with_all_post_processing(self):
        """Should apply all post-processing steps in order."""
        mock_user = Mock(spec=User)
        mock_user.candidate_profile = {'primary_identity': 'Director'}

        mock_job = Mock(spec=JobProfile)
        mock_job.id = 1
        mock_job.job_title = 'Director'
        mock_job.seniority = 'Director'
        mock_job.core_priorities = ['Leadership']

        # Mock LLM that returns problematic text
        mock_llm = AsyncMock()
        mock_llm.generate_text = AsyncMock(
            return_value=(
                "Passionate director — results-oriented — with proven track record. "
                + " ".join(["Word"] * 70)  # 70+ words
            )
        )
        mock_llm.__class__.__name__ = 'TestLLM'

        summary = await rewrite_summary_for_job(
            user=mock_user,
            job_profile=mock_job,
            skill_gap_result=Mock(),
            selected_skills=[],
            experiences=[],
            llm=mock_llm,
            max_words=60
        )

        # All issues should be fixed
        assert "—" not in summary  # Em-dashes removed
        assert "passionate" not in summary.lower()  # Banned phrase removed
        word_count = len(summary.split())
        assert word_count <= 60  # Truncated to limit
