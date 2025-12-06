"""
Unit tests for the BulletRewriter service.

Tests bullet rewriting functionality including:
- Metric preservation validation
- Proper noun preservation
- LLM integration (mocked)
- Version history storage
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from services.bullet_rewriter import (
    extract_metrics,
    extract_proper_nouns,
    extract_action_verb,
    validate_rewrite,
    rewrite_bullet,
    store_version_history,
)


class TestExtractMetrics:
    """Tests for metric extraction from bullet text."""

    def test_extract_percentages(self):
        """Should extract percentage values."""
        text = "Improved efficiency by 45% and reduced costs by 30%"
        metrics = extract_metrics(text)
        assert "45%" in metrics
        assert "30%" in metrics

    def test_extract_numbers_with_commas(self):
        """Should extract large numbers with comma separators."""
        text = "Managed portfolio of 1,500,000 assets across 50 clients"
        metrics = extract_metrics(text)
        assert "1,500,000" in metrics
        assert "50" in metrics

    def test_extract_currency(self):
        """Should extract currency values."""
        text = "Generated $2.5M in revenue and saved $500K annually"
        metrics = extract_metrics(text)
        assert "$2.5M" in metrics or "2.5" in metrics
        assert "$500K" in metrics or "500" in metrics

    def test_extract_decimal_numbers(self):
        """Should extract decimal numbers."""
        text = "Achieved 4.5x ROI with 99.9% uptime"
        metrics = extract_metrics(text)
        assert "4.5" in metrics or "4.5x" in metrics
        assert "99.9%" in metrics


class TestExtractProperNouns:
    """Tests for proper noun extraction."""

    def test_extract_company_names(self):
        """Should extract company names."""
        text = "Led implementation at Goldman Sachs and Morgan Stanley"
        nouns = extract_proper_nouns(text)
        assert "Goldman" in nouns or "Goldman Sachs" in nouns
        assert "Morgan" in nouns or "Morgan Stanley" in nouns

    def test_filter_common_verbs(self):
        """Should filter out common action verbs."""
        text = "Led project at Fidelity using Python"
        nouns = extract_proper_nouns(text)
        assert "Led" not in nouns
        assert "Fidelity" in nouns
        assert "Python" in nouns

    def test_extract_technology_names(self):
        """Should extract technology proper nouns."""
        text = "Implemented Azure DevOps and AWS Lambda solutions"
        nouns = extract_proper_nouns(text)
        # Note: The regex matches multi-word capitalized phrases
        assert "Implemented Azure" in nouns or "Azure" in nouns
        assert "Lambda" in nouns


class TestExtractActionVerb:
    """Tests for action verb extraction."""

    def test_extract_first_verb(self):
        """Should extract the first word as action verb."""
        text = "Led cross-functional team of 15 engineers"
        verb = extract_action_verb(text)
        assert verb == "Led"

    def test_handle_punctuation(self):
        """Should strip trailing punctuation."""
        text = "Implemented, deployed, and maintained systems"
        verb = extract_action_verb(text)
        assert verb == "Implemented"

    def test_empty_text(self):
        """Should return None for empty text."""
        verb = extract_action_verb("")
        assert verb is None


class TestValidateRewrite:
    """Tests for rewrite validation logic."""

    def test_valid_rewrite_preserves_metrics(self):
        """Should pass when all metrics are preserved."""
        original = "Managed revenue by 45% serving 500+ clients"
        rewritten = "Drove 45% revenue growth across 500+ enterprise clients"
        is_valid, violations = validate_rewrite(original, rewritten)
        assert is_valid is True
        assert len(violations) == 0

    def test_invalid_rewrite_missing_metrics(self):
        """Should fail when metrics are missing."""
        original = "Increased revenue by 45% serving 500 clients"
        rewritten = "Drove significant revenue growth across enterprise clients"
        is_valid, violations = validate_rewrite(original, rewritten)
        assert is_valid is False
        assert any("Missing metrics" in v for v in violations)

    def test_invalid_rewrite_missing_proper_nouns(self):
        """Should fail when proper nouns are missing."""
        original = "Led implementation at Goldman Sachs"
        rewritten = "Led implementation at major financial institution"
        is_valid, violations = validate_rewrite(original, rewritten)
        assert is_valid is False
        assert any("Missing proper nouns" in v for v in violations)

    def test_valid_rewrite_preserves_both(self):
        """Should pass when both metrics and proper nouns are preserved."""
        original = "Built ML models using Azure achieving 95% accuracy for Fidelity"
        rewritten = "Architected ML solutions using Azure with 95% accuracy for Fidelity"
        is_valid, violations = validate_rewrite(original, rewritten)
        assert is_valid is True


class TestStoreVersionHistory:
    """Tests for version history storage."""

    def test_stores_version_entry(self):
        """Should store version entry in bullet's version_history."""
        # Create mock bullet
        mock_bullet = Mock()
        mock_bullet.id = 1
        mock_bullet.version_history = None

        # Create mock db session
        mock_db = Mock()

        store_version_history(
            db=mock_db,
            bullet=mock_bullet,
            rewritten_text="New bullet text",
            job_profile_id=42,
            keywords_added=["Python", "AI"],
            rewrite_type="keyword_optimization"
        )

        # Verify version_history was updated
        assert mock_bullet.version_history is not None
        assert "versions" in mock_bullet.version_history
        assert len(mock_bullet.version_history["versions"]) == 1

        version = mock_bullet.version_history["versions"][0]
        assert version["text"] == "New bullet text"
        assert version["context"] == "job_profile_42"
        assert version["keywords_added"] == ["Python", "AI"]
        assert version["rewrite_type"] == "keyword_optimization"

        # Verify db operations
        mock_db.add.assert_called_once_with(mock_bullet)
        mock_db.commit.assert_called_once()

    def test_appends_to_existing_history(self):
        """Should append to existing version history."""
        mock_bullet = Mock()
        mock_bullet.id = 1
        mock_bullet.version_history = {
            "versions": [{"text": "old version", "created_at": "2024-01-01"}]
        }

        mock_db = Mock()

        store_version_history(
            db=mock_db,
            bullet=mock_bullet,
            rewritten_text="New version",
            job_profile_id=99,
            keywords_added=["ML"],
        )

        assert len(mock_bullet.version_history["versions"]) == 2
        assert mock_bullet.version_history["versions"][1]["text"] == "New version"

    def test_limits_history_to_10_versions(self):
        """Should keep only last 10 versions."""
        mock_bullet = Mock()
        mock_bullet.id = 1
        mock_bullet.version_history = {
            "versions": [{"text": f"version_{i}"} for i in range(10)]
        }

        mock_db = Mock()

        store_version_history(
            db=mock_db,
            bullet=mock_bullet,
            rewritten_text="Version 11",
            job_profile_id=1,
            keywords_added=[],
        )

        assert len(mock_bullet.version_history["versions"]) == 10
        assert mock_bullet.version_history["versions"][-1]["text"] == "Version 11"


@pytest.mark.asyncio
class TestRewriteBullet:
    """Tests for the async rewrite_bullet function."""

    async def test_successful_rewrite(self):
        """Should return rewritten bullet on success."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Drove 45% revenue growth for Goldman Sachs"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result, success = await rewrite_bullet(
            bullet_text="Managed revenue by 45% at Goldman Sachs",
            jd_keywords=["revenue", "growth", "financial"],
            llm_client=mock_client,
            star_notes=None
        )

        assert success is True
        assert "45%" in result
        assert "Goldman" in result

    async def test_returns_original_on_validation_failure(self):
        """Should return original bullet if rewrite fails validation."""
        mock_client = Mock()
        # Rewrite missing the 45% metric
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Drove significant revenue growth"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        original = "Increased revenue by 45% at Goldman Sachs"
        result, success = await rewrite_bullet(
            bullet_text=original,
            jd_keywords=["revenue", "growth"],
            llm_client=mock_client,
        )

        assert success is False
        assert result == original  # Returns original on failure

    async def test_returns_original_on_exception(self):
        """Should return original bullet on LLM error."""
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        original = "Original bullet text"
        result, success = await rewrite_bullet(
            bullet_text=original,
            jd_keywords=["test"],
            llm_client=mock_client,
        )

        assert success is False
        assert result == original
