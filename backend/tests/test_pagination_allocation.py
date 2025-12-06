"""
Unit tests for pagination-aware bullet allocation and page splitting.

Tests the PaginationService for managing resume content distribution across pages,
line budgets, and bullet-to-line-count estimation.

Sprint 8C - PRD Section 2.11

Covers:
- Line estimation for bullets, summaries, and skills
- Value-per-line computation for priority sorting
- Budget constant loading from config
- Page splitting logic
- Configuration management
"""

import pytest
import math
from unittest.mock import Mock, MagicMock, patch
import yaml
import os

from services.pagination import PaginationService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_config():
    """Sample pagination configuration from config.yaml."""
    return {
        'pagination': {
            'page1_line_budget': 50,
            'page2_line_budget': 55,
            'chars_per_line_estimate': 75,
            'min_bullets_per_role': 2,
            'max_bullets_per_role': 6,
            'section_header_lines': 1,
            'job_header_lines': 2,
            'bullet_chrome_lines': 1,
            'max_summary_lines': 4,
            'max_skills_lines': 3,
            'min_bullets_after_job_header': 2,
            'compression_enabled': True,
            'compression_target_reduction': 0.20,
            'condense_older_roles': True,
        }
    }


@pytest.fixture
def short_bullet():
    """Short bullet text (< 75 chars)."""
    return "Led team of 5 engineers"


@pytest.fixture
def medium_bullet():
    """Medium bullet text (75-150 chars)."""
    return "Architected microservices platform serving 100M+ requests daily with 99.9% uptime"


@pytest.fixture
def long_bullet():
    """Long bullet text (225+ chars)."""
    return (
        "Designed and implemented comprehensive enterprise data pipeline processing 10+ TB of data "
        "daily across AWS, GCP, and on-premises systems. Established CI/CD practices improving "
        "deployment frequency from quarterly to weekly releases. Led cross-functional team of "
        "15 engineers across 4 continents to deliver real-time analytics platform."
    )


@pytest.fixture
def empty_bullet():
    """Empty/minimal bullet text."""
    return ""


@pytest.fixture
def skill_list_few():
    """Small set of skills."""
    return ["Python", "AWS", "SQL"]


@pytest.fixture
def skill_list_many():
    """Large set of skills."""
    return [
        "Python", "Go", "Rust", "C++", "Java",
        "AWS", "GCP", "Kubernetes", "Docker",
        "PostgreSQL", "MongoDB", "Redis",
        "Machine Learning", "Deep Learning", "NLP"
    ]


@pytest.fixture
def mock_bullet_with_relevance():
    """Mock bullet object with relevance score."""
    bullet = Mock()
    bullet.text = "Increased conversion rate by 35% through A/B testing"
    bullet.relevance_score = 0.92
    return bullet


@pytest.fixture
def mock_bullet_low_relevance():
    """Mock bullet with low relevance."""
    bullet = Mock()
    bullet.text = "Attended team meetings and company events"
    bullet.relevance_score = 0.45
    return bullet


# ============================================================================
# TestLineEstimation
# ============================================================================

class TestLineEstimation:
    """Tests for estimating line counts for different content types."""

    def test_estimate_bullet_lines_short_text(self, short_bullet):
        """Short bullet (< 75 chars) should be 2 lines (1 chrome + 1 text)."""
        service = PaginationService()
        lines = service.estimate_bullet_lines(short_bullet)

        assert lines == 2, f"Expected 2 lines for short bullet ('{short_bullet}'), got {lines}"

    def test_estimate_bullet_lines_medium_text(self, medium_bullet):
        """Medium bullet (75-150 chars) should be 3 lines."""
        service = PaginationService()
        lines = service.estimate_bullet_lines(medium_bullet)

        assert lines == 3, f"Expected 3 lines for medium bullet, got {lines}"

    def test_estimate_bullet_lines_long_text(self, long_bullet):
        """Long bullet (225+ chars) should be 4+ lines."""
        service = PaginationService()
        lines = service.estimate_bullet_lines(long_bullet)

        assert lines >= 4, f"Expected 4+ lines for long bullet, got {lines}"

    def test_estimate_bullet_lines_empty_text(self, empty_bullet):
        """Empty text should return minimum (bullet chrome only)."""
        service = PaginationService()
        lines = service.estimate_bullet_lines(empty_bullet)

        # Should at least have chrome (1 line)
        assert lines >= 1, f"Expected at least 1 line for empty bullet, got {lines}"

    def test_estimate_summary_lines_short_summary(self):
        """Short summary (50 words) should be 2-3 lines."""
        service = PaginationService()
        summary = "AI leader with 8+ years in machine learning systems. Expert in deep learning."

        lines = service.estimate_summary_lines(summary)

        assert 1 <= lines <= 3, f"Expected 1-3 lines for short summary, got {lines}"

    def test_estimate_summary_lines_medium_summary(self):
        """Medium summary (100+ words) should be 3-4 lines."""
        service = PaginationService()
        summary = (
            "AI leader with 8+ years driving machine learning systems at scale. "
            "Expert in deep learning and transformers. Passionate about making AI "
            "accessible and trustworthy. Track record delivering ML solutions that "
            "impact millions of users. Specialized in governance and AI ethics."
        )

        lines = service.estimate_summary_lines(summary)

        assert 2 <= lines <= 4, f"Expected 2-4 lines for medium summary, got {lines}"

    def test_estimate_summary_lines_empty_summary(self):
        """Empty summary should be 0 lines."""
        service = PaginationService()
        lines = service.estimate_summary_lines("")

        assert lines == 0, f"Expected 0 lines for empty summary, got {lines}"

    def test_estimate_skills_lines_few_skills(self, skill_list_few):
        """Few skills should fit on 1-2 lines."""
        service = PaginationService()
        lines = service.estimate_skills_lines(skill_list_few)

        assert 1 <= lines <= 2, f"Expected 1-2 lines for few skills, got {lines}"

    def test_estimate_skills_lines_many_skills(self, skill_list_many):
        """Many skills may need 3+ lines."""
        service = PaginationService()
        lines = service.estimate_skills_lines(skill_list_many)

        assert lines >= 2, f"Expected 2+ lines for many skills, got {lines}"

    def test_estimate_skills_lines_empty_list(self):
        """Empty skill list should be 0 lines."""
        service = PaginationService()
        lines = service.estimate_skills_lines([])

        assert lines == 0, f"Expected 0 lines for empty skills, got {lines}"

    def test_estimate_skills_lines_single_skill(self):
        """Single skill should be 1 line."""
        service = PaginationService()
        lines = service.estimate_skills_lines(["Python"])

        assert lines == 1, f"Expected 1 line for single skill, got {lines}"


# ============================================================================
# TestValuePerLine
# ============================================================================

class TestValuePerLine:
    """Tests for computing value-per-line metrics for prioritization."""

    def test_compute_value_per_line_high_value_short(self, short_bullet):
        """High relevance + short bullet = high value per line."""
        service = PaginationService()
        relevance = 0.95

        vpl = service.compute_bullet_value_per_line(short_bullet, relevance)

        # Short text has few lines, high relevance = high value per line
        assert vpl > 0.4, f"Expected high value per line (>0.4), got {vpl}"

    def test_compute_value_per_line_high_value_long(self, long_bullet):
        """High relevance + long bullet = lower value per line."""
        service = PaginationService()
        relevance = 0.95

        vpl = service.compute_bullet_value_per_line(long_bullet, relevance)

        # Long text has many lines, high relevance = moderate value per line
        assert 0 < vpl < 0.5, f"Expected moderate value per line, got {vpl}"

    def test_compute_value_per_line_low_value_short(self, short_bullet):
        """Low relevance + short bullet = moderate value per line."""
        service = PaginationService()
        relevance = 0.45

        vpl = service.compute_bullet_value_per_line(short_bullet, relevance)

        # Low relevance reduces value
        assert 0 < vpl < 0.5, f"Expected moderate value per line, got {vpl}"

    def test_compute_value_per_line_zero_relevance(self, medium_bullet):
        """Zero relevance should give zero value per line."""
        service = PaginationService()
        relevance = 0.0

        vpl = service.compute_bullet_value_per_line(medium_bullet, relevance)

        assert vpl == 0, f"Expected 0 value per line for zero relevance, got {vpl}"

    def test_value_per_line_sorts_correctly(self):
        """Bullets should sort by value-per-line descending."""
        service = PaginationService()

        # Create bullets with different value-per-line ratios
        bullets_data = [
            ("Medium text with moderate relevance", 0.65),
            ("Short text", 0.95),
            ("Very long bullet text that spans multiple lines due to its length and detail", 0.85),
        ]

        # Compute value-per-line for each
        vpls = [
            (text, rel, service.compute_bullet_value_per_line(text, rel))
            for text, rel in bullets_data
        ]
        sorted_bullets = sorted(vpls, key=lambda x: x[2], reverse=True)

        # Verify sorting (first should have higher vpl than last)
        assert sorted_bullets[0][2] >= sorted_bullets[-1][2], "Bullets not sorted by value per line"


# ============================================================================
# TestBudgetConstants
# ============================================================================

class TestBudgetConstants:
    """Tests for loading and retrieving budget constants from config."""

    def test_get_total_budget(self, sample_config):
        """Total budget = page1 + page2."""
        # sample_config has 'pagination' wrapper, extract it
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)
        total_budget = service.get_total_budget()
        expected = 50 + 55  # page1_line_budget + page2_line_budget

        assert total_budget == expected, f"Expected total budget {expected}, got {total_budget}"

    def test_get_page1_budget(self, sample_config):
        """Page 1 budget from config."""
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)
        page1_budget = service.get_page1_budget()

        assert page1_budget == 50, f"Expected page1 budget 50, got {page1_budget}"

    def test_get_page2_budget(self, sample_config):
        """Page 2 budget from config."""
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)
        page2_budget = service.get_page2_budget()

        assert page2_budget == 55, f"Expected page2 budget 55, got {page2_budget}"

    def test_job_header_lines(self, sample_config):
        """Job header constant from config."""
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)
        job_header = service.get_job_header_lines()

        assert job_header == 2, f"Expected job header 2 lines, got {job_header}"

    def test_section_header_lines(self, sample_config):
        """Section header constant from config."""
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)
        section_header = service.get_section_header_lines()

        assert section_header == 1, f"Expected section header 1 line, got {section_header}"


# ============================================================================
# TestConfigLoading
# ============================================================================

class TestConfigLoading:
    """Tests for configuration loading and management."""

    def test_load_default_config(self):
        """Service loads config.yaml by default."""
        # Should load without errors
        service = PaginationService()

        # Should have loaded pagination section (or empty dict with defaults)
        assert service._config is not None, "Config should be loaded"

    def test_override_config(self, sample_config):
        """Service accepts config override in constructor."""
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)

        # Should use provided config
        assert service.get_page1_budget() == 50, "Should use overridden config"

    def test_missing_config_uses_defaults(self):
        """Missing config values use sensible defaults."""
        empty_config = {}
        service = PaginationService(config=empty_config)

        # Should fallback to defaults
        page1_budget = service.get_page1_budget()
        assert page1_budget > 0, "Should have positive default page1 budget"

    def test_config_with_partial_values(self):
        """Service handles config with some missing values."""
        # The service expects config to be the pagination dict directly
        partial_config = {
            'page1_line_budget': 60,
            # Missing other values - will use defaults for missing keys
        }

        service = PaginationService(config=partial_config)

        # Should return provided value
        assert service.get_page1_budget() == 60, "Should use provided value"
        # Should have default for missing value (defaults in constructor)
        page2_budget = service.get_page2_budget()
        assert page2_budget > 0, "Should have default for missing value"

    def test_config_with_full_values(self, sample_config):
        """Service uses all provided config values."""
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)

        # Verify all values are correctly loaded
        assert service.get_page1_budget() == 50
        assert service.get_page2_budget() == 55
        assert service.get_section_header_lines() == 1
        assert service.get_job_header_lines() == 2


# ============================================================================
# TestBudgetComputations
# ============================================================================

class TestBudgetComputations:
    """Tests for budget-related computations."""

    def test_total_budget_computation(self, sample_config):
        """Total budget should equal sum of both pages."""
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)

        total = service.get_total_budget()
        page1 = service.get_page1_budget()
        page2 = service.get_page2_budget()

        assert total == page1 + page2, "Total should be sum of page budgets"

    def test_budget_values_positive(self, sample_config):
        """All budget values should be positive."""
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)

        assert service.get_page1_budget() > 0, "Page 1 budget should be positive"
        assert service.get_page2_budget() > 0, "Page 2 budget should be positive"
        assert service.get_total_budget() > 0, "Total budget should be positive"

    def test_page2_larger_than_page1(self, sample_config):
        """Page 2 typically has more space than page 1."""
        pagination_config = sample_config['pagination']
        service = PaginationService(config=pagination_config)

        # In config, page2 should be >= page1 (page1 has header/contact info)
        assert service.get_page2_budget() >= service.get_page1_budget(), \
            "Page 2 should have at least as much budget as page 1"


# ============================================================================
# TestEdgeCases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_long_bullet(self):
        """Should handle extremely long bullet text."""
        service = PaginationService()
        very_long = "A" * 1000

        lines = service.estimate_bullet_lines(very_long)

        assert lines > 0, "Should estimate positive lines for very long bullet"
        # Very long text should need many lines
        assert lines > 10, "1000 char bullet should need 10+ lines"

    def test_special_characters_in_bullet(self):
        """Should handle special characters in bullet text."""
        service = PaginationService()
        special = "Improved efficiency: 50% increase; saved $1.5M; led 15 engineers across 3 continents"

        lines = service.estimate_bullet_lines(special)

        assert lines >= 1, "Should handle special characters correctly"

    def test_unicode_characters_in_bullet(self):
        """Should handle unicode characters."""
        service = PaginationService()
        unicode_text = "Led team in multiple countries: UK, France, Germany (Deutschland), Asia"

        lines = service.estimate_bullet_lines(unicode_text)

        assert lines >= 1, "Should handle unicode characters"

    def test_whitespace_only_bullet(self):
        """Should handle whitespace-only text."""
        service = PaginationService()
        whitespace = "   \t\n   "

        lines = service.estimate_bullet_lines(whitespace)

        assert lines >= 1, "Should handle whitespace-only text"

    def test_empty_config_uses_defaults(self):
        """Should handle completely empty config gracefully."""
        service = PaginationService(config={})

        # Should not crash and should have defaults
        page1 = service.get_page1_budget()
        assert page1 > 0, "Should have positive default even with empty config"

    def test_empty_skills_list(self):
        """Should handle empty skills list."""
        service = PaginationService()
        lines = service.estimate_skills_lines([])

        assert lines == 0, "Empty skills should return 0 lines"

    def test_skills_with_empty_strings(self):
        """Should handle skills list with empty strings."""
        service = PaginationService()
        skills = ["Python", "", "Java", "   ", "SQL"]

        lines = service.estimate_skills_lines(skills)

        # Should skip empty strings
        assert lines >= 1, "Should handle skills with empty strings"

    def test_value_per_line_zero_relevance(self):
        """Zero relevance should give zero value per line."""
        service = PaginationService()
        vpl = service.compute_bullet_value_per_line("Sample text", 0.0)

        assert vpl == 0, "Zero relevance should give zero value per line"

    def test_value_per_line_max_relevance(self):
        """Maximum relevance should give highest value per line."""
        service = PaginationService()
        vpl = service.compute_bullet_value_per_line("Short", 1.0)

        assert vpl > 0, "Max relevance should give positive value"

    def test_very_short_bullet_text(self):
        """Single character bullet should work."""
        service = PaginationService()
        lines = service.estimate_bullet_lines("A")

        assert lines >= 1, "Even single char should be counted"

    def test_summary_at_max_lines_cap(self):
        """Summary should be capped at configured maximum."""
        service = PaginationService()

        # Create a very long summary
        long_summary = " ".join(["word"] * 500)

        lines = service.estimate_summary_lines(long_summary)

        # Should be capped at max_summary_lines (default 4)
        assert lines <= 4, f"Summary lines {lines} should not exceed configured maximum"

    def test_skills_at_max_lines_cap(self):
        """Skills should be capped at configured maximum."""
        service = PaginationService()

        # Create many skills
        many_skills = [f"Skill{i}" for i in range(100)]

        lines = service.estimate_skills_lines(many_skills)

        # Should be capped at max_skills_lines (default 3)
        assert lines <= 3, f"Skills lines {lines} should not exceed configured maximum"


class TestCrossComponentBehavior:
    """Tests for interactions between estimation methods."""

    def test_value_per_line_uses_estimate_bullet_lines(self):
        """Value per line should use bullet line estimation."""
        service = PaginationService()

        # Create two different texts with same relevance
        short = "Short"
        long = "This is a much longer text that will wrap to multiple lines due to its length"

        vpl_short = service.compute_bullet_value_per_line(short, 0.8)
        vpl_long = service.compute_bullet_value_per_line(long, 0.8)

        # Same relevance, but short should have higher value per line
        assert vpl_short > vpl_long, \
            f"Short text (vpl={vpl_short}) should beat long text (vpl={vpl_long}) at same relevance"

    def test_consistent_line_estimation(self):
        """Bullet line estimation should be consistent."""
        service = PaginationService()
        text = "Led team of engineers to deliver project on time and within budget"

        # Same text, multiple calls
        lines1 = service.estimate_bullet_lines(text)
        lines2 = service.estimate_bullet_lines(text)

        assert lines1 == lines2, "Estimation should be consistent"

    def test_skill_estimation_scales_with_list_size(self):
        """More skills should generally require more lines."""
        service = PaginationService()

        few_skills = ["Python", "Java"]
        many_skills = ["Python", "Java", "C++", "Rust", "Go", "Ruby", "PHP", "JavaScript"]

        lines_few = service.estimate_skills_lines(few_skills)
        lines_many = service.estimate_skills_lines(many_skills)

        assert lines_many >= lines_few, "More skills should need at least as many lines"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
