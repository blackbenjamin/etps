"""
Tests for Skills Formatter Service

Tests LLM-based skills categorization with validation guardrails.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from schemas.resume_tailor import SelectedSkill
from schemas.skills_formatter import SkillCategory, SkillsFormatterResponse, SKILL_CATEGORIES
from services.skills_formatter import (
    format_skills_with_llm,
    format_skills_sync,
    _normalize_skill_for_comparison,
    _build_allowed_skills_set,
    _validate_llm_response,
    _fallback_categorization,
    _parse_llm_response,
)


# Test fixtures
@pytest.fixture
def sample_skills():
    """Sample selected skills for testing."""
    return [
        SelectedSkill(
            skill="Python",
            priority_score=0.9,
            match_type="direct_match",
            source="user_master_resume"
        ),
        SelectedSkill(
            skill="Machine Learning",
            priority_score=0.85,
            match_type="direct_match",
            source="job_requirements"
        ),
        SelectedSkill(
            skill="AWS",
            priority_score=0.8,
            match_type="direct_match",
            source="user_master_resume"
        ),
        SelectedSkill(
            skill="Data Governance",
            priority_score=0.75,
            match_type="adjacent_skill",
            source="job_requirements"
        ),
        SelectedSkill(
            skill="Tableau",
            priority_score=0.7,
            match_type="transferable",
            source="user_master_resume"
        ),
        SelectedSkill(
            skill="Stakeholder Engagement",
            priority_score=0.65,
            match_type="user_competency",
            source="user_master_resume"
        ),
    ]


@pytest.fixture
def mock_job_profile():
    """Mock job profile for testing."""
    profile = MagicMock()
    profile.extracted_skills = ["Python", "Machine Learning", "AWS", "Data Governance"]
    profile.must_have_capabilities = ["Python", "Machine Learning"]
    return profile


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    llm = AsyncMock()
    return llm


# Test normalization
class TestNormalizeSkill:
    def test_normalize_lowercase(self):
        assert _normalize_skill_for_comparison("Python") == "python"

    def test_normalize_strips_whitespace(self):
        assert _normalize_skill_for_comparison("  Python  ") == "python"

    def test_normalize_preserves_special_chars(self):
        assert _normalize_skill_for_comparison("AWS/GCP") == "aws/gcp"


# Test allowed skills building
class TestBuildAllowedSkillsSet:
    def test_includes_selected_skills(self, sample_skills):
        allowed = _build_allowed_skills_set(sample_skills)
        assert "python" in allowed
        assert "machine learning" in allowed
        assert "aws" in allowed

    def test_includes_job_profile_skills(self, sample_skills, mock_job_profile):
        allowed = _build_allowed_skills_set(sample_skills, mock_job_profile)
        assert "python" in allowed
        assert "data governance" in allowed

    def test_deduplicates_skills(self, sample_skills, mock_job_profile):
        allowed = _build_allowed_skills_set(sample_skills, mock_job_profile)
        # Python appears in both, but should only be in set once
        count = sum(1 for s in allowed if s == "python")
        assert count == 1

    def test_handles_none_job_profile(self, sample_skills):
        allowed = _build_allowed_skills_set(sample_skills, None)
        assert len(allowed) == len(sample_skills)


# Test LLM response validation
class TestValidateLLMResponse:
    def test_accepts_valid_skills(self):
        categories = [
            SkillCategory(category_name="Programming", skills=["Python", "SQL"])
        ]
        allowed = {"python", "sql"}

        validated, rejected = _validate_llm_response(categories, allowed)

        assert len(validated) == 1
        assert validated[0].skills == ["Python", "SQL"]
        assert len(rejected) == 0

    def test_rejects_hallucinated_skills(self):
        categories = [
            SkillCategory(category_name="Programming", skills=["Python", "JavaScript"])
        ]
        allowed = {"python"}  # JavaScript not allowed

        validated, rejected = _validate_llm_response(categories, allowed)

        assert len(validated) == 1
        assert validated[0].skills == ["Python"]
        assert "JavaScript" in rejected

    def test_removes_empty_categories(self):
        categories = [
            SkillCategory(category_name="Programming", skills=["JavaScript"])
        ]
        allowed = {"python"}  # JavaScript not allowed, category becomes empty

        validated, rejected = _validate_llm_response(categories, allowed)

        assert len(validated) == 0
        assert "JavaScript" in rejected


# Test fallback categorization
class TestFallbackCategorization:
    def test_categorizes_ai_ml_skills(self, sample_skills):
        categories = _fallback_categorization(sample_skills)

        # Find AI/ML category
        ai_ml = next((c for c in categories if c.category_name == "AI/ML"), None)
        assert ai_ml is not None
        assert "Machine Learning" in ai_ml.skills

    def test_categorizes_programming_skills(self, sample_skills):
        categories = _fallback_categorization(sample_skills)

        # Find Programming category
        prog = next((c for c in categories if "Programming" in c.category_name), None)
        assert prog is not None
        assert "Python" in prog.skills

    def test_categorizes_cloud_skills(self, sample_skills):
        categories = _fallback_categorization(sample_skills)

        # Find Cloud category
        cloud = next((c for c in categories if "Cloud" in c.category_name), None)
        assert cloud is not None
        assert "AWS" in cloud.skills

    def test_uncategorized_goes_to_other(self):
        # Use skills that truly don't match any category patterns
        skills = [
            SelectedSkill(
                skill="Communication",
                priority_score=0.7,
                match_type="user_competency",
                source="user_master_resume"
            ),
            SelectedSkill(
                skill="Problem Solving",
                priority_score=0.6,
                match_type="user_competency",
                source="user_master_resume"
            ),
        ]
        categories = _fallback_categorization(skills)

        # These skills should be in Other
        other = next((c for c in categories if "Other" in c.category_name), None)
        assert other is not None
        assert "Communication" in other.skills
        assert "Problem Solving" in other.skills

    def test_handles_empty_skills(self):
        categories = _fallback_categorization([])
        assert categories == []


# Test sync formatting
class TestFormatSkillsSync:
    def test_returns_dict_structure(self, sample_skills):
        result = format_skills_sync(sample_skills)

        assert isinstance(result, dict)
        # Should have at least one category
        assert len(result) > 0

    def test_categorizes_correctly(self, sample_skills):
        result = format_skills_sync(sample_skills)

        # Check that Python is in programming category
        found_python = False
        for category, skills in result.items():
            if "Python" in skills:
                found_python = True
                break
        assert found_python

    def test_handles_empty_input(self):
        result = format_skills_sync([])
        assert result == {}


# Test LLM response parsing
class TestParseLLMResponse:
    def test_parses_valid_response(self):
        response = {
            "categories": [
                {"category_name": "AI/ML", "skills": ["Python", "Machine Learning"]},
                {"category_name": "Cloud", "skills": ["AWS"]}
            ]
        }

        categories = _parse_llm_response(response)

        assert len(categories) == 2
        assert categories[0].category_name == "AI/ML"
        assert categories[0].skills == ["Python", "Machine Learning"]

    def test_handles_empty_response(self):
        categories = _parse_llm_response({})
        assert categories == []

    def test_handles_none_response(self):
        categories = _parse_llm_response(None)
        assert categories == []

    def test_filters_invalid_categories(self):
        response = {
            "categories": [
                {"category_name": "AI/ML", "skills": ["Python"]},
                {"invalid": "data"},  # Missing category_name
                {"category_name": "", "skills": ["AWS"]},  # Empty category_name
            ]
        }

        categories = _parse_llm_response(response)

        assert len(categories) == 1
        assert categories[0].category_name == "AI/ML"


# Test async LLM formatting
class TestFormatSkillsWithLLM:
    @pytest.mark.asyncio
    async def test_success_with_mock_llm(self, sample_skills, mock_llm, mock_job_profile):
        mock_llm.generate_json.return_value = {
            "categories": [
                {"category_name": "AI/ML", "skills": ["Machine Learning"]},
                {"category_name": "Programming Languages & Frameworks", "skills": ["Python"]},
                {"category_name": "Cloud & Infrastructure", "skills": ["AWS"]},
            ]
        }

        result = await format_skills_with_llm(
            selected_skills=sample_skills,
            llm=mock_llm,
            job_profile=mock_job_profile,
            job_title="Data Scientist"
        )

        assert isinstance(result, SkillsFormatterResponse)
        assert result.validation_passed
        assert not result.fallback_used
        assert len(result.categories) == 3

    @pytest.mark.asyncio
    async def test_rejects_hallucinated_skills(self, sample_skills, mock_llm, mock_job_profile):
        # LLM returns a skill not in the allowed list
        mock_llm.generate_json.return_value = {
            "categories": [
                {"category_name": "AI/ML", "skills": ["Machine Learning", "Deep Learning"]},  # Deep Learning not allowed
            ]
        }

        result = await format_skills_with_llm(
            selected_skills=sample_skills,
            llm=mock_llm,
            job_profile=mock_job_profile
        )

        assert not result.validation_passed
        assert "Deep Learning" in result.validation_errors

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self, sample_skills, mock_llm):
        mock_llm.generate_json.side_effect = Exception("LLM API error")

        result = await format_skills_with_llm(
            selected_skills=sample_skills,
            llm=mock_llm
        )

        assert result.fallback_used
        assert result.validation_passed
        assert len(result.categories) > 0

    @pytest.mark.asyncio
    async def test_fallback_on_empty_llm_response(self, sample_skills, mock_llm):
        mock_llm.generate_json.return_value = {}

        result = await format_skills_with_llm(
            selected_skills=sample_skills,
            llm=mock_llm
        )

        assert result.fallback_used

    @pytest.mark.asyncio
    async def test_handles_empty_skills_list(self, mock_llm):
        result = await format_skills_with_llm(
            selected_skills=[],
            llm=mock_llm
        )

        assert result.validation_passed
        assert len(result.categories) == 0
        assert not result.fallback_used


# Test schema validation
class TestSkillsFormatterSchema:
    def test_skill_category_validation(self):
        category = SkillCategory(
            category_name="AI/ML",
            skills=["Python", "Machine Learning"]
        )
        assert category.category_name == "AI/ML"
        assert len(category.skills) == 2

    def test_response_validation(self):
        response = SkillsFormatterResponse(
            categories=[SkillCategory(category_name="AI/ML", skills=["Python"])],
            validation_passed=True,
            validation_errors=[],
            fallback_used=False
        )
        assert response.validation_passed
        assert not response.fallback_used

    def test_predefined_categories_exist(self):
        assert "AI/ML" in SKILL_CATEGORIES
        assert "Programming Languages & Frameworks" in SKILL_CATEGORIES
        assert "Cloud & Infrastructure" in SKILL_CATEGORIES
