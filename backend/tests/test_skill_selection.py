"""
Tests for Skill Selection (Sprint 10E)

Tests the interactive skill selection panel backend functionality.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from db.models import JobProfile, User
from db.database import get_db, engine


client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    """Get database session for testing."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_user(db: Session) -> User:
    """Create or get a sample user for testing."""
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@pytest.fixture
def sample_job_profile(db: Session, sample_user: User) -> JobProfile:
    """Create a sample job profile for testing."""
    job = JobProfile(
        user_id=sample_user.id,
        raw_jd_text="Sample job description for AI Engineer role requiring Python, Machine Learning, and Data Analysis.",
        job_title="AI Engineer",
        extracted_skills=["Python", "Machine Learning", "Data Analysis", "SQL"]
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


class TestSkillSelectionEndpoint:
    """Tests for the PUT /job-profiles/{id}/skills endpoint."""

    def test_update_skill_selection_success(self, db: Session, sample_job_profile: JobProfile):
        """Test successful skill selection update."""
        request_body = {
            "selected_skills": [
                {"skill": "Python", "match_pct": 92.0, "included": True, "order": 0},
                {"skill": "Machine Learning", "match_pct": 85.0, "included": True, "order": 1},
                {"skill": "Data Analysis", "match_pct": 78.0, "included": True, "order": 2},
                {"skill": "SQL", "match_pct": 65.0, "included": False, "order": 3}
            ],
            "key_skills": ["Python", "Machine Learning"]
        }

        response = client.put(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills",
            json=request_body
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_profile_id"] == sample_job_profile.id
        assert len(data["selected_skills"]) == 4
        assert data["key_skills"] == ["Python", "Machine Learning"]
        assert "updated_at" in data

    def test_update_skill_selection_too_many_key_skills(self, db: Session, sample_job_profile: JobProfile):
        """Test validation: max 4 key skills."""
        request_body = {
            "selected_skills": [
                {"skill": "Python", "match_pct": 90.0, "included": True, "order": 0}
            ],
            "key_skills": ["Python", "ML", "SQL", "Java", "JavaScript"]  # 5 skills - should fail
        }

        response = client.put(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills",
            json=request_body
        )

        assert response.status_code == 422  # Validation error

    def test_update_skill_selection_job_not_found(self):
        """Test 404 when job profile doesn't exist."""
        response = client.put(
            "/api/v1/job/job-profiles/999999/skills",
            json={"selected_skills": [], "key_skills": []}
        )

        assert response.status_code == 404

    def test_update_skill_selection_duplicate_orders(self, db: Session, sample_job_profile: JobProfile):
        """Test validation: order values must be unique."""
        request_body = {
            "selected_skills": [
                {"skill": "Python", "match_pct": 90.0, "included": True, "order": 0},
                {"skill": "ML", "match_pct": 80.0, "included": True, "order": 0}  # Duplicate order
            ],
            "key_skills": []
        }

        response = client.put(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills",
            json=request_body
        )

        assert response.status_code == 422  # Validation error

    def test_update_skill_selection_empty_key_skills(self, db: Session, sample_job_profile: JobProfile):
        """Test that empty key_skills is allowed."""
        request_body = {
            "selected_skills": [
                {"skill": "Python", "match_pct": 90.0, "included": True, "order": 0}
            ],
            "key_skills": []
        }

        response = client.put(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills",
            json=request_body
        )

        assert response.status_code == 200
        data = response.json()
        assert data["key_skills"] == []


class TestGetSkillSelection:
    """Tests for the GET /job-profiles/{id}/skills endpoint."""

    def test_get_skill_selection_empty(self, db: Session, sample_job_profile: JobProfile):
        """Test getting skill selection when none has been set."""
        response = client.get(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_profile_id"] == sample_job_profile.id
        assert data["selected_skills"] == []
        assert data["key_skills"] == []

    def test_get_skill_selection_after_save(self, db: Session, sample_job_profile: JobProfile):
        """Test getting skill selection after saving."""
        # First, save a selection
        request_body = {
            "selected_skills": [
                {"skill": "Python", "match_pct": 92.0, "included": True, "order": 0},
                {"skill": "Machine Learning", "match_pct": 85.0, "included": True, "order": 1}
            ],
            "key_skills": ["Python"]
        }

        put_response = client.put(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills",
            json=request_body
        )
        assert put_response.status_code == 200

        # Then, get it back
        get_response = client.get(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills"
        )

        assert get_response.status_code == 200
        data = get_response.json()
        assert len(data["selected_skills"]) == 2
        assert data["key_skills"] == ["Python"]

    def test_get_skill_selection_job_not_found(self):
        """Test 404 when job profile doesn't exist."""
        response = client.get("/api/v1/job/job-profiles/999999/skills")
        assert response.status_code == 404


class TestSkillSelectionPersistence:
    """Tests for skill selection data persistence."""

    def test_skill_selection_persists_to_database(self, db: Session, sample_job_profile: JobProfile):
        """Test that skill selections are correctly persisted to the database."""
        request_body = {
            "selected_skills": [
                {"skill": "Python", "match_pct": 92.0, "included": True, "order": 0},
                {"skill": "Machine Learning", "match_pct": 85.0, "included": False, "order": 1}
            ],
            "key_skills": ["Python"]
        }

        response = client.put(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills",
            json=request_body
        )
        assert response.status_code == 200

        # Refresh the job profile from database
        db.refresh(sample_job_profile)

        # Verify data persisted correctly
        assert sample_job_profile.selected_skills is not None
        assert len(sample_job_profile.selected_skills) == 2
        assert sample_job_profile.selected_skills[0]["skill"] == "Python"
        assert sample_job_profile.selected_skills[0]["included"] == True
        assert sample_job_profile.selected_skills[1]["included"] == False

        assert sample_job_profile.key_skills == ["Python"]

    def test_skill_selection_can_be_updated(self, db: Session, sample_job_profile: JobProfile):
        """Test that skill selections can be updated multiple times."""
        # First save
        request1 = {
            "selected_skills": [
                {"skill": "Python", "match_pct": 90.0, "included": True, "order": 0}
            ],
            "key_skills": ["Python"]
        }
        response1 = client.put(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills",
            json=request1
        )
        assert response1.status_code == 200

        # Second save with different data
        request2 = {
            "selected_skills": [
                {"skill": "Machine Learning", "match_pct": 85.0, "included": True, "order": 0},
                {"skill": "Python", "match_pct": 90.0, "included": True, "order": 1}
            ],
            "key_skills": ["Machine Learning", "Python"]
        }
        response2 = client.put(
            f"/api/v1/job/job-profiles/{sample_job_profile.id}/skills",
            json=request2
        )
        assert response2.status_code == 200

        # Verify the update
        db.refresh(sample_job_profile)
        assert len(sample_job_profile.selected_skills) == 2
        assert sample_job_profile.selected_skills[0]["skill"] == "Machine Learning"
        assert len(sample_job_profile.key_skills) == 2
