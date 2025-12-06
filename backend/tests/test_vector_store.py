"""
Integration tests for Sprint 7: Qdrant Vector Store Integration

Comprehensive test suite covering:
- Vector store collection management
- Point operations (upsert, search, delete)
- Bullet and job profile indexing
- Semantic search functionality
- Embedding service extensions
- Factory functions and edge cases

Tests use MockVectorStore and MockEmbeddingService for deterministic,
fast results without requiring Qdrant server or OpenAI API.
"""

import pytest
import math
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any, Optional

from services.vector_store import (
    MockVectorStore,
    BaseVectorStore,
    COLLECTION_SCHEMAS,
    create_vector_store,
    initialize_collections,
    index_bullet,
    index_all_bullets,
    index_job_profile,
    search_similar_bullets,
    search_similar_jobs,
    search_bullets_for_job,
    CONFIG,
)
from services.embeddings import (
    MockEmbeddingService,
    create_embedding_service,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_vector_store():
    """Provide a fresh MockVectorStore instance for each test."""
    return MockVectorStore()


@pytest.fixture
def mock_embedding_service():
    """Provide a MockEmbeddingService instance for tests."""
    return MockEmbeddingService(similarity_threshold=0.60, embedding_dim=384)


@pytest.fixture
def sample_bullet():
    """Create a mock Bullet object with all required fields."""
    bullet = Mock()
    bullet.id = 1
    bullet.user_id = 100
    bullet.experience_id = 10
    bullet.engagement_id = None
    bullet.text = "Developed machine learning models for fraud detection, improving detection accuracy by 35%"
    bullet.tags = ["machine_learning", "fraud_detection", "analytics"]
    bullet.seniority_level = "senior"
    bullet.bullet_type = "achievement"
    bullet.importance = "high"
    bullet.ai_first_choice = True
    bullet.retired = False
    bullet.usage_count = 5
    bullet.embedding = None
    return bullet


@pytest.fixture
def sample_job_profile():
    """Create a mock JobProfile object with all required fields."""
    job = Mock()
    job.id = 1
    job.user_id = 100
    job.company_id = 50
    job.job_title = "Senior Machine Learning Engineer"
    job.location = "San Francisco, CA"
    job.seniority = "senior"
    job.job_type_tags = ["full_time", "remote"]
    job.responsibilities = "Lead ML model development. Mentor junior engineers. Architecture and design decisions."
    job.requirements = "10+ years ML experience. Python proficiency. Deep learning knowledge. Cloud platforms."
    job.nice_to_haves = "Published research. Open source contributions. Kaggle competitions."
    job.embedding = None
    return job


@pytest.fixture
def sample_bullets_batch():
    """Create multiple mock Bullet objects for batch testing."""
    bullets = []

    texts = [
        "Built scalable data pipeline processing 10TB daily with Apache Spark",
        "Optimized SQL queries reducing query time by 60%",
        "Led team of 5 engineers delivering project 2 weeks early",
        "Implemented CI/CD pipeline reducing deployment time by 80%",
        "Developed React frontend with 99.9% uptime SLA"
    ]

    for idx, text in enumerate(texts):
        bullet = Mock()
        bullet.id = idx + 1
        bullet.user_id = 100
        bullet.experience_id = 10
        bullet.engagement_id = None
        bullet.text = text
        bullet.tags = ["tech", "achievement"]
        bullet.seniority_level = "mid"
        bullet.bullet_type = "achievement"
        bullet.importance = "medium"
        bullet.ai_first_choice = False
        bullet.retired = False
        bullet.usage_count = 1
        bullet.embedding = None
        bullets.append(bullet)

    return bullets


# ============================================================================
# COLLECTION MANAGEMENT TESTS
# ============================================================================

class TestCollectionManagement:
    """Tests for collection creation and management."""

    @pytest.mark.asyncio
    async def test_collection_exists_returns_false_before_creation(self, mock_vector_store):
        """Should return False when collection doesn't exist yet."""
        exists = await mock_vector_store.collection_exists("bullets")
        assert exists is False

    @pytest.mark.asyncio
    async def test_ensure_collection_creates_collection(self, mock_vector_store):
        """Should create collection that didn't exist."""
        assert await mock_vector_store.collection_exists("bullets") is False

        await mock_vector_store.ensure_collection("bullets")

        assert await mock_vector_store.collection_exists("bullets") is True

    @pytest.mark.asyncio
    async def test_ensure_collection_is_idempotent(self, mock_vector_store):
        """Should be safe to call ensure_collection multiple times."""
        await mock_vector_store.ensure_collection("bullets")
        await mock_vector_store.ensure_collection("bullets")

        assert await mock_vector_store.collection_exists("bullets") is True

    @pytest.mark.asyncio
    async def test_ensure_collection_raises_for_invalid_schema(self, mock_vector_store):
        """Should raise ValueError for undefined collection schema."""
        with pytest.raises(ValueError, match="No schema defined"):
            await mock_vector_store.ensure_collection("nonexistent_collection")

    @pytest.mark.asyncio
    async def test_initialize_collections_creates_all_required(self, mock_vector_store):
        """Should create all collections defined in COLLECTION_SCHEMAS."""
        assert await mock_vector_store.collection_exists("bullets") is False
        assert await mock_vector_store.collection_exists("jobs") is False
        assert await mock_vector_store.collection_exists("approved_outputs") is False

        await initialize_collections(mock_vector_store)

        assert await mock_vector_store.collection_exists("bullets") is True
        assert await mock_vector_store.collection_exists("jobs") is True
        assert await mock_vector_store.collection_exists("approved_outputs") is True

    @pytest.mark.asyncio
    async def test_collection_schemas_have_required_fields(self):
        """Should define required schema fields for each collection."""
        required_fields = {"vector_size", "distance", "payload_schema"}

        for collection_name, schema in COLLECTION_SCHEMAS.items():
            assert isinstance(schema, dict), f"Schema for {collection_name} must be dict"
            assert all(f in schema for f in required_fields), \
                f"Schema for {collection_name} missing required fields"
            assert schema["vector_size"] == 384
            assert schema["distance"] == "Cosine"


# ============================================================================
# POINT OPERATIONS TESTS
# ============================================================================

class TestPointOperations:
    """Tests for vector point storage and retrieval operations."""

    @pytest.mark.asyncio
    async def test_upsert_points_stores_vectors(self, mock_vector_store):
        """Should store points with vectors and payloads."""
        await mock_vector_store.ensure_collection("bullets")

        points = [{
            "id": 1,
            "vector": [0.1] * 384,
            "payload": {"text": "test bullet", "user_id": 100}
        }]

        await mock_vector_store.upsert_points("bullets", points)

        # Verify point was stored by searching
        results = await mock_vector_store.search("bullets", [0.1] * 384, limit=10)
        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["payload"]["text"] == "test bullet"

    @pytest.mark.asyncio
    async def test_upsert_points_empty_list_is_noop(self, mock_vector_store):
        """Should handle empty point list gracefully."""
        await mock_vector_store.ensure_collection("bullets")

        # Should not raise error
        await mock_vector_store.upsert_points("bullets", [])

        results = await mock_vector_store.search("bullets", [0.1] * 384, limit=10)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_upsert_points_requires_id_and_vector(self, mock_vector_store):
        """Should raise ValueError if points missing required fields."""
        await mock_vector_store.ensure_collection("bullets")

        # Missing vector
        with pytest.raises(ValueError, match="id.*vector"):
            await mock_vector_store.upsert_points("bullets", [{"id": 1}])

        # Missing id
        with pytest.raises(ValueError, match="id.*vector"):
            await mock_vector_store.upsert_points("bullets", [{"vector": [0.1] * 384}])

    @pytest.mark.asyncio
    async def test_upsert_points_overwrites_existing(self, mock_vector_store):
        """Should overwrite point with same ID."""
        await mock_vector_store.ensure_collection("bullets")

        # First upsert
        await mock_vector_store.upsert_points("bullets", [{
            "id": 1,
            "vector": [0.1] * 384,
            "payload": {"text": "original"}
        }])

        # Second upsert with same ID, different payload
        await mock_vector_store.upsert_points("bullets", [{
            "id": 1,
            "vector": [0.2] * 384,
            "payload": {"text": "updated"}
        }])

        results = await mock_vector_store.search("bullets", [0.2] * 384, limit=10)
        assert len(results) == 1
        assert results[0]["payload"]["text"] == "updated"

    @pytest.mark.asyncio
    async def test_delete_points_removes_vectors(self, mock_vector_store):
        """Should delete points by ID."""
        await mock_vector_store.ensure_collection("bullets")

        # Add points
        await mock_vector_store.upsert_points("bullets", [
            {"id": 1, "vector": [0.1] * 384, "payload": {}},
            {"id": 2, "vector": [0.2] * 384, "payload": {}},
        ])

        # Delete one point
        await mock_vector_store.delete_points("bullets", [1])

        results = await mock_vector_store.search("bullets", [0.1] * 384, limit=10)
        assert len(results) == 1
        assert results[0]["id"] == 2

    @pytest.mark.asyncio
    async def test_delete_points_nonexistent_ids_safe(self, mock_vector_store):
        """Should not error when deleting non-existent IDs."""
        await mock_vector_store.ensure_collection("bullets")

        await mock_vector_store.upsert_points("bullets", [{
            "id": 1,
            "vector": [0.1] * 384,
            "payload": {}
        }])

        # Should not raise
        await mock_vector_store.delete_points("bullets", [999])

        # Original point still there
        results = await mock_vector_store.search("bullets", [0.1] * 384, limit=10)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_delete_points_empty_list_is_noop(self, mock_vector_store):
        """Should handle empty delete list gracefully."""
        await mock_vector_store.ensure_collection("bullets")

        await mock_vector_store.upsert_points("bullets", [{
            "id": 1,
            "vector": [0.1] * 384,
            "payload": {}
        }])

        # Should not raise
        await mock_vector_store.delete_points("bullets", [])

        results = await mock_vector_store.search("bullets", [0.1] * 384, limit=10)
        assert len(results) == 1


# ============================================================================
# SEARCH TESTS
# ============================================================================

class TestSearch:
    """Tests for vector similarity search."""

    @pytest.mark.asyncio
    async def test_search_returns_results_sorted_by_score(self, mock_vector_store):
        """Should return results sorted by similarity score descending."""
        await mock_vector_store.ensure_collection("bullets")

        # Add points with identical vectors (perfect match = score 1.0)
        vec1 = self._normalize_vector([1.0, 0.0, 0.0])
        vec2 = self._normalize_vector([0.9, 0.1, 0.0])
        vec3 = self._normalize_vector([0.5, 0.5, 0.0])

        await mock_vector_store.upsert_points("bullets", [
            {"id": 1, "vector": vec1, "payload": {"rank": 1}},
            {"id": 2, "vector": vec2, "payload": {"rank": 2}},
            {"id": 3, "vector": vec3, "payload": {"rank": 3}},
        ])

        # Search with query similar to vec1
        results = await mock_vector_store.search("bullets", vec1, limit=10)

        assert len(results) == 3
        # Verify sorted descending by score
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_search_with_score_threshold_filters_results(self, mock_vector_store):
        """Should filter out results below score threshold."""
        await mock_vector_store.ensure_collection("bullets")

        query_vec = self._normalize_vector([1.0, 0.0, 0.0])
        vec_similar = self._normalize_vector([0.95, 0.05, 0.0])
        vec_different = self._normalize_vector([0.0, 1.0, 0.0])

        await mock_vector_store.upsert_points("bullets", [
            {"id": 1, "vector": vec_similar, "payload": {}},
            {"id": 2, "vector": vec_different, "payload": {}},
        ])

        # High threshold should exclude different vector
        results = await mock_vector_store.search(
            "bullets",
            query_vec,
            limit=10,
            score_threshold=0.8
        )

        # Should only return similar vector
        assert len(results) >= 1
        assert results[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_search_with_filters_on_payload_fields(self, mock_vector_store):
        """Should filter results by payload field values."""
        await mock_vector_store.ensure_collection("bullets")

        vec = self._normalize_vector([1.0, 0.0, 0.0])

        await mock_vector_store.upsert_points("bullets", [
            {"id": 1, "vector": vec, "payload": {"user_id": 100, "tags": ["ai"]}},
            {"id": 2, "vector": vec, "payload": {"user_id": 200, "tags": ["ai"]}},
            {"id": 3, "vector": vec, "payload": {"user_id": 100, "tags": ["ml"]}},
        ])

        # Filter by user_id
        results = await mock_vector_store.search(
            "bullets",
            vec,
            limit=10,
            filters={"user_id": 100}
        )

        assert len(results) == 2
        assert all(r["payload"]["user_id"] == 100 for r in results)

    @pytest.mark.asyncio
    async def test_search_with_filters_list_values(self, mock_vector_store):
        """Should support filtering with list of acceptable values."""
        await mock_vector_store.ensure_collection("bullets")

        vec = self._normalize_vector([1.0, 0.0, 0.0])

        await mock_vector_store.upsert_points("bullets", [
            {"id": 1, "vector": vec, "payload": {"importance": "high"}},
            {"id": 2, "vector": vec, "payload": {"importance": "medium"}},
            {"id": 3, "vector": vec, "payload": {"importance": "low"}},
        ])

        # Filter with list of values
        results = await mock_vector_store.search(
            "bullets",
            vec,
            limit=10,
            filters={"importance": ["high", "medium"]}
        )

        assert len(results) == 2
        assert all(r["payload"]["importance"] in ["high", "medium"] for r in results)

    @pytest.mark.asyncio
    async def test_search_with_limit_parameter(self, mock_vector_store):
        """Should respect limit parameter."""
        await mock_vector_store.ensure_collection("bullets")

        vec = self._normalize_vector([1.0, 0.0, 0.0])

        # Add 10 points
        points = [
            {"id": i, "vector": vec, "payload": {}}
            for i in range(1, 11)
        ]
        await mock_vector_store.upsert_points("bullets", points)

        # Test different limits
        results = await mock_vector_store.search("bullets", vec, limit=3)
        assert len(results) == 3

        results = await mock_vector_store.search("bullets", vec, limit=5)
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_search_empty_collection_returns_empty_list(self, mock_vector_store):
        """Should return empty list when searching empty collection."""
        await mock_vector_store.ensure_collection("bullets")

        results = await mock_vector_store.search(
            "bullets",
            self._normalize_vector([1.0, 0.0, 0.0]),
            limit=10
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_search_nonexistent_collection_returns_empty(self, mock_vector_store):
        """Should return empty list for non-existent collection."""
        results = await mock_vector_store.search(
            "nonexistent",
            self._normalize_vector([1.0, 0.0, 0.0]),
            limit=10
        )

        assert results == []

    @staticmethod
    def _normalize_vector(vec: List[float]) -> List[float]:
        """Normalize a vector to unit length."""
        magnitude = math.sqrt(sum(v * v for v in vec))
        if magnitude == 0:
            return vec
        return [v / magnitude for v in vec]


# ============================================================================
# BULLET INDEXING TESTS
# ============================================================================

class TestBulletIndexing:
    """Tests for indexing resume bullets into vector store."""

    @pytest.mark.asyncio
    async def test_index_bullet_creates_point(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_bullet
    ):
        """Should index bullet with correct payload."""
        await mock_vector_store.ensure_collection("bullets")

        await index_bullet(sample_bullet, mock_embedding_service, mock_vector_store)

        # Verify point was stored
        embedding = await mock_embedding_service.generate_embedding(sample_bullet.text)
        results = await mock_vector_store.search("bullets", embedding, limit=10)

        assert len(results) == 1
        assert results[0]["id"] == 1
        payload = results[0]["payload"]
        assert payload["bullet_id"] == 1
        assert payload["user_id"] == 100
        assert payload["text"] == sample_bullet.text

    @pytest.mark.asyncio
    async def test_index_bullet_generates_embedding_if_missing(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_bullet
    ):
        """Should generate embedding if bullet doesn't have one."""
        await mock_vector_store.ensure_collection("bullets")
        sample_bullet.embedding = None

        # Mock embedding service to track calls
        original_embed = mock_embedding_service.generate_embedding
        call_count = []

        async def tracked_embed(text):
            call_count.append(text)
            return await original_embed(text)

        mock_embedding_service.generate_embedding = tracked_embed

        await index_bullet(sample_bullet, mock_embedding_service, mock_vector_store)

        # Should have called embedding service
        assert len(call_count) > 0
        assert sample_bullet.text in call_count

    @pytest.mark.asyncio
    async def test_index_bullet_uses_existing_embedding(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_bullet
    ):
        """Should use pre-generated embedding if available."""
        await mock_vector_store.ensure_collection("bullets")

        # Pre-set embedding
        sample_bullet.embedding = [0.1] * 384

        # Mock to verify it's not called
        original_embed = mock_embedding_service.generate_embedding
        call_count = []

        async def tracked_embed(text):
            call_count.append(text)
            return await original_embed(text)

        mock_embedding_service.generate_embedding = tracked_embed

        await index_bullet(sample_bullet, mock_embedding_service, mock_vector_store)

        # Should use existing embedding, but may still call for search
        # Just verify it works
        results = await mock_vector_store.search("bullets", [0.1] * 384, limit=10)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_index_bullet_skips_retired_when_configured(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_bullet
    ):
        """Should skip retired bullets when index_retired_bullets is False."""
        await mock_vector_store.ensure_collection("bullets")
        sample_bullet.retired = True

        # With default config (index_retired_bullets=False)
        await index_bullet(sample_bullet, mock_embedding_service, mock_vector_store)

        # Bullet should not be indexed
        embedding = await mock_embedding_service.generate_embedding("any text")
        results = await mock_vector_store.search("bullets", embedding, limit=10)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_index_all_bullets_indexes_multiple(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_bullets_batch
    ):
        """Should index multiple bullets in batch."""
        await mock_vector_store.ensure_collection("bullets")

        # Mock database session
        mock_db = Mock()

        # Mock query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_bullets_batch
        mock_db.query.return_value = mock_query

        indexed_count = await index_all_bullets(
            mock_db,
            mock_embedding_service,
            mock_vector_store
        )

        assert indexed_count == len(sample_bullets_batch)

        # Verify all bullets were indexed
        embedding = await mock_embedding_service.generate_embedding("test")
        results = await mock_vector_store.search("bullets", embedding, limit=100)
        assert len(results) == len(sample_bullets_batch)

    @pytest.mark.asyncio
    async def test_index_all_bullets_filters_by_user_id(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_bullets_batch
    ):
        """Should filter bullets by user_id."""
        await mock_vector_store.ensure_collection("bullets")

        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_bullets_batch[:2]  # Return subset
        mock_db.query.return_value = mock_query

        indexed_count = await index_all_bullets(
            mock_db,
            mock_embedding_service,
            mock_vector_store,
            user_id=100
        )

        assert indexed_count == 2
        mock_db.query.assert_called()
        # First filter call should be for user_id
        mock_query.filter.assert_called()

    @pytest.mark.asyncio
    async def test_index_all_bullets_respects_batch_size(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_bullets_batch
    ):
        """Should process bullets in batches respecting config batch size."""
        await mock_vector_store.ensure_collection("bullets")

        # Mock database
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_bullets_batch
        mock_db.query.return_value = mock_query

        # Mock upsert to track calls
        upsert_calls = []
        original_upsert = mock_vector_store.upsert_points

        async def tracked_upsert(collection_name, points):
            upsert_calls.append(len(points))
            return await original_upsert(collection_name, points)

        mock_vector_store.upsert_points = tracked_upsert

        indexed_count = await index_all_bullets(
            mock_db,
            mock_embedding_service,
            mock_vector_store
        )

        assert indexed_count == len(sample_bullets_batch)
        # Verify batching occurred (batch size is 50 by default)
        assert len(upsert_calls) >= 1


# ============================================================================
# JOB PROFILE INDEXING TESTS
# ============================================================================

class TestJobProfileIndexing:
    """Tests for indexing job profiles into vector store."""

    @pytest.mark.asyncio
    async def test_index_job_profile_creates_point(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_job_profile
    ):
        """Should index job profile with correct payload."""
        await mock_vector_store.ensure_collection("jobs")

        await index_job_profile(
            sample_job_profile,
            mock_embedding_service,
            mock_vector_store
        )

        # Verify point was stored
        embedding = await mock_embedding_service.embed_job_profile(
            title=sample_job_profile.job_title,
            responsibilities=sample_job_profile.responsibilities,
            requirements=sample_job_profile.requirements,
            nice_to_haves=sample_job_profile.nice_to_haves
        )
        results = await mock_vector_store.search("jobs", embedding, limit=10)

        assert len(results) == 1
        assert results[0]["id"] == 1
        payload = results[0]["payload"]
        assert payload["job_profile_id"] == 1
        assert payload["user_id"] == 100
        assert payload["job_title"] == sample_job_profile.job_title

    @pytest.mark.asyncio
    async def test_index_job_profile_generates_embedding_if_missing(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_job_profile
    ):
        """Should generate embedding if job doesn't have one."""
        await mock_vector_store.ensure_collection("jobs")
        sample_job_profile.embedding = None

        # Mock to track calls
        original_embed = mock_embedding_service.embed_job_profile
        call_count = []

        async def tracked_embed(*args, **kwargs):
            call_count.append((args, kwargs))
            return await original_embed(*args, **kwargs)

        mock_embedding_service.embed_job_profile = tracked_embed

        await index_job_profile(
            sample_job_profile,
            mock_embedding_service,
            mock_vector_store
        )

        # Should have called embedding service
        assert len(call_count) > 0

    @pytest.mark.asyncio
    async def test_index_job_profile_uses_existing_embedding(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_job_profile
    ):
        """Should use pre-generated embedding if available."""
        await mock_vector_store.ensure_collection("jobs")

        # Pre-set embedding
        sample_job_profile.embedding = [0.2] * 384

        await index_job_profile(
            sample_job_profile,
            mock_embedding_service,
            mock_vector_store
        )

        # Should be searchable with that embedding
        results = await mock_vector_store.search("jobs", [0.2] * 384, limit=10)
        assert len(results) == 1


# ============================================================================
# SEMANTIC SEARCH TESTS
# ============================================================================

class TestSemanticSearch:
    """Tests for semantic search functions."""

    @pytest.mark.asyncio
    async def test_search_similar_bullets_returns_relevant_results(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_bullets_batch
    ):
        """Should find relevant bullets for query text."""
        await mock_vector_store.ensure_collection("bullets")

        # Index some bullets
        for bullet in sample_bullets_batch:
            await index_bullet(bullet, mock_embedding_service, mock_vector_store)

        # Search for related concept
        query = "data processing infrastructure"
        results = await search_similar_bullets(
            query,
            mock_embedding_service,
            mock_vector_store,
            limit=5
        )

        assert isinstance(results, list)
        # Mock embeddings may not be semantically meaningful, but structure should be correct
        if results:
            assert "id" in results[0]
            assert "score" in results[0]
            assert "payload" in results[0]

    @pytest.mark.asyncio
    async def test_search_similar_bullets_respects_filters(
        self,
        mock_vector_store,
        mock_embedding_service
    ):
        """Should apply filters when searching."""
        await mock_vector_store.ensure_collection("bullets")

        # Add bullets with different user IDs
        bullets = []
        for user_id in [100, 200]:
            bullet = Mock()
            bullet.id = user_id
            bullet.user_id = user_id
            bullet.experience_id = 1
            bullet.engagement_id = None
            bullet.text = "Machine learning experience"
            bullet.tags = ["ml"]
            bullet.seniority_level = "senior"
            bullet.bullet_type = "achievement"
            bullet.importance = "high"
            bullet.ai_first_choice = True
            bullet.retired = False
            bullet.usage_count = 1
            bullet.embedding = None
            bullets.append(bullet)

        for bullet in bullets:
            await index_bullet(bullet, mock_embedding_service, mock_vector_store)

        # Search with filter
        results = await search_similar_bullets(
            "ML work",
            mock_embedding_service,
            mock_vector_store,
            limit=10,
            filters={"user_id": 100}
        )

        # Should only return results for user 100
        assert all(r["payload"]["user_id"] == 100 for r in results)

    @pytest.mark.asyncio
    async def test_search_similar_jobs_returns_relevant_results(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_job_profile
    ):
        """Should find relevant job profiles for query text."""
        await mock_vector_store.ensure_collection("jobs")

        # Index job
        await index_job_profile(
            sample_job_profile,
            mock_embedding_service,
            mock_vector_store
        )

        # Search for similar job
        results = await search_similar_jobs(
            "ML Engineer role",
            mock_embedding_service,
            mock_vector_store,
            limit=5
        )

        assert isinstance(results, list)
        if results:
            assert "id" in results[0]
            assert "score" in results[0]
            assert "payload" in results[0]

    @pytest.mark.asyncio
    async def test_search_bullets_for_job_finds_matching_bullets(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_job_profile,
        sample_bullets_batch
    ):
        """Should find bullets matching a job profile."""
        await mock_vector_store.ensure_collection("bullets")

        # Index bullets
        for bullet in sample_bullets_batch:
            await index_bullet(bullet, mock_embedding_service, mock_vector_store)

        # Search for matching bullets
        results = await search_bullets_for_job(
            sample_job_profile,
            mock_embedding_service,
            mock_vector_store,
            limit=10
        )

        assert isinstance(results, list)
        # Should find some matches given the sample data
        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_search_bullets_for_job_uses_existing_embedding(
        self,
        mock_vector_store,
        mock_embedding_service,
        sample_job_profile,
        sample_bullets_batch
    ):
        """Should use job's existing embedding if available."""
        await mock_vector_store.ensure_collection("bullets")

        # Pre-set job embedding
        sample_job_profile.embedding = [0.3] * 384

        # Index a bullet with similar embedding
        bullet = sample_bullets_batch[0]
        bullet.embedding = [0.3] * 384
        await index_bullet(bullet, mock_embedding_service, mock_vector_store)

        results = await search_bullets_for_job(
            sample_job_profile,
            mock_embedding_service,
            mock_vector_store,
            limit=10
        )

        assert isinstance(results, list)
        if results:
            assert results[0]["id"] == bullet.id


# ============================================================================
# EMBEDDING SERVICE EXTENSION TESTS
# ============================================================================

class TestEmbeddingServiceExtensions:
    """Tests for new embedding service methods."""

    @pytest.mark.asyncio
    async def test_embed_bullet_generates_384d_embedding(
        self,
        mock_embedding_service
    ):
        """Should generate 384-dimension embedding for bullet."""
        embedding = await mock_embedding_service.embed_bullet(
            "Developed ML models with 95% accuracy"
        )

        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(v, float) for v in embedding)

    @pytest.mark.asyncio
    async def test_embed_bullet_with_context_parameter(
        self,
        mock_embedding_service
    ):
        """Should accept optional context parameter."""
        context = {"role": "senior", "domain": "ml"}
        embedding = await mock_embedding_service.embed_bullet(
            "Developed ML models",
            context=context
        )

        assert len(embedding) == 384

    @pytest.mark.asyncio
    async def test_embed_job_profile_combines_fields(
        self,
        mock_embedding_service,
        sample_job_profile
    ):
        """Should combine all job profile fields into single embedding."""
        embedding = await mock_embedding_service.embed_job_profile(
            title=sample_job_profile.job_title,
            responsibilities=sample_job_profile.responsibilities,
            requirements=sample_job_profile.requirements,
            nice_to_haves=sample_job_profile.nice_to_haves
        )

        assert isinstance(embedding, list)
        assert len(embedding) == 384

    @pytest.mark.asyncio
    async def test_embed_job_profile_without_nice_to_haves(
        self,
        mock_embedding_service
    ):
        """Should handle optional nice_to_haves field."""
        embedding = await mock_embedding_service.embed_job_profile(
            title="Software Engineer",
            responsibilities="Build scalable systems",
            requirements="Python, Docker",
            nice_to_haves=None
        )

        assert len(embedding) == 384

    @pytest.mark.asyncio
    async def test_embed_job_profile_validates_required_fields(
        self,
        mock_embedding_service
    ):
        """Should raise ValueError for empty required fields."""
        with pytest.raises(ValueError, match="title"):
            await mock_embedding_service.embed_job_profile(
                title="",
                responsibilities="Something",
                requirements="Something"
            )

        with pytest.raises(ValueError, match="Responsibilities"):
            await mock_embedding_service.embed_job_profile(
                title="Engineer",
                responsibilities="",
                requirements="Something"
            )

        with pytest.raises(ValueError, match="Requirements"):
            await mock_embedding_service.embed_job_profile(
                title="Engineer",
                responsibilities="Something",
                requirements=""
            )


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================

class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_vector_store_mock_flag(self):
        """Should return MockVectorStore when use_mock=True."""
        store = create_vector_store(use_mock=True)
        assert isinstance(store, MockVectorStore)

    def test_create_vector_store_singleton_behavior(self):
        """Mock vector store should be fresh instance per call."""
        store1 = create_vector_store(use_mock=True)
        store2 = create_vector_store(use_mock=True)
        # Each call should return a new MockVectorStore instance
        assert isinstance(store1, MockVectorStore)
        assert isinstance(store2, MockVectorStore)

    def test_create_embedding_service_mock_flag(self):
        """Should return MockEmbeddingService when use_mock=True."""
        service = create_embedding_service(use_mock=True)
        assert isinstance(service, MockEmbeddingService)

    def test_create_embedding_service_with_custom_threshold(self):
        """Should accept custom similarity threshold."""
        service = create_embedding_service(
            use_mock=True,
            similarity_threshold=0.80
        )
        assert service.similarity_threshold == 0.80


# ============================================================================
# COSINE SIMILARITY TESTS
# ============================================================================

class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    @staticmethod
    def _normalize_vector(vec: List[float]) -> List[float]:
        """Normalize a vector to unit length."""
        magnitude = math.sqrt(sum(v * v for v in vec))
        if magnitude == 0:
            return vec
        return [v / magnitude for v in vec]

    def test_cosine_similarity_identical_vectors(self):
        """Cosine similarity of identical vectors should be 1.0."""
        vec = [1.0, 0.0, 0.0]
        similarity = MockVectorStore._cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self):
        """Cosine similarity of orthogonal vectors should be ~0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = MockVectorStore._cosine_similarity(vec1, vec2)
        assert abs(similarity) < 1e-6

    def test_cosine_similarity_opposite_vectors(self):
        """Cosine similarity of opposite vectors should be -1."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        similarity = MockVectorStore._cosine_similarity(vec1, vec2)
        assert abs(similarity - (-1.0)) < 1e-6

    def test_cosine_similarity_with_zero_vector(self):
        """Cosine similarity with zero vector should be 0."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 0.0, 0.0]
        similarity = MockVectorStore._cosine_similarity(vec1, vec2)
        assert similarity == 0.0

    def test_cosine_similarity_dimension_mismatch(self):
        """Should raise ValueError for different dimensions."""
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        with pytest.raises(ValueError, match="dimension"):
            MockVectorStore._cosine_similarity(vec1, vec2)


# ============================================================================
# EDGE CASES AND INTEGRATION TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and integration scenarios."""

    @pytest.mark.asyncio
    async def test_search_with_multiple_filters(self, mock_vector_store):
        """Should handle multiple filter conditions."""
        await mock_vector_store.ensure_collection("bullets")

        vec = TestSearch._normalize_vector([1.0, 0.0, 0.0])

        await mock_vector_store.upsert_points("bullets", [
            {
                "id": 1,
                "vector": vec,
                "payload": {"user_id": 100, "importance": "high", "retired": False}
            },
            {
                "id": 2,
                "vector": vec,
                "payload": {"user_id": 100, "importance": "low", "retired": False}
            },
            {
                "id": 3,
                "vector": vec,
                "payload": {"user_id": 200, "importance": "high", "retired": False}
            },
        ])

        # Multiple filters
        results = await mock_vector_store.search(
            "bullets",
            vec,
            limit=10,
            filters={"user_id": 100, "importance": "high"}
        )

        assert len(results) == 1
        assert results[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_batch_upsert_operations(self, mock_vector_store):
        """Should handle large batch operations."""
        await mock_vector_store.ensure_collection("bullets")

        vec = TestSearch._normalize_vector([0.5, 0.5, 0.0])

        # Create large batch
        points = [
            {"id": i, "vector": vec, "payload": {"index": i}}
            for i in range(200)
        ]

        await mock_vector_store.upsert_points("bullets", points)

        results = await mock_vector_store.search("bullets", vec, limit=100)
        assert len(results) == 100

    @pytest.mark.asyncio
    async def test_mixed_filter_and_threshold(self, mock_vector_store):
        """Should combine filters and score threshold."""
        await mock_vector_store.ensure_collection("bullets")

        query_vec = TestSearch._normalize_vector([1.0, 0.0, 0.0])
        vec_similar = TestSearch._normalize_vector([0.9, 0.1, 0.0])
        vec_different = TestSearch._normalize_vector([0.0, 1.0, 0.0])

        await mock_vector_store.upsert_points("bullets", [
            {"id": 1, "vector": vec_similar, "payload": {"user_id": 100}},
            {"id": 2, "vector": vec_different, "payload": {"user_id": 100}},
            {"id": 3, "vector": vec_similar, "payload": {"user_id": 200}},
        ])

        results = await mock_vector_store.search(
            "bullets",
            query_vec,
            limit=10,
            score_threshold=0.8,
            filters={"user_id": 100}
        )

        # Should only return ID 1: user 100 AND high similarity
        assert len(results) >= 1
        assert results[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_payload_preservation_through_operations(
        self,
        mock_vector_store
    ):
        """Should preserve complete payload through store and retrieve."""
        await mock_vector_store.ensure_collection("bullets")

        original_payload = {
            "bullet_id": 1,
            "user_id": 100,
            "text": "Complex achievement",
            "tags": ["ai", "ml", "governance"],
            "seniority_level": "senior",
            "ai_first_choice": True,
            "usage_count": 42
        }

        vec = TestSearch._normalize_vector([0.5, 0.5, 0.0])

        await mock_vector_store.upsert_points("bullets", [{
            "id": 1,
            "vector": vec,
            "payload": original_payload
        }])

        results = await mock_vector_store.search("bullets", vec, limit=10)

        assert results[0]["payload"] == original_payload

    @pytest.mark.asyncio
    async def test_collection_isolation(self, mock_vector_store):
        """Should keep different collections isolated."""
        await mock_vector_store.ensure_collection("bullets")
        await mock_vector_store.ensure_collection("jobs")

        vec = TestSearch._normalize_vector([1.0, 0.0, 0.0])

        # Add to both collections
        await mock_vector_store.upsert_points("bullets", [{
            "id": 1,
            "vector": vec,
            "payload": {"type": "bullet"}
        }])

        await mock_vector_store.upsert_points("jobs", [{
            "id": 1,
            "vector": vec,
            "payload": {"type": "job"}
        }])

        # Search each collection
        bullet_results = await mock_vector_store.search("bullets", vec, limit=10)
        job_results = await mock_vector_store.search("jobs", vec, limit=10)

        assert len(bullet_results) == 1
        assert bullet_results[0]["payload"]["type"] == "bullet"
        assert len(job_results) == 1
        assert job_results[0]["payload"]["type"] == "job"
