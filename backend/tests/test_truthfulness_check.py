"""
Unit tests for resume truthfulness validation.

Tests the critic's ability to detect fabricated information in resumes.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import date

from services.critic import validate_resume_truthfulness, CriticIssue


@pytest.fixture
def mock_db_session():
    """Create a mock database session with sample experiences."""
    mock_db = MagicMock()

    # Create mock experiences
    exp1 = Mock()
    exp1.id = 1
    exp1.user_id = 100
    exp1.employer_name = "Acme Corp"
    exp1.job_title = "Senior Engineer"
    exp1.location = "New York, NY"
    exp1.start_date = date(2020, 1, 15)
    exp1.end_date = date(2023, 6, 30)

    exp2 = Mock()
    exp2.id = 2
    exp2.user_id = 100
    exp2.employer_name = "Tech Startup Inc"
    exp2.job_title = "Principal Consultant"
    exp2.location = "Boston, MA"
    exp2.start_date = date(2023, 7, 1)
    exp2.end_date = None  # Current role

    mock_db.query.return_value.filter.return_value.all.return_value = [exp1, exp2]

    return mock_db


@pytest.mark.asyncio
class TestTruthfulnessValidation:
    """Tests for the validate_resume_truthfulness function."""

    async def test_valid_resume_passes(self, mock_db_session):
        """Should pass when all fields match stored data."""
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": 1,
                    "employer_name": "Acme Corp",
                    "job_title": "Senior Engineer",
                    "location": "New York, NY",
                    "start_date": "2020-01-15",
                    "end_date": "2023-06-30"
                },
                {
                    "experience_id": 2,
                    "employer_name": "Tech Startup Inc",
                    "job_title": "Principal Consultant",
                    "location": "Boston, MA",
                    "start_date": "2023-07-01",
                    "end_date": None
                }
            ]
        }

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=100,
            db=mock_db_session
        )

        assert is_truthful is True
        assert len(issues) == 0

    async def test_detects_employer_name_change(self, mock_db_session):
        """Should detect when employer name is altered."""
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": 1,
                    "employer_name": "Google",  # Changed from "Acme Corp"
                    "job_title": "Senior Engineer",
                    "start_date": "2020-01-15",
                }
            ]
        }

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=100,
            db=mock_db_session
        )

        assert is_truthful is False
        assert len(issues) >= 1
        assert any("Employer name mismatch" in i.message for i in issues)
        assert any(i.severity == "error" for i in issues)

    async def test_detects_job_title_change(self, mock_db_session):
        """Should detect when job title is altered."""
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": 1,
                    "employer_name": "Acme Corp",
                    "job_title": "VP of Engineering",  # Changed from "Senior Engineer"
                    "start_date": "2020-01-15",
                }
            ]
        }

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=100,
            db=mock_db_session
        )

        assert is_truthful is False
        assert any("Job title mismatch" in i.message for i in issues)

    async def test_detects_date_changes(self, mock_db_session):
        """Should detect when employment dates are altered."""
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": 1,
                    "employer_name": "Acme Corp",
                    "job_title": "Senior Engineer",
                    "start_date": "2018-01-15",  # Changed from 2020
                    "end_date": "2023-06-30"
                }
            ]
        }

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=100,
            db=mock_db_session
        )

        assert is_truthful is False
        assert any("Start date mismatch" in i.message for i in issues)

    async def test_detects_fabricated_experience(self, mock_db_session):
        """Should detect experience IDs that don't exist in database."""
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": 999,  # Non-existent ID
                    "employer_name": "Fake Company",
                    "job_title": "Fake Title",
                    "start_date": "2020-01-01"
                }
            ]
        }

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=100,
            db=mock_db_session
        )

        assert is_truthful is False
        assert any("not found in stored employment history" in i.message for i in issues)

    async def test_skips_portfolio_bullets(self, mock_db_session):
        """Should skip validation for synthetic portfolio bullets (negative IDs)."""
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": -1001,  # Portfolio bullet
                    "employer_name": "Portfolio Project",
                    "job_title": "AI Project",
                }
            ]
        }

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=100,
            db=mock_db_session
        )

        assert is_truthful is True
        assert len(issues) == 0

    async def test_location_mismatch_is_warning_not_error(self, mock_db_session):
        """Should mark location mismatches as warning severity, not error."""
        resume_json = {
            "selected_roles": [
                {
                    "experience_id": 1,
                    "employer_name": "Acme Corp",
                    "job_title": "Senior Engineer",
                    "location": "San Francisco, CA",  # Changed from "New York, NY"
                    "start_date": "2020-01-15",
                }
            ]
        }

        is_truthful, issues = await validate_resume_truthfulness(
            resume_json=resume_json,
            user_id=100,
            db=mock_db_session
        )

        # Location issues are "warning" not "error", so still truthful
        assert is_truthful is True
        assert len(issues) == 1
        assert issues[0].severity == "warning"
