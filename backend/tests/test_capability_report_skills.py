"""
Tests for Capability Report Skills Feature (Sprint 11D)

Tests for the "Report Unregistered Skills" feature that allows users to add
skills they possess that aren't currently matched in the Capability Cluster Analysis.
Includes tests for:
- POST /api/v1/capability/job-profiles/{job_profile_id}/user-skills
- GET /api/v1/users/{user_id}/experiences
"""

import pytest
from datetime import datetime, date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from db.models import JobProfile, User, Experience, Engagement, Bullet
from db.database import get_db


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
    """Create a dedicated test user for capability report tests."""
    # Check if test user already exists and reuse it
    existing = db.query(User).filter(User.username == "capability_report_test_user").first()
    if existing:
        return existing

    # Create fresh test user
    user = User(
        username="capability_report_test_user",
        email="capability_report_test@example.com",
        full_name="Capability Report Test User"
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
        raw_jd_text="Senior AI Engineer role requiring Python, Machine Learning, and Data Analysis.",
        job_title="Senior AI Engineer",
        company_name="Test Corp",
        seniority="Senior",
        extracted_skills=["Python", "Machine Learning", "Data Analysis", "SQL"]
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@pytest.fixture
def sample_experience(db: Session, sample_user: User) -> Experience:
    """Create a sample experience for the user."""
    exp = Experience(
        user_id=sample_user.id,
        employer_name="Tech Corp",
        job_title="AI Engineer",
        description="Worked on ML systems",
        start_date=date(2020, 1, 1),
        end_date=date(2023, 12, 31),
        order=0,
        employer_type="full_time",
        tools_and_technologies=["Python", "TensorFlow"]
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@pytest.fixture
def sample_bullets(db: Session, sample_user: User, sample_experience: Experience) -> list:
    """Create sample bullets for the experience."""
    bullets = [
        Bullet(
            user_id=sample_user.id,
            experience_id=sample_experience.id,
            text="Developed machine learning models using Python and scikit-learn",
            tags=["Machine Learning", "Python"],
            retired=False,
            order=0
        ),
        Bullet(
            user_id=sample_user.id,
            experience_id=sample_experience.id,
            text="Optimized SQL queries for data analysis pipelines",
            tags=["SQL", "Data Analysis"],
            retired=False,
            order=1
        ),
        Bullet(
            user_id=sample_user.id,
            experience_id=sample_experience.id,
            text="Led team of 3 engineers on critical AI infrastructure project",
            tags=["Leadership", "AI"],
            retired=False,
            order=2
        )
    ]
    db.add_all(bullets)
    db.commit()
    for bullet in bullets:
        db.refresh(bullet)
    return bullets


@pytest.fixture
def sample_consulting_experience(db: Session, sample_user: User) -> Experience:
    """Create a consulting experience with engagements."""
    exp = Experience(
        user_id=sample_user.id,
        employer_name="Consulting Firm",
        job_title="Senior Consultant",
        description="Consulting engagements",
        start_date=date(2019, 1, 1),
        end_date=date(2020, 12, 31),
        order=1,
        employer_type="independent_consulting"
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@pytest.fixture
def sample_engagement(db: Session, sample_consulting_experience: Experience) -> Engagement:
    """Create a sample engagement within consulting experience."""
    engagement = Engagement(
        experience_id=sample_consulting_experience.id,
        client="Fortune 500 Company",
        project_name="Digital Transformation Strategy",
        project_type="advisory",
        date_range_label="Q1-Q2 2020",
        domain_tags=["AI Strategy", "Digital Transformation"],
        tech_tags=["AWS", "Python"],
        order=0
    )
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    return engagement


@pytest.fixture
def sample_engagement_bullets(db: Session, sample_user: User, sample_engagement: Engagement) -> list:
    """Create sample bullets for the engagement."""
    bullets = [
        Bullet(
            user_id=sample_user.id,
            experience_id=sample_engagement.experience_id,
            engagement_id=sample_engagement.id,
            text="Developed AI strategy roadmap for enterprise client",
            tags=["AI Strategy", "Consulting"],
            retired=False,
            order=0
        ),
        Bullet(
            user_id=sample_user.id,
            experience_id=sample_engagement.experience_id,
            engagement_id=sample_engagement.id,
            text="Architected cloud-native ML pipeline on AWS",
            tags=["AWS", "Machine Learning"],
            retired=False,
            order=1
        )
    ]
    db.add_all(bullets)
    db.commit()
    for bullet in bullets:
        db.refresh(bullet)
    return bullets


class TestAddUserSkill:
    """Tests for POST /api/v1/capability/job-profiles/{job_profile_id}/user-skills"""

    def test_add_skill_to_experience(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_experience: Experience
    ):
        """Test POST adds skill to experience.tools_and_technologies"""
        request_body = {
            "skill_name": "Kubernetes",
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": []
                }
            ]
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()
        assert data["skill_name"] == "Kubernetes"
        assert data["user_id"] == sample_job_profile.user_id
        assert data["entities_updated"] >= 1
        assert "added_at" in data
        assert isinstance(data["added_at"], str)  # ISO datetime

    def test_add_skill_to_bullets(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_experience: Experience,
        sample_bullets: list
    ):
        """Test POST adds skill to bullet.tags for specific bullets"""
        request_body = {
            "skill_name": "Apache Spark",
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": [sample_bullets[0].id, sample_bullets[1].id]
                }
            ]
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()
        assert data["skill_name"] == "Apache Spark"
        assert data["entities_updated"] == 2  # 2 bullets updated

    def test_add_skill_to_engagement_bullets(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_consulting_experience: Experience,
        sample_engagement: Engagement,
        sample_engagement_bullets: list
    ):
        """Test POST adds skill with engagement_id specified"""
        request_body = {
            "skill_name": "Prompt Engineering",
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_consulting_experience.id,
                    "engagement_id": sample_engagement.id,
                    "bullet_ids": [sample_engagement_bullets[0].id]
                }
            ]
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_body
        )

        assert response.status_code == 201
        data = response.json()
        assert data["skill_name"] == "Prompt Engineering"
        assert data["entities_updated"] >= 1

    def test_add_skill_validation_empty_mappings(
        self,
        db: Session,
        sample_job_profile: JobProfile
    ):
        """Test POST returns 400 for empty evidence_mappings"""
        request_body = {
            "skill_name": "Docker",
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": []  # Empty - should fail
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_body
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data or "evidence_mappings" in str(data)

    def test_add_skill_validation_long_name(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_experience: Experience
    ):
        """Test POST returns 400 for skill_name > 100 chars"""
        long_skill_name = "A" * 101  # Exceeds max_length of 100

        request_body = {
            "skill_name": long_skill_name,
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": []
                }
            ]
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_body
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data or "skill_name" in str(data)

    def test_add_skill_validation_empty_skill_name(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_experience: Experience
    ):
        """Test POST returns 400 for empty skill_name"""
        request_body = {
            "skill_name": "",  # Empty - should fail
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": []
                }
            ]
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_body
        )

        assert response.status_code == 400

    def test_add_skill_job_profile_not_found(
        self,
        db: Session,
        sample_user: User,
        sample_experience: Experience
    ):
        """Test POST returns 404 for invalid job_profile_id"""
        invalid_job_profile_id = 999999

        request_body = {
            "skill_name": "Kubernetes",
            "user_id": sample_user.id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": []
                }
            ]
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{invalid_job_profile_id}/user-skills",
            json=request_body
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data.get("detail", "").lower()

    def test_add_skill_experience_not_found(
        self,
        db: Session,
        sample_job_profile: JobProfile
    ):
        """Test POST returns 404 for invalid experience_id"""
        invalid_experience_id = 999999

        request_body = {
            "skill_name": "Docker",
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": invalid_experience_id,
                    "engagement_id": None,
                    "bullet_ids": []
                }
            ]
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_body
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data.get("detail", "").lower()

    def test_add_skill_engagement_not_found(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_consulting_experience: Experience
    ):
        """Test POST returns 404 for invalid engagement_id"""
        invalid_engagement_id = 999999

        request_body = {
            "skill_name": "Prompt Engineering",
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_consulting_experience.id,
                    "engagement_id": invalid_engagement_id,
                    "bullet_ids": []
                }
            ]
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_body
        )

        assert response.status_code == 404

    def test_add_skill_bullet_not_found(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_experience: Experience
    ):
        """Test POST returns 404 for invalid bullet_id"""
        invalid_bullet_id = 999999

        request_body = {
            "skill_name": "Apache Spark",
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": [invalid_bullet_id]
                }
            ]
        }

        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_body
        )

        assert response.status_code == 404


class TestGetUserExperiences:
    """Tests for GET /api/v1/users/{user_id}/experiences"""

    def test_get_user_experiences(
        self,
        db: Session,
        sample_user: User,
        sample_experience: Experience,
        sample_bullets: list
    ):
        """Test GET returns all experiences with engagements/bullets"""
        response = client.get(f"/api/v1/users/{sample_user.id}/experiences")

        assert response.status_code == 200
        data = response.json()

        # Should be a list of experiences
        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our test experience
        exp_data = None
        for exp in data:
            if exp["id"] == sample_experience.id:
                exp_data = exp
                break

        assert exp_data is not None
        assert exp_data["job_title"] == sample_experience.job_title
        assert exp_data["employer_name"] == sample_experience.employer_name
        assert exp_data["employer_type"] == "full_time"
        assert exp_data["tools_and_technologies"] == ["Python", "TensorFlow"]

        # Should have nested engagements (empty for non-consulting)
        assert "engagements" in exp_data
        assert isinstance(exp_data["engagements"], list)

        # Should have nested bullets
        assert "bullets" in exp_data
        assert isinstance(exp_data["bullets"], list)
        assert len(exp_data["bullets"]) == 3

        # Check bullet structure
        for bullet in exp_data["bullets"]:
            assert "id" in bullet
            assert "text" in bullet
            assert "tags" in bullet
            assert isinstance(bullet["tags"], list)

    def test_get_user_experiences_with_consulting(
        self,
        db: Session,
        sample_user: User,
        sample_consulting_experience: Experience,
        sample_engagement: Engagement,
        sample_engagement_bullets: list
    ):
        """Test GET returns consulting experiences with nested engagements"""
        response = client.get(f"/api/v1/users/{sample_user.id}/experiences")

        assert response.status_code == 200
        data = response.json()

        # Find consulting experience
        consulting_exp = None
        for exp in data:
            if exp["id"] == sample_consulting_experience.id:
                consulting_exp = exp
                break

        assert consulting_exp is not None
        assert consulting_exp["employer_type"] == "independent_consulting"

        # Check engagements
        assert "engagements" in consulting_exp
        assert len(consulting_exp["engagements"]) >= 1

        # Find our test engagement
        eng_data = None
        for eng in consulting_exp["engagements"]:
            if eng["id"] == sample_engagement.id:
                eng_data = eng
                break

        assert eng_data is not None
        assert eng_data["client"] == "Fortune 500 Company"
        assert eng_data["project_name"] == "Digital Transformation Strategy"

        # Check engagement bullets
        assert "bullets" in eng_data
        assert len(eng_data["bullets"]) == 2

    def test_get_user_experiences_empty(
        self,
        db: Session,
        sample_user: User
    ):
        """Test GET returns empty list for user with no experiences"""
        # Create a fresh user with no experiences (use unique uuid for username)
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        fresh_user = User(
            username=f"fresh_test_user_{unique_id}",
            email=f"fresh_{unique_id}@example.com",
            full_name="Fresh Test User"
        )
        db.add(fresh_user)
        db.commit()
        db.refresh(fresh_user)

        response = client.get(f"/api/v1/users/{fresh_user.id}/experiences")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_user_experiences_not_found(self):
        """Test GET returns 404 for invalid user_id"""
        invalid_user_id = 999999

        response = client.get(f"/api/v1/users/{invalid_user_id}/experiences")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data.get("detail", "").lower()

    def test_get_user_experiences_response_structure(
        self,
        db: Session,
        sample_user: User,
        sample_experience: Experience,
        sample_bullets: list
    ):
        """Test response has correct structure with all required fields"""
        response = client.get(f"/api/v1/users/{sample_user.id}/experiences")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        exp = data[0]

        # Required fields at experience level
        assert "id" in exp
        assert "job_title" in exp
        assert "employer_name" in exp
        assert "employer_type" in exp
        assert "tools_and_technologies" in exp or exp["tools_and_technologies"] is None
        assert "engagements" in exp
        assert "bullets" in exp

        # Bullet structure
        if exp["bullets"]:
            bullet = exp["bullets"][0]
            assert "id" in bullet
            assert "text" in bullet
            assert "tags" in bullet


class TestSkillPersistence:
    """Tests for skill data persistence after POST"""

    def test_skill_persists_after_add(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_experience: Experience
    ):
        """Verify skill appears in DB after POST and can be retrieved"""
        skill_name = "Kubernetes"

        # Add skill
        add_request = {
            "skill_name": skill_name,
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": []
                }
            ]
        }

        add_response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=add_request
        )

        assert add_response.status_code == 201

        # Refresh experience and check skill persisted
        db.refresh(sample_experience)

        # Verify skill is in tools_and_technologies
        assert sample_experience.tools_and_technologies is not None
        assert skill_name in sample_experience.tools_and_technologies

    def test_skill_added_to_bullet_tags_persists(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_experience: Experience,
        sample_bullets: list
    ):
        """Verify skill is added to bullet tags and persists"""
        skill_name = "RAG Systems"
        target_bullet = sample_bullets[0]

        # Add skill to bullet
        add_request = {
            "skill_name": skill_name,
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": [target_bullet.id]
                }
            ]
        }

        add_response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=add_request
        )

        assert add_response.status_code == 201

        # Refresh bullet and verify
        db.refresh(target_bullet)

        assert target_bullet.tags is not None
        assert skill_name in target_bullet.tags

    def test_multiple_skill_additions_accumulate(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_experience: Experience
    ):
        """Test that multiple skill additions accumulate without overwriting"""
        skill_1 = "Docker"
        skill_2 = "Kubernetes"

        # Add first skill
        request_1 = {
            "skill_name": skill_1,
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": []
                }
            ]
        }

        response_1 = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_1
        )
        assert response_1.status_code == 201

        # Add second skill
        request_2 = {
            "skill_name": skill_2,
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": []
                }
            ]
        }

        response_2 = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request_2
        )
        assert response_2.status_code == 201

        # Refresh and verify both are present
        db.refresh(sample_experience)

        assert sample_experience.tools_and_technologies is not None
        assert skill_1 in sample_experience.tools_and_technologies
        assert skill_2 in sample_experience.tools_and_technologies

    def test_duplicate_skill_not_added_twice(
        self,
        db: Session,
        sample_job_profile: JobProfile,
        sample_experience: Experience
    ):
        """Test that adding the same skill twice doesn't create duplicates"""
        skill_name = "Python"

        # Add skill first time
        request = {
            "skill_name": skill_name,
            "user_id": sample_job_profile.user_id,
            "evidence_mappings": [
                {
                    "experience_id": sample_experience.id,
                    "engagement_id": None,
                    "bullet_ids": []
                }
            ]
        }

        response_1 = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request
        )
        assert response_1.status_code == 201

        # Add same skill second time
        response_2 = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/user-skills",
            json=request
        )
        assert response_2.status_code == 201

        # Refresh and verify no duplicates
        db.refresh(sample_experience)

        if sample_experience.tools_and_technologies:
            # Count occurrences - should be at most 1 (or 0 if already existed)
            count = sample_experience.tools_and_technologies.count(skill_name)
            assert count <= 1
