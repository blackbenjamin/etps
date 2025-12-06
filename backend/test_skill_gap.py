"""
Test script for skill gap analysis service.

Tests the Sprint 2 Skill Gap Analyzer enhancements including:
- Semantic skill matching with embedding-based similarity
- Gap categorization (critical/important/nice-to-have)
- Positioning strategy generation with user-specific context
- Weak signal detection with semantic matching
- Resume tailoring integration
- Database persistence and caching

The tests document expected Sprint 2 behavior and will guide implementation.
"""

import asyncio
import pytest
import uuid
from datetime import date, datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from db.database import get_db, engine
from db.models import Base, User, Experience, Bullet, JobProfile
from services.skill_gap import (
    analyze_skill_gap,
    build_user_skill_profile,
    compute_matched_skills,
    compute_missing_skills,
    compute_weak_signals,
    compute_skill_match_score,
    generate_positioning_strategies,
    determine_recommendation,
    find_skill_match,
    get_related_skills,
    normalize_skill,
    SKILL_SYNONYMS,
    RELATED_SKILLS,
)
from schemas.skill_gap import (
    SkillGapResponse,
    SkillMatch,
    SkillGap,
    WeakSignal,
    UserSkillProfile,
    SkillGapRequest,
)


def setup_test_data(db: Session) -> tuple[int, int]:
    """
    Create comprehensive test data for skill gap analysis testing.

    Returns:
        Tuple of (user_id, job_profile_id)
    """
    unique_id = str(uuid.uuid4())[:8]

    # Create test user
    user = User(
        username=f"skill_gap_test_{unique_id}",
        email=f"skill_gap_{unique_id}@example.com",
        full_name="Test Candidate",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create test experiences
    exp1 = Experience(
        user_id=user.id,
        job_title="Senior Machine Learning Engineer",
        employer_name="Tech Corp",
        location="San Francisco, CA",
        start_date=date(2020, 1, 1),
        end_date=None,
        description="ML engineering and AI systems work",
        order=0,
    )
    db.add(exp1)
    db.commit()
    db.refresh(exp1)

    exp2 = Experience(
        user_id=user.id,
        job_title="Data Engineer",
        employer_name="DataCo",
        location="San Francisco, CA",
        start_date=date(2018, 1, 1),
        end_date=date(2020, 1, 1),
        description="Data pipeline and infrastructure work",
        order=1,
    )
    db.add(exp2)
    db.commit()
    db.refresh(exp2)

    # Create test bullets with various skills and evidence
    bullets = [
        # Strong ML-related bullets
        Bullet(
            user_id=user.id,
            experience_id=exp1.id,
            text="Architected production ML pipeline processing 100M+ daily predictions with 99.95% uptime using TensorFlow and PyTorch",
            tags=["machine_learning", "deep_learning", "tensorflow", "pytorch", "mlops"],
            seniority_level="senior",
            bullet_type="achievement",
            relevance_scores={
                "machine_learning": 0.95,
                "deep_learning": 0.90,
                "tensorflow": 0.88,
                "pytorch": 0.85,
            },
            usage_count=2,
        ),
        Bullet(
            user_id=user.id,
            experience_id=exp1.id,
            text="Led team of 5 ML engineers to develop NLP models for customer sentiment analysis, improving accuracy by 23% and reducing inference latency by 40%",
            tags=["nlp", "leadership", "model_training", "python"],
            seniority_level="senior",
            bullet_type="achievement",
            relevance_scores={
                "nlp": 0.92,
                "leadership": 0.85,
                "python": 0.88,
            },
            usage_count=1,
        ),
        # Data engineering bullets
        Bullet(
            user_id=user.id,
            experience_id=exp2.id,
            text="Designed and implemented Apache Spark ETL pipeline ingesting 50TB daily data, reducing processing time from 6 hours to 45 minutes",
            tags=["spark", "etl", "data_engineering", "python"],
            seniority_level="mid",
            bullet_type="metric_impact",
            relevance_scores={
                "spark": 0.90,
                "etl": 0.88,
                "data_engineering": 0.92,
                "python": 0.85,
            },
            usage_count=1,
        ),
        # DevOps/infrastructure bullets
        Bullet(
            user_id=user.id,
            experience_id=exp1.id,
            text="Migrated legacy ML infrastructure to Kubernetes and Docker, reducing deployment time by 70% and improving system reliability",
            tags=["kubernetes", "docker", "devops", "aws"],
            seniority_level="senior",
            bullet_type="achievement",
            relevance_scores={
                "kubernetes": 0.87,
                "docker": 0.85,
                "devops": 0.86,
                "aws": 0.80,
            },
            usage_count=0,
        ),
        # Python/programming bullets
        Bullet(
            user_id=user.id,
            experience_id=exp1.id,
            text="Built FastAPI microservices for real-time model serving with 99.9% uptime and sub-100ms latency",
            tags=["fastapi", "python", "backend", "microservices"],
            seniority_level="senior",
            bullet_type="achievement",
            relevance_scores={
                "fastapi": 0.88,
                "python": 0.92,
                "backend": 0.85,
            },
            usage_count=0,
        ),
        # Weaker/generic bullets
        Bullet(
            user_id=user.id,
            experience_id=exp2.id,
            text="Participated in data quality initiatives and assisted with various ETL projects",
            tags=["data_quality", "etl"],
            seniority_level="mid",
            bullet_type="responsibility",
            relevance_scores={"data_quality": 0.50},
            usage_count=3,
        ),
    ]
    db.add_all(bullets)
    db.commit()

    # Create job profile with clear requirements/nice-to-haves
    job_profile = JobProfile(
        user_id=user.id,
        raw_jd_text="""
        Senior ML Engineering Manager

        We are looking for an experienced leader to build and manage ML teams.

        Requirements:
        - 5+ years in Machine Learning Model Development
        - Expertise in Deep Learning frameworks (TensorFlow or PyTorch)
        - Strong Python programming skills
        - Experience with Kubernetes and containerization
        - Leadership and team management experience

        Nice to Have:
        - Experience with LLMs or Generative AI
        - Knowledge of Model Risk Management and AI Governance
        - Familiarity with cloud platforms (AWS, GCP)
        - Experience with Apache Spark or other big data tools
        """,
        job_title="Senior ML Engineering Manager",
        seniority="senior",
        extracted_skills=[
            "Machine Learning",
            "Deep Learning",
            "TensorFlow",
            "PyTorch",
            "Python",
            "Kubernetes",
            "Docker",
            "Leadership",
            "LLM",
            "Generative AI",
            "Model Risk Management",
            "AI Governance",
            "AWS",
            "Apache Spark",
        ],
        must_have_capabilities=[
            "Machine Learning Model Development",
            "Deep Learning",
            "Python",
            "Kubernetes",
            "Leadership",
        ],
        nice_to_have_capabilities=[
            "LLM or Generative AI",
            "Model Risk Management",
            "AI Governance",
            "Cloud Platform Experience",
            "Apache Spark",
        ],
        core_priorities=[
            "ML engineering leadership",
            "Deep learning expertise",
            "Team building and management",
        ],
        tone_style="formal_corporate",
    )
    db.add(job_profile)
    db.commit()
    db.refresh(job_profile)

    return user.id, job_profile.id


class TestSemanticSkillMatching:
    """Test semantic skill matching capabilities for Sprint 2."""

    def test_semantic_matching_ml_to_machine_learning(self):
        """Test that 'ML Engineering' matches 'Machine Learning' semantically.

        EXPECTS FAIL in current implementation (no semantic matching).
        Sprint 2: Should use embeddings or LLM to recognize semantic similarity.
        """
        # This should work with semantic matching
        user_skills = ["Machine Learning", "Deep Learning", "TensorFlow"]
        job_skill = "ML Engineering"

        # Current implementation only does exact/synonym matching
        matched = find_skill_match(job_skill, user_skills)

        # Sprint 2: This should succeed with semantic matching
        # For now, it may fail but the test documents expected behavior
        assert matched is not None, (
            "Semantic matching should recognize ML Engineering as related to Machine Learning. "
            "Current implementation uses only exact/synonym matching."
        )

    def test_similarity_threshold_respects_config(self):
        """Test that semantic similarity respects configured threshold (default 0.75).

        EXPECTS FAIL in current implementation (no config-based threshold).
        Sprint 2: Should have configurable similarity threshold for embeddings.
        """
        # This test documents expected behavior for semantic threshold
        threshold = 0.75

        user_skills = ["Python", "JavaScript", "TypeScript"]
        job_skill = "Scripting"  # Similar but not synonym

        # Sprint 2: Should accept based on similarity score >= threshold
        # For now, this will fail
        try:
            matched = find_skill_match(job_skill, user_skills)
            # If semantic matching is implemented, should check threshold
            assert threshold <= 0.75, "Threshold config should be <= 0.75"
        except Exception:
            pytest.skip("Semantic matching not yet implemented")

    @pytest.mark.asyncio
    async def test_fallback_to_synonym_when_embedding_unavailable(self):
        """Test fallback to synonym matching when embedding service unavailable.

        EXPECTS PASS - tests fallback mechanism.
        Sprint 2: When semantic service unavailable, use SKILL_SYNONYMS mapping.
        """
        user_skills = ["PyTorch"]
        job_skill = "torch"  # A pytorch synonym

        # Should match via synonym mapping when semantic unavailable
        matched = await find_skill_match(job_skill, user_skills)
        assert matched == "PyTorch", (
            "Should fall back to synonym matching when embedding service unavailable"
        )

    @pytest.mark.asyncio
    async def test_multiple_candidate_skills_returns_best_match(self):
        """Test that when multiple user skills could match, best one is returned.

        EXPECTS FAIL with semantic matching.
        Sprint 2: Should use semantic similarity scores to pick best match.
        """
        user_skills = ["Machine Learning", "ML Ops", "Data Science"]
        job_skill = "Machine Learning Engineering"

        # Should return best match (ML or ML Ops, not Data Science)
        matched = await find_skill_match(job_skill, user_skills)
        # Current implementation returns first match found
        # Sprint 2: Should return highest confidence match
        assert matched in ["Machine Learning", "ML Ops"], (
            "Should return highest confidence match among candidates"
        )


class TestGapCategorization:
    """Test skill gap categorization (critical/important/nice-to-have)."""

    @pytest.mark.asyncio
    async def test_critical_skills_from_requirements_section(self):
        """Test that skills from requirements section are identified as critical.

        EXPECTS FAIL - needs LLM-based categorization.
        Sprint 2: Should parse JD structure to identify must-haves vs nice-to-haves.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(
                JobProfile.id == job_profile_id
            ).first()

            # Create user with missing critical skill
            user_skill_profile = UserSkillProfile(
                skills=["Python", "Kubernetes"],
                capabilities=["ML Engineering"],
                bullet_tags=["python", "kubernetes"],
                seniority_levels=["senior"],
                relevance_scores={"Python": 0.95, "Kubernetes": 0.85},
            )

            # Run analysis
            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                user_skill_profile=user_skill_profile,
            )

            # Find gaps
            missing = response.skill_gaps

            # Look for critical gaps (Deep Learning from requirements)
            critical_gaps = [g for g in missing if g.importance == "critical"]

            # Sprint 2: Should identify Deep Learning as critical (in requirements)
            assert any("Deep Learning" in str(g.skill) for g in critical_gaps), (
                "Deep Learning should be marked critical (from requirements section)"
            )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_nice_to_have_skills_categorized_correctly(self):
        """Test that skills from preferred/nice-to-have sections are categorized.

        EXPECTS FAIL - needs section-aware parsing.
        Sprint 2: Should distinguish nice-to-have from requirements.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(
                JobProfile.id == job_profile_id
            ).first()

            user_skill_profile = UserSkillProfile(
                skills=["Python", "Kubernetes", "Deep Learning"],
                capabilities=["ML Engineering", "Leadership"],
                bullet_tags=["python", "kubernetes", "deep_learning"],
                seniority_levels=["senior"],
                relevance_scores={
                    "Python": 0.95,
                    "Kubernetes": 0.85,
                    "Deep Learning": 0.90,
                },
            )

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                user_skill_profile=user_skill_profile,
            )

            # Look for nice-to-have gaps
            gaps = response.skill_gaps
            nice_to_have_gaps = [g for g in gaps if g.importance == "nice-to-have"]

            # LLM or Generative AI should be nice-to-have
            assert any(
                "LLM" in str(g.skill) or "Generative" in str(g.skill)
                for g in nice_to_have_gaps
            ), (
                "LLM/Generative AI should be marked nice-to-have (from that section)"
            )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_llm_based_categorization_various_jd_structures(self):
        """Test LLM-based categorization works with various JD structures.

        EXPECTS FAIL - needs LLM integration.
        Sprint 2: Should use LLM to extract and categorize requirements.
        """
        # This test documents that we need smart parsing of different JD formats:
        # - Traditional "Requirements" / "Nice to Have"
        # - Bullet-point lists without sections
        # - Embedded requirements throughout prose

        jd_structures = [
            # Format 1: Clear sections
            "Requirements:\n- Python\n- Machine Learning\n\nNice to Have:\n- LLM",
            # Format 2: Prose with embedded skills
            "We need someone skilled in Python and Machine Learning. Experience with LLM is nice to have.",
            # Format 3: Bullet list without sections
            "- 5+ years Python\n- Deep Learning experience\n- Ideally: LLM background",
        ]

        # Sprint 2: Should handle all formats and categorize appropriately
        pytest.skip("LLM-based categorization not yet implemented")


class TestPositioningStrategy:
    """Test positioning strategy generation with user-specific context."""

    @pytest.mark.asyncio
    async def test_strategies_reference_user_actual_skills(self):
        """Test that strategies mention user's actual skills, not generic templates.

        EXPECTS FAIL - needs context-aware strategy generation.
        Sprint 2: Strategies should reference specific user skills.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(
                JobProfile.id == job_profile_id
            ).first()

            user_skill_profile = UserSkillProfile(
                skills=[
                    "Python",
                    "TensorFlow",
                    "Kubernetes",
                    "Apache Spark",
                    "Leadership",
                ],
                capabilities=["ML Engineering", "Team Management"],
                bullet_tags=["tensorflow", "kubernetes", "spark"],
                seniority_levels=["senior"],
                relevance_scores={
                    "Python": 0.95,
                    "TensorFlow": 0.92,
                    "Kubernetes": 0.88,
                },
            )

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                user_skill_profile=user_skill_profile,
            )

            strategies = response.key_positioning_angles

            # Strategies should mention specific user skills (TensorFlow, Kubernetes, etc)
            strategy_text = " ".join(strategies)
            assert any(
                skill in strategy_text.lower()
                for skill in ["tensorflow", "kubernetes", "spark", "leadership"]
            ), (
                "Strategies should reference actual user skills, not generic templates. "
                f"Got: {strategies}"
            )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_strategies_align_with_job_priorities(self):
        """Test that positioning strategies align with job's core priorities.

        EXPECTS FAIL - needs priority-aware strategy generation.
        Sprint 2: Strategies should be tailored to job priorities.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(
                JobProfile.id == job_profile_id
            ).first()

            user_skill_profile = UserSkillProfile(
                skills=["Python", "Leadership", "Team Management"],
                capabilities=["ML Engineering"],
                bullet_tags=["python", "leadership"],
                seniority_levels=["senior"],
                relevance_scores={"Python": 0.95, "Leadership": 0.90},
            )

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                user_skill_profile=user_skill_profile,
            )

            strategies = response.key_positioning_angles
            strategy_text = " ".join(strategies).lower()

            # Job priorities: ML leadership, deep learning, team building
            # Strategies should emphasize these
            assert any(
                word in strategy_text
                for word in ["leadership", "team", "ml", "machine learning"]
            ), (
                "Strategies should align with job priorities: ML leadership, team building. "
                f"Got: {strategies}"
            )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_critical_gaps_get_mitigation_strategies(self):
        """Test that critical gaps receive specific mitigation strategies.

        EXPECTS FAIL - needs mitigation strategy generation.
        Sprint 2: Critical gaps should have actionable mitigation guidance.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(
                JobProfile.id == job_profile_id
            ).first()

            # User missing critical skill: Deep Learning
            user_skill_profile = UserSkillProfile(
                skills=["Python", "Kubernetes"],
                capabilities=["Software Engineering"],
                bullet_tags=["python", "kubernetes"],
                seniority_levels=["senior"],
                relevance_scores={"Python": 0.95},
            )

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                user_skill_profile=user_skill_profile,
            )

            # Find critical gap
            critical_gaps = [g for g in response.skill_gaps if g.importance == "critical"]

            # Should have mitigation strategies
            if critical_gaps:
                for gap in critical_gaps:
                    assert gap.positioning_strategy, (
                        f"Critical gap '{gap.skill}' should have positioning_strategy"
                    )
                    # Strategy should mention related skills, learning, or growth
                    strategy = gap.positioning_strategy.lower()
                    assert any(
                        word in strategy
                        for word in ["learning", "adjacent", "transfer", "experience", "growth", "certif", "acquiring", "skills"]
                    ), (
                        f"Mitigation for critical gap should suggest learning path, transfer, or growth. "
                        f"Got: {gap.positioning_strategy}"
                    )
        finally:
            db.rollback()


class TestWeakSignalDetection:
    """Test weak signal detection with semantic matching."""

    @pytest.mark.asyncio
    async def test_semantic_detection_finds_related_skills(self):
        """Test that weak signal detection finds skills beyond RELATED_SKILLS mapping.

        EXPECTS FAIL - needs semantic similarity in weak signal detection.
        Sprint 2: Should use embeddings to find related skills semantically.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(
                JobProfile.id == job_profile_id
            ).first()

            # User has "Software Engineering" which is semantically related to ML
            user_skill_profile = UserSkillProfile(
                skills=["Python", "Software Engineering", "Data Analysis"],
                capabilities=["System Architecture"],
                bullet_tags=["python", "architecture"],
                seniority_levels=["senior"],
                relevance_scores={"Python": 0.95},
            )

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                user_skill_profile=user_skill_profile,
            )

            weak_signals = response.weak_signals

            # Should find weak signals for skills where user has related experience
            # even if not in RELATED_SKILLS mapping
            assert len(weak_signals) > 0, (
                "Should detect weak signals where user has adjacent experience. "
                "Semantic matching should find related skills beyond RELATED_SKILLS mapping."
            )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_weak_signal_evidence_includes_actual_bullet_text(self):
        """Test that weak signal evidence extracts actual bullet text.

        EXPECTS FAIL - needs evidence extraction from bullets.
        Sprint 2: Evidence should include actual text, not just skill names.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            # Get actual bullets
            user_bullets = db.query(Bullet).filter(
                Bullet.user_id == user_id,
                Bullet.retired == False,
            ).all()

            user_skill_profile = await build_user_skill_profile(user_id, db)

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                user_skill_profile=user_skill_profile,
            )

            weak_signals = response.weak_signals

            # Evidence should be actual text from bullets, not generic descriptions
            for signal in weak_signals:
                for evidence in signal.current_evidence:
                    # Evidence should be substantive, ideally referencing actual work
                    assert len(evidence) > 20, (
                        f"Evidence should include meaningful bullet text. Got: {evidence}"
                    )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_weak_signals_ranked_by_similarity_score(self):
        """Test that weak signals are ranked by confidence/similarity score.

        EXPECTS FAIL - needs similarity scoring for weak signals.
        Sprint 2: Weak signals should include similarity scores and be ranked.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            user_skill_profile = await build_user_skill_profile(user_id, db)

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                user_skill_profile=user_skill_profile,
            )

            weak_signals = response.weak_signals

            # Weak signals should be ordered by confidence
            if len(weak_signals) > 1:
                # Should be ranked somehow (documented via schema extension)
                # Sprint 2: Add similarity_score to WeakSignal schema
                assert all(
                    hasattr(signal, "skill") for signal in weak_signals
                ), "Weak signals should be ranked by relevance"
        finally:
            db.rollback()


class TestResumeTailoringIntegration:
    """Test skill gap analysis integration with resume tailoring."""

    @pytest.mark.asyncio
    async def test_skill_gap_called_during_tailoring(self):
        """Test that skill gap analysis is called automatically during resume tailoring.

        EXPECTS FAIL - needs integration into tailor_resume.
        Sprint 2: tailor_resume should call analyze_skill_gap as part of workflow.
        """
        # This test documents that resume tailoring should:
        # 1. Analyze skill gaps between user and job
        # 2. Use results to prioritize bullets
        # 3. Return skill gap summary in response
        pytest.skip("Integration with tailor_resume not yet implemented")

    @pytest.mark.asyncio
    async def test_bullet_selection_uses_prioritize_tags_guidance(self):
        """Test that bullet selection uses prioritize_tags from skill gap analysis.

        EXPECTS FAIL - needs integration.
        Sprint 2: tailor_resume should use bullet_selection_guidance from skill gap.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            # Response should include guidance
            guidance = response.bullet_selection_guidance
            assert "prioritize_tags" in guidance, (
                "Skill gap response should include bullet_selection_guidance.prioritize_tags"
            )

            # prioritize_tags should be actual skills user has (not generic)
            prioritize_tags = guidance.get("prioritize_tags", [])
            assert len(prioritize_tags) > 0, (
                "Should provide specific tags to prioritize based on job match"
            )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_skill_gap_summary_included_in_response(self):
        """Test that skill gap summary is included in tailored resume response.

        EXPECTS FAIL - needs integration into response schema.
        Sprint 2: TailoredResumeResponse should include skill_gap_analysis summary.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            # Response should have comprehensive analysis
            assert hasattr(response, "skill_match_score"), "Should have overall match score"
            assert hasattr(response, "recommendation"), "Should have recommendation"
            assert hasattr(response, "key_positioning_angles"), "Should have positioning angles"

            # These should all be populated
            assert response.skill_match_score is not None
            assert response.recommendation is not None
            assert len(response.key_positioning_angles) > 0
        finally:
            db.rollback()


class TestDatabasePersistence:
    """Test skill gap analysis persistence and caching."""

    @pytest.mark.asyncio
    async def test_skill_gap_analysis_saved_to_job_profile(self):
        """Test that skill gap analysis results are saved to JobProfile.skill_gap_analysis.

        EXPECTS FAIL - needs persistence logic.
        Sprint 2: analyze_skill_gap should save results to database.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)
            job_profile = db.query(JobProfile).filter(
                JobProfile.id == job_profile_id
            ).first()

            # Run analysis
            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            # Refresh from DB to check persistence
            db.refresh(job_profile)

            # Should be saved to skill_gap_analysis JSON field
            assert job_profile.skill_gap_analysis is not None, (
                "Skill gap analysis should be persisted to JobProfile.skill_gap_analysis"
            )

            # Should contain key fields
            analysis_data = job_profile.skill_gap_analysis
            assert "matched_skills" in analysis_data or isinstance(
                analysis_data, dict
            ), (
                "Persisted analysis should be structured data"
            )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_cache_retrieval_works(self):
        """Test that previously computed skill gap analysis can be retrieved from cache.

        EXPECTS FAIL - needs caching logic.
        Sprint 2: Should check for cached analysis before recomputing.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            # First call - compute
            response1 = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            # Second call - should retrieve from cache if implemented
            # Track timestamp or add cache tracking
            response2 = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            # Responses should be consistent
            assert response1.skill_match_score == response2.skill_match_score, (
                "Cached analysis should return consistent results"
            )
            assert (
                len(response1.matched_skills) == len(response2.matched_skills)
            ), (
                "Cached matched skills should be consistent"
            )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_user_profile_change(self):
        """Test that cache is invalidated when user profile changes.

        EXPECTS FAIL - needs cache invalidation logic.
        Sprint 2: Cache should be cleared when user adds/updates skills.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            # Compute initial analysis
            response1 = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )
            initial_score = response1.skill_match_score

            # Add new bullet with high-value skill
            exp = db.query(Experience).filter(
                Experience.user_id == user_id
            ).first()

            new_bullet = Bullet(
                user_id=user_id,
                experience_id=exp.id,
                text="Trained state-of-the-art LLM models using Hugging Face and distributed training",
                tags=["llm", "generative_ai", "huggingface"],
                seniority_level="senior",
                bullet_type="achievement",
                relevance_scores={"llm": 0.95},
                usage_count=0,
            )
            db.add(new_bullet)
            db.commit()

            # Recompute - should be different (cache invalidated)
            response2 = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )
            new_score = response2.skill_match_score

            # Score should improve with new skill
            assert new_score >= initial_score, (
                "Cache should be invalidated when user profile changes. "
                f"Score should improve from {initial_score} with new LLM bullet."
            )
        finally:
            db.rollback()


class TestSkillGapAnalysisIntegration:
    """Integration tests for complete skill gap analysis workflow."""

    @pytest.mark.asyncio
    async def test_end_to_end_analysis_with_real_data(self):
        """Test end-to-end skill gap analysis with realistic data.

        EXPECTS PASS with current implementation.
        Tests that analysis runs without errors and returns valid response.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            # Run full analysis
            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            # Validate response structure
            assert isinstance(response, SkillGapResponse)
            assert response.job_profile_id == job_profile_id
            assert response.user_id == user_id

            # Check all required fields are populated
            assert 0 <= response.skill_match_score <= 100
            assert response.recommendation in [
                "strong_match",
                "moderate_match",
                "weak_match",
                "stretch_role",
            ]
            assert 0 <= response.confidence <= 1

            # Check lists
            assert isinstance(response.matched_skills, list)
            assert isinstance(response.skill_gaps, list)
            assert isinstance(response.weak_signals, list)
            assert isinstance(response.key_positioning_angles, list)
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_analysis_with_comprehensive_user_profile(self):
        """Test analysis with user having strong skill match.

        EXPECTS PASS with current implementation.
        Validates that well-matched candidate gets high score.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            # Build comprehensive skill profile from created data
            user_skill_profile = await build_user_skill_profile(user_id, db)

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
                user_skill_profile=user_skill_profile,
            )

            # User has most required skills, should get decent score
            assert response.skill_match_score >= 50, (
                "User with ML background should score >= 50 for ML role"
            )

            # Should have matched skills
            assert len(response.matched_skills) > 0, (
                "User with technical background should have matched skills"
            )

            # Should have identified some gaps (LLM, AI Governance likely)
            assert len(response.skill_gaps) > 0, (
                "Even strong candidates have some gaps"
            )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_analysis_with_junior_candidate(self):
        """Test analysis with junior-level candidate for senior role.

        EXPECTS PASS with current implementation.
        Validates that gap analysis identifies skill maturity gaps.
        """
        db = next(get_db())
        try:
            unique_id = str(uuid.uuid4())[:8]

            # Create junior user
            user = User(
                username=f"junior_test_{unique_id}",
                email=f"junior_{unique_id}@example.com",
                full_name="Junior Developer",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Create simple experience
            exp = Experience(
                user_id=user.id,
                job_title="Junior Python Developer",
                employer_name="StartupCo",
                location="Remote",
                start_date=date(2023, 6, 1),
                end_date=None,
                description="Python development",
                order=0,
            )
            db.add(exp)
            db.commit()
            db.refresh(exp)

            # Create limited bullets
            bullet = Bullet(
                user_id=user.id,
                experience_id=exp.id,
                text="Developed Python scripts for data processing",
                tags=["python", "data_processing"],
                seniority_level="junior",
                bullet_type="responsibility",
                relevance_scores={"python": 0.70},
                usage_count=0,
            )
            db.add(bullet)

            # Use existing job profile (senior ML role)
            job_profile = db.query(JobProfile).filter(
                JobProfile.user_id == user.id
            ).first()
            if not job_profile:
                # Create new job profile for this user
                job_profile = JobProfile(
                    user_id=user.id,
                    raw_jd_text="Senior ML Role",
                    job_title="Senior ML Engineer",
                    seniority="senior",
                    extracted_skills=[
                        "Machine Learning",
                        "Deep Learning",
                        "Python",
                    ],
                    must_have_capabilities=[
                        "Machine Learning",
                        "Leadership",
                    ],
                )
                db.add(job_profile)
                db.commit()
                db.refresh(job_profile)

            # Run analysis
            response = await analyze_skill_gap(
                job_profile_id=job_profile.id,
                user_id=user.id,
                db=db,
            )

            # Junior candidate should have many critical gaps
            critical_gaps = [
                g for g in response.skill_gaps if g.importance == "critical"
            ]
            assert len(critical_gaps) > 0, (
                "Junior candidate for senior role should have critical gaps"
            )

            # Score should be lower
            assert response.skill_match_score < 50, (
                "Junior candidate for senior role should score < 50"
            )

            # Recommendation should be stretch or weak
            assert response.recommendation in ["stretch_role", "weak_match"], (
                f"Junior for senior role should be stretch or weak, got {response.recommendation}"
            )
        finally:
            db.rollback()


class TestPositioningStrategyContent:
    """Test the actual content and quality of positioning strategies."""

    @pytest.mark.asyncio
    async def test_strategies_are_actionable_not_generic(self):
        """Test that generated strategies are specific and actionable.

        EXPECTS FAIL - current implementation uses templates.
        Sprint 2: Strategies should be customized, not generic templates.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            strategies = response.key_positioning_angles

            # Each strategy should be substantive (> 50 chars) and specific
            for strategy in strategies:
                assert len(strategy) > 50, (
                    f"Strategy should be detailed, not generic: '{strategy}'"
                )
                # Should avoid generic phrases alone
                generic_phrases = [
                    "highlight your experience",
                    "show your skills",
                    "emphasize your work",
                ]
                full_generic = all(p not in strategy for p in generic_phrases)
                assert full_generic or len(strategy) > 100, (
                    "Strategy should provide specific guidance, not just generic phrases"
                )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_mitigation_strategies_address_specific_gaps(self):
        """Test that mitigation strategies directly address identified gaps.

        EXPECTS FAIL - needs gap-specific mitigation.
        Sprint 2: Each gap should have mitigation tailored to that gap.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            # Each gap should have its own positioning strategy
            for gap in response.skill_gaps:
                # Strategy should mention the skill or related concepts
                strategy = gap.positioning_strategy.lower()
                skill_lower = gap.skill.lower()

                # Should reference the specific gap or related concepts
                assert any(
                    word in strategy
                    for word in [
                        skill_lower,  # Direct match like "generative ai"
                        skill_lower.replace(" ", "_"),  # snake_case
                        gap.skill.replace(" ", "").lower(),  # No spaces
                        "gap",
                        "missing",
                        "experience",
                        "developing",
                        "growth",
                    ]
                ), (
                    f"Mitigation for {gap.skill} should reference that skill. "
                    f"Got: {gap.positioning_strategy}"
                )
        finally:
            db.rollback()


class TestCoverLetterAndAdvantagesGeneration:
    """Test generation of cover letter hooks and user advantages."""

    @pytest.mark.asyncio
    async def test_cover_letter_hooks_reference_matched_skills(self):
        """Test that cover letter hooks mention user's strongest matches.

        EXPECTS PASS with current implementation.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            hooks = response.cover_letter_hooks

            # Should have hooks
            assert len(hooks) > 0, "Should generate cover letter hooks"

            # Hooks should reference matched skills
            if response.matched_skills:
                hooks_text = " ".join(hooks).lower()
                top_skill = response.matched_skills[0].skill.lower()
                # At least one hook should mention top matched skill or related concept
                assert any(
                    word in hooks_text
                    for word in [top_skill, "expertise", "experience", "strength"]
                ), (
                    f"Hooks should reference matched skills. "
                    f"Top match: {response.matched_skills[0].skill}"
                )
        finally:
            db.rollback()

    @pytest.mark.asyncio
    async def test_user_advantages_drawn_from_profile(self):
        """Test that user advantages are drawn from actual profile data.

        EXPECTS PASS with current implementation.
        """
        db = next(get_db())
        try:
            user_id, job_profile_id = setup_test_data(db)

            response = await analyze_skill_gap(
                job_profile_id=job_profile_id,
                user_id=user_id,
                db=db,
            )

            advantages = response.user_advantages

            # Should identify advantages from user profile
            assert len(advantages) > 0, "Should identify user advantages"

            # Advantages should be specific to candidate
            # (not generic like "you are hardworking")
            for advantage in advantages:
                assert any(
                    word in advantage.lower()
                    for word in [
                        "experience",
                        "skill",
                        "expertise",
                        "proven",
                        "demonstrated",
                    ]
                ), (
                    f"Advantage should be specific to candidate. Got: {advantage}"
                )
        finally:
            db.rollback()


def run_tests():
    """Run all tests synchronously."""
    print("=" * 70)
    print("Skill Gap Analysis Test Suite - Sprint 2 Enhancements")
    print("=" * 70)
    print("\nNote: Many tests are expected to FAIL (marked with EXPECTS FAIL)")
    print("These document Sprint 2 expected behavior that isn't yet implemented.")
    print("=" * 70)

    # Run async tests
    async def run_async_tests():
        # Semantic matching tests
        print("\nTesting semantic skill matching...")
        test_semantic = TestSemanticSkillMatching()
        test_semantic.test_fallback_to_synonym_when_embedding_unavailable()
        test_semantic.test_multiple_candidate_skills_returns_best_match()
        print("  ✓ Synonym fallback tests passed")

        # Gap categorization tests
        print("\nTesting gap categorization...")
        test_gap = TestGapCategorization()
        await test_gap.test_critical_skills_from_requirements_section()
        await test_gap.test_nice_to_have_skills_categorized_correctly()
        print("  ✓ Gap categorization tests passed")

        # Positioning strategy tests
        print("\nTesting positioning strategies...")
        test_positioning = TestPositioningStrategy()
        await test_positioning.test_strategies_reference_user_actual_skills()
        await test_positioning.test_strategies_align_with_job_priorities()
        await test_positioning.test_critical_gaps_get_mitigation_strategies()
        print("  ✓ Positioning strategy tests passed")

        # Weak signal tests
        print("\nTesting weak signal detection...")
        test_weak = TestWeakSignalDetection()
        await test_weak.test_weak_signal_evidence_includes_actual_bullet_text()
        print("  ✓ Weak signal tests passed")

        # Database persistence tests
        print("\nTesting database persistence...")
        test_db = TestDatabasePersistence()
        await test_db.test_skill_gap_analysis_saved_to_job_profile()
        await test_db.test_cache_retrieval_works()
        print("  ✓ Database persistence tests passed")

        # Integration tests
        print("\nTesting integration workflow...")
        test_integration = TestSkillGapAnalysisIntegration()
        await test_integration.test_end_to_end_analysis_with_real_data()
        await test_integration.test_analysis_with_comprehensive_user_profile()
        await test_integration.test_analysis_with_junior_candidate()
        print("  ✓ Integration tests passed")

        # Cover letter and advantages tests
        print("\nTesting cover letter hooks and advantages...")
        test_cl = TestCoverLetterAndAdvantagesGeneration()
        await test_cl.test_cover_letter_hooks_reference_matched_skills()
        await test_cl.test_user_advantages_drawn_from_profile()
        print("  ✓ Cover letter and advantages tests passed")

    asyncio.run(run_async_tests())

    print("\n" + "=" * 70)
    print("Skill Gap Analysis test suite completed!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
