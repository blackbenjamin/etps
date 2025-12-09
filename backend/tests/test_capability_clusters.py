"""
Tests for Capability Clusters (Sprint 11)

Comprehensive tests for the capability cluster extraction, evidence mapping,
and API endpoints.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from db.models import JobProfile, User, Bullet, Experience
from db.database import get_db
from schemas.capability import (
    EvidenceSkill,
    ComponentSkill,
    CapabilityCluster,
    CapabilityClusterAnalysis,
    CapabilityClusterRequest,
    KeySkillSelection,
)
from services.capability_ontology import (
    CAPABILITY_ONTOLOGY,
    get_cluster_names,
    get_clusters_by_keywords,
    get_clusters_by_role_indicators,
    get_ontology_summary,
)
from services.capability_extractor import (
    compute_jd_cache_key,
    is_cache_valid,
    extract_capability_clusters,
    calculate_cluster_importance,
    _mock_extract_clusters,
)
from services.evidence_mapper import (
    extract_bullet_keywords,
    compute_keyword_overlap,
    map_bullets_to_cluster,
    calculate_overall_match_score,
    determine_recommendation,
    generate_positioning_strategy,
)


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
    """Create a dedicated test user (NOT User 1 which is real user data)."""
    # Check if test user already exists and reuse it
    existing = db.query(User).filter(User.username == "capability_test_user").first()
    if existing:
        return existing

    # Create fresh test user
    user = User(
        username="capability_test_user",
        email="capability_test@example.com",
        full_name="Capability Test User"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_job_profile(db: Session, sample_user: User) -> JobProfile:
    """Create a sample job profile for testing capability clusters."""
    job = JobProfile(
        user_id=sample_user.id,
        raw_jd_text="""
        AI & Emerging Technology Solutions Consultant

        We are seeking a strategic consultant with expertise in AI/ML, digital twins,
        and emerging technologies. The role requires strong consulting skills,
        client advisory experience, and technical leadership.

        Requirements:
        - 5+ years of experience in AI/ML or emerging technology consulting
        - Strong background in solution architecture
        - Experience with digital transformation initiatives
        - Excellent client communication skills
        - AWS or Azure cloud certification preferred
        """,
        job_title="AI & Emerging Technology Solutions Consultant",
        company_name="Test Corp",
        seniority="Senior",
        extracted_skills=["AI Strategy", "Machine Learning", "Digital Twins",
                         "Solution Architecture", "AWS", "Consulting"],
        must_have_capabilities=["5+ years AI/ML experience", "Client advisory"],
        nice_to_have_capabilities=["Cloud certification", "Digital transformation"]
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@pytest.fixture
def sample_bullets(db: Session, sample_user: User) -> list:
    """Create sample bullets for testing evidence mapping."""
    # First create an experience
    exp = Experience(
        user_id=sample_user.id,
        employer_name="Tech Corp",
        job_title="Senior AI Engineer",
        description="AI/ML development",
        start_date=datetime(2020, 1, 1),
        order=0
    )
    db.add(exp)
    db.commit()
    db.refresh(exp)

    bullets = [
        Bullet(
            user_id=sample_user.id,
            experience_id=exp.id,
            text="Led AI/ML strategy development for Fortune 500 client, resulting in $2M cost savings",
            tags=["AI Strategy", "Machine Learning", "Consulting"],
            retired=False
        ),
        Bullet(
            user_id=sample_user.id,
            experience_id=exp.id,
            text="Architected cloud-native solutions on AWS for enterprise clients",
            tags=["AWS", "Solution Architecture", "Cloud"],
            retired=False
        ),
        Bullet(
            user_id=sample_user.id,
            experience_id=exp.id,
            text="Developed digital twin prototypes for manufacturing optimization",
            tags=["Digital Twins", "Prototyping"],
            retired=False
        ),
    ]
    for bullet in bullets:
        db.add(bullet)
    db.commit()
    for bullet in bullets:
        db.refresh(bullet)
    return bullets


# =============================================================================
# ONTOLOGY TESTS
# =============================================================================

class TestCapabilityOntology:
    """Tests for the capability ontology."""

    def test_ontology_has_clusters(self):
        """Test that ontology contains clusters."""
        assert len(CAPABILITY_ONTOLOGY) >= 20

    def test_get_cluster_names(self):
        """Test retrieval of cluster names."""
        names = get_cluster_names()
        assert len(names) >= 20
        assert "AI & Data Strategy" in names
        assert "Solution Architecture" in names

    def test_cluster_structure(self):
        """Test that clusters have required fields."""
        for name, data in CAPABILITY_ONTOLOGY.items():
            assert "description" in data
            assert "component_skills" in data
            assert "evidence_keywords" in data
            assert len(data["component_skills"]) >= 1

    def test_get_clusters_by_keywords(self):
        """Test finding clusters by keywords."""
        matches = get_clusters_by_keywords(["AI", "machine learning", "strategy"])
        assert len(matches) > 0
        assert "AI & Data Strategy" in matches or "Machine Learning Engineering" in matches

    def test_get_clusters_by_role_indicators(self):
        """Test finding clusters by job title."""
        matches = get_clusters_by_role_indicators("AI Solutions Architect")
        assert len(matches) > 0

    def test_get_ontology_summary(self):
        """Test ontology summary generation."""
        summary = get_ontology_summary()
        assert len(summary) > 0
        assert "AI & Data Strategy" in summary


# =============================================================================
# CACHE TESTS
# =============================================================================

class TestCapabilityCache:
    """Tests for capability cluster caching."""

    def test_compute_jd_cache_key(self):
        """Test cache key computation."""
        key1 = compute_jd_cache_key("Test JD text", "Engineer")
        key2 = compute_jd_cache_key("Test JD text", "Engineer")
        key3 = compute_jd_cache_key("Different text", "Engineer")

        assert key1 == key2  # Same input = same key
        assert key1 != key3  # Different input = different key
        assert len(key1) == 64  # SHA256 hex length

    def test_cache_key_normalization(self):
        """Test that cache keys are normalized."""
        key1 = compute_jd_cache_key("Test  JD   text", "Engineer")
        key2 = compute_jd_cache_key("test jd text", "engineer")

        assert key1 == key2  # Should normalize to same key

    def test_is_cache_valid_none(self):
        """Test cache validation with None timestamp."""
        assert is_cache_valid(None) == False

    def test_is_cache_valid_recent(self):
        """Test cache validation with recent timestamp."""
        recent = datetime.utcnow() - timedelta(hours=1)
        assert is_cache_valid(recent) == True

    def test_is_cache_valid_expired(self):
        """Test cache validation with expired timestamp."""
        old = datetime.utcnow() - timedelta(hours=25)
        assert is_cache_valid(old) == False


# =============================================================================
# EXTRACTOR TESTS
# =============================================================================

class TestCapabilityExtractor:
    """Tests for capability cluster extraction."""

    @pytest.mark.asyncio
    async def test_mock_extract_clusters(self):
        """Test mock cluster extraction."""
        clusters = _mock_extract_clusters(
            jd_text="AI strategy consulting role requiring machine learning expertise",
            job_title="AI Strategy Consultant",
            extracted_skills=["AI Strategy", "Machine Learning", "Consulting"]
        )

        assert len(clusters) >= 4
        assert all(isinstance(c, CapabilityCluster) for c in clusters)

    @pytest.mark.asyncio
    async def test_extract_capability_clusters_mock(self):
        """Test cluster extraction with mock mode."""
        clusters = await extract_capability_clusters(
            jd_text="Senior software engineer with cloud architecture experience",
            job_title="Senior Software Engineer",
            extracted_skills=["AWS", "Python", "Architecture"],
            use_mock=True
        )

        assert len(clusters) >= 4
        for cluster in clusters:
            assert cluster.name
            assert cluster.description
            assert cluster.importance in ["critical", "important", "nice-to-have"]

    def test_calculate_cluster_importance(self):
        """Test cluster importance calculation."""
        cluster = CapabilityCluster(
            name="Test Cluster",
            description="Test description",
            component_skills=[
                ComponentSkill(name="Python", required=True),
                ComponentSkill(name="Machine Learning", required=True),
            ],
            importance="important"
        )

        jd_text = "Required: Python programming experience. Must have ML expertise."
        must_have = ["Python", "Machine Learning"]
        nice_to_have = ["AWS"]

        importance = calculate_cluster_importance(cluster, jd_text, must_have, nice_to_have)
        assert importance in ["critical", "important", "nice-to-have"]


# =============================================================================
# EVIDENCE MAPPER TESTS
# =============================================================================

class TestEvidenceMapper:
    """Tests for evidence mapping functionality."""

    def test_extract_bullet_keywords(self, sample_bullets, db):
        """Test keyword extraction from bullets."""
        bullet = sample_bullets[0]
        keywords = extract_bullet_keywords(bullet)

        assert "ai" in keywords or "ai strategy" in keywords
        assert len(keywords) > 0

    def test_compute_keyword_overlap_full_match(self):
        """Test keyword overlap with full match."""
        cluster_keywords = {"python", "machine learning", "aws"}
        bullet_keywords = {"python", "machine learning", "aws", "extra"}

        overlap = compute_keyword_overlap(cluster_keywords, bullet_keywords)
        assert overlap >= 0.9  # Should be high

    def test_compute_keyword_overlap_partial_match(self):
        """Test keyword overlap with partial match."""
        cluster_keywords = {"python", "machine learning", "aws"}
        bullet_keywords = {"python", "java"}

        overlap = compute_keyword_overlap(cluster_keywords, bullet_keywords)
        assert 0.0 < overlap < 1.0  # Partial match

    def test_compute_keyword_overlap_no_match(self):
        """Test keyword overlap with no match."""
        cluster_keywords = {"python", "machine learning"}
        bullet_keywords = {"java", "spring"}

        overlap = compute_keyword_overlap(cluster_keywords, bullet_keywords)
        assert overlap < 0.3

    def test_compute_keyword_overlap_empty(self):
        """Test keyword overlap with empty sets."""
        assert compute_keyword_overlap(set(), {"python"}) == 0.0
        assert compute_keyword_overlap({"python"}, set()) == 0.0

    def test_calculate_overall_match_score(self):
        """Test overall match score calculation."""
        clusters = [
            CapabilityCluster(
                name="AI Strategy",
                description="Test",
                importance="critical",
                match_percentage=80.0,
                component_skills=[]
            ),
            CapabilityCluster(
                name="Leadership",
                description="Test",
                importance="important",
                match_percentage=60.0,
                component_skills=[]
            ),
        ]

        score = calculate_overall_match_score(clusters)
        assert 0 <= score <= 100

    def test_calculate_overall_match_score_empty(self):
        """Test overall match score with empty clusters."""
        assert calculate_overall_match_score([]) == 0.0

    def test_determine_recommendation_strong(self):
        """Test recommendation for strong match."""
        rec = determine_recommendation(75.0, 0)
        assert rec == "strong_match"

    def test_determine_recommendation_moderate(self):
        """Test recommendation for moderate match."""
        rec = determine_recommendation(55.0, 1)
        assert rec == "moderate_match"

    def test_determine_recommendation_weak(self):
        """Test recommendation for weak match."""
        rec = determine_recommendation(20.0, 3)
        assert rec == "weak_match"

    def test_generate_positioning_strategy_no_gaps(self):
        """Test positioning strategy with no gaps."""
        cluster = CapabilityCluster(
            name="AI Strategy",
            description="Test",
            importance="critical",
            component_skills=[]
        )

        strategy = generate_positioning_strategy(cluster, [], 5)
        assert "Strong alignment" in strategy or "Lead with" in strategy

    def test_generate_positioning_strategy_with_gaps(self):
        """Test positioning strategy with gaps."""
        cluster = CapabilityCluster(
            name="AI Strategy",
            description="Test",
            importance="critical",
            component_skills=[]
        )

        strategy = generate_positioning_strategy(cluster, ["Python", "ML"], 2)
        assert len(strategy) > 0


# =============================================================================
# SCHEMA TESTS
# =============================================================================

class TestCapabilitySchemas:
    """Tests for capability Pydantic schemas."""

    def test_evidence_skill_creation(self):
        """Test EvidenceSkill schema."""
        skill = EvidenceSkill(name="Python", category="tech")
        assert skill.name == "Python"
        assert skill.matched == False
        assert skill.confidence == 0.0

    def test_component_skill_creation(self):
        """Test ComponentSkill schema."""
        skill = ComponentSkill(
            name="AI Strategy",
            required=True,
            evidence_skills=[
                EvidenceSkill(name="TensorFlow", category="tech")
            ]
        )
        assert skill.name == "AI Strategy"
        assert skill.required == True
        assert len(skill.evidence_skills) == 1

    def test_capability_cluster_creation(self):
        """Test CapabilityCluster schema."""
        cluster = CapabilityCluster(
            name="AI & Data Strategy",
            description="Strategic AI leadership",
            importance="critical",
            component_skills=[
                ComponentSkill(name="Roadmap creation", required=True)
            ],
            match_percentage=75.0,
            gaps=["Digital Twins"]
        )
        assert cluster.name == "AI & Data Strategy"
        assert cluster.importance == "critical"
        assert cluster.match_percentage == 75.0

    def test_capability_cluster_analysis_creation(self):
        """Test CapabilityClusterAnalysis schema."""
        analysis = CapabilityClusterAnalysis(
            job_profile_id=1,
            user_id=1,
            clusters=[
                CapabilityCluster(
                    name="AI Strategy",
                    description="Test",
                    importance="critical",
                    component_skills=[]
                )
            ],
            overall_match_score=72.5,
            recommendation="strong_match",
            positioning_summary="Lead with AI experience",
            key_strengths=["AI Strategy"],
            critical_gaps=["Digital Twins"]
        )
        assert analysis.overall_match_score == 72.5
        assert analysis.recommendation == "strong_match"
        assert len(analysis.clusters) == 1


# =============================================================================
# API ENDPOINT TESTS
# =============================================================================

class TestCapabilityAPI:
    """Tests for capability cluster API endpoints."""

    def test_get_capability_clusters(self, db: Session, sample_job_profile: JobProfile, sample_bullets):
        """Test GET /capability/job-profiles/{id}/clusters endpoint."""
        response = client.get(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/clusters?user_id=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "cached" in data
        analysis = data["analysis"]
        assert "clusters" in analysis
        assert "overall_match_score" in analysis

    def test_get_capability_clusters_not_found(self, db: Session):
        """Test GET clusters for non-existent job profile."""
        response = client.get("/api/v1/capability/job-profiles/99999/clusters?user_id=1")
        assert response.status_code == 404

    def test_analyze_capability_clusters(self, db: Session, sample_job_profile: JobProfile, sample_bullets):
        """Test POST /capability/job-profiles/{id}/clusters/analyze endpoint."""
        response = client.post(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/clusters/analyze",
            json={
                "job_profile_id": sample_job_profile.id,
                "user_id": 1,
                "force_refresh": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cached"] == False  # Force refresh = not cached

    def test_update_cluster_selections(self, db: Session, sample_job_profile: JobProfile):
        """Test PUT /capability/job-profiles/{id}/clusters/selections endpoint."""
        response = client.put(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/clusters/selections",
            json={
                "job_profile_id": sample_job_profile.id,
                "key_skills": [
                    {"cluster_name": "AI Strategy", "skill_name": "Roadmap creation", "selected": True},
                    {"cluster_name": "Solution Architecture", "skill_name": "System design", "selected": True}
                ],
                "cluster_expansions": {
                    "AI Strategy": True,
                    "Solution Architecture": False
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_profile_id" in data
        assert "updated_at" in data

    def test_get_combined_analysis(self, db: Session, sample_job_profile: JobProfile, sample_bullets):
        """Test GET /capability/job-profiles/{id}/combined-analysis endpoint."""
        response = client.get(
            f"/api/v1/capability/job-profiles/{sample_job_profile.id}/combined-analysis?user_id=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert "flat_analysis" in data
        assert "cluster_analysis" in data
        assert "merged_score" in data
        assert 0 <= data["merged_score"] <= 100


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestJDOnlyExtraction:
    """Tests verifying that cluster extraction is based on JD text only, not user's extracted_skills.

    This test class validates the JD-first cluster extraction architecture requirement:
    - Clusters should be determined from JD content and job title only
    - User's background (extracted_skills) should NOT influence cluster results
    """

    def test_extracted_skills_ignored(self):
        """Verify that extracted_skills parameter does NOT affect cluster results.

        This test calls extract_capability_clusters twice with the same JD but different
        extracted_skills and verifies that the results are identical.
        """
        jd_text = """
        Data Governance & Compliance Officer

        We are seeking an experienced Data Governance Officer to establish and maintain
        our data governance framework. This role focuses on data quality, regulatory
        compliance (GDPR, CCPA), data lineage tracking, and metadata management.

        Key Responsibilities:
        - Design and implement data governance policies
        - Ensure regulatory compliance across data systems
        - Manage data quality standards
        - Establish data lineage and metadata practices
        - Conduct data audits and risk assessments

        Requirements:
        - 5+ years in data governance
        - Strong knowledge of data regulations (GDPR, CCPA, HIPAA)
        - Experience with metadata management tools
        - Data stewardship background
        """

        job_title = "Data Governance & Compliance Officer"

        # Extract clusters with no extracted_skills
        clusters_no_skills = _mock_extract_clusters(
            jd_text=jd_text,
            job_title=job_title,
            extracted_skills=None
        )

        # Extract clusters with extracted_skills that should NOT influence result
        # These are unrelated to Data Governance
        clusters_with_ai_skills = _mock_extract_clusters(
            jd_text=jd_text,
            job_title=job_title,
            extracted_skills=["AI Strategy", "Machine Learning", "Deep Learning", "TensorFlow"]
        )

        # Extract cluster names for comparison
        names_no_skills = {c.name for c in clusters_no_skills}
        names_with_ai_skills = {c.name for c in clusters_with_ai_skills}

        # Verify they are identical - extracted_skills should not change results
        assert names_no_skills == names_with_ai_skills, (
            f"Cluster names differ based on extracted_skills!\n"
            f"Without skills: {names_no_skills}\n"
            f"With AI skills: {names_with_ai_skills}\n"
            f"This proves the bug: extracted_skills is influencing cluster selection."
        )

        # Verify Data Governance cluster IS in results (should match JD)
        assert "Data Governance & Compliance" in names_no_skills, (
            "Data Governance & Compliance should be in results based on JD content"
        )

        # Verify AI & Data Strategy is NOT in results
        # (despite being in extracted_skills, it shouldn't appear based on JD content)
        assert "AI & Data Strategy" not in names_no_skills, (
            "AI & Data Strategy should NOT be in results (not mentioned in JD)"
        )

    def test_no_hallucination_from_user_profile(self):
        """Verify user's background doesn't influence cluster extraction.

        This test verifies that even though extracted_skills contains ML-related
        technologies, those clusters are NOT extracted from a Program Manager JD.
        """
        jd_text = """
        Program Manager - Supply Chain

        Lead program management for our supply chain transformation initiatives.
        Responsibilities include managing complex projects, coordinating across
        stakeholders, and ensuring timeline and budget compliance.

        Requirements:
        - 3+ years program/project management experience
        - Strong stakeholder coordination skills
        - Agile and Waterfall methodology experience
        - Budget and resource management
        - Risk management expertise

        Supply Chain Focus:
        - Supply chain optimization projects
        - Logistics process improvement
        - Vendor management coordination
        """

        job_title = "Program Manager - Supply Chain"

        # Call with extracted_skills containing ML tech that should NOT appear
        clusters = _mock_extract_clusters(
            jd_text=jd_text,
            job_title=job_title,
            extracted_skills=["TensorFlow", "PyTorch", "ML Engineering", "Deep Learning", "Computer Vision"]
        )

        cluster_names = {c.name for c in clusters}

        # Verify Program Management IS in results (matches JD)
        assert "Program & Project Management" in cluster_names, (
            "Program & Project Management should be in results based on JD"
        )

        # Verify ML-related clusters are NOT in results (despite being in extracted_skills)
        assert "Machine Learning Engineering" not in cluster_names, (
            "Machine Learning Engineering should NOT be extracted from Supply Chain PM JD\n"
            "This proves the bug: extracted_skills is influencing cluster selection."
        )

        # Verify AI & Data Strategy is NOT in results
        assert "AI & Data Strategy" not in cluster_names, (
            "AI & Data Strategy should NOT be extracted from Supply Chain PM JD"
        )

    def test_mock_extractor_jd_only(self):
        """Verify _mock_extract_clusters uses only JD text and title, not extracted_skills.

        This is the most direct test: call the mock extractor with a healthcare JD
        but with blockchain-related extracted_skills. Verify that blockchain clusters
        do NOT appear, proving extraction is JD-only.
        """
        jd_text = """
        Healthcare IT Consultant

        We seek an experienced consultant for our EHR implementation project.
        This role requires deep healthcare IT experience, understanding of HIPAA
        compliance, and expertise with electronic health record systems.

        Key Requirements:
        - 7+ years healthcare IT experience
        - EHR system implementation knowledge
        - HIPAA compliance understanding
        - Clinical workflow optimization
        - Healthcare data management
        - Experience with major EHR platforms (Epic, Cerner, Athena)
        """

        job_title = "Healthcare IT Consultant"

        # Extract skills contains blockchain/crypto - completely unrelated to healthcare
        clusters = _mock_extract_clusters(
            jd_text=jd_text,
            job_title=job_title,
            extracted_skills=["Blockchain", "Cryptocurrency", "NFT", "Smart Contracts", "Web3"]
        )

        cluster_names = {c.name for c in clusters}

        # Verify Healthcare IS in results (matches JD content)
        assert "Healthcare & Life Sciences Domain" in cluster_names, (
            "Healthcare & Life Sciences Domain should be extracted based on JD keywords"
        )

        # Verify blockchain/crypto clusters are NOT in results
        # (they're not in the ontology but the point is: no crypto-related extraction)
        blockchain_related = ["Blockchain", "Cryptocurrency", "Web3", "Emerging Technologies"]
        for cluster_name in cluster_names:
            assert "blockchain" not in cluster_name.lower(), (
                f"Blockchain-related cluster '{cluster_name}' should NOT appear in healthcare JD\n"
                f"This proves the bug: extracted_skills is influencing extraction."
            )
            assert "crypto" not in cluster_name.lower(), (
                f"Crypto-related cluster should NOT appear in healthcare JD"
            )


class TestCapabilityIntegration:
    """Integration tests for capability cluster workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, db: Session, sample_job_profile: JobProfile, sample_bullets):
        """Test complete capability analysis workflow."""
        from services.skill_gap import get_cluster_analysis

        # Get cluster analysis
        analysis = await get_cluster_analysis(
            job_profile_id=sample_job_profile.id,
            user_id=1,
            db=db,
            use_mock=True
        )

        assert analysis is not None
        assert len(analysis.clusters) >= 4
        assert 0 <= analysis.overall_match_score <= 100
        assert analysis.recommendation in ["strong_match", "moderate_match", "stretch_role", "weak_match"]

    @pytest.mark.asyncio
    async def test_combined_analysis_integration(self, db: Session, sample_job_profile: JobProfile, sample_bullets):
        """Test combined flat + cluster analysis."""
        from services.skill_gap import get_combined_analysis, merge_analysis_scores

        flat_analysis, cluster_analysis = await get_combined_analysis(
            job_profile_id=sample_job_profile.id,
            user_id=1,
            db=db,
            use_mock_clusters=True
        )

        assert flat_analysis is not None
        assert cluster_analysis is not None

        # Test score merging
        merged = merge_analysis_scores(flat_analysis, cluster_analysis)
        assert 0 <= merged <= 100
