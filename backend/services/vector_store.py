"""
Vector Store Service for Semantic Search

Provides Qdrant integration for indexing and searching:
- Resume bullets
- Job profiles
- Approved outputs (future Sprint 8)

Supports both production Qdrant instances and in-memory mock for testing.

Note: The QdrantVectorStore uses synchronous QdrantClient internally.
For high-concurrency production use, consider switching to AsyncQdrantClient
from qdrant_client.async_qdrant_client and properly awaiting all client calls.
The current implementation is suitable for single-user CLI and development use.
"""

import logging
import math
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple, Set

import yaml


logger = logging.getLogger(__name__)


# Configuration loader
def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = os.path.join(
        os.path.dirname(__file__), '..', 'config', 'config.yaml'
    )
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # Return defaults if config not found
        return {
            'vector_store': {
                'host': 'localhost',
                'port': 6333,
                'collection_prefix': 'etps_',
                'auto_index_on_startup': True,
                'batch_size': 50
            },
            'embeddings': {
                'vector_dimensions': 384,
                'index_retired_bullets': False
            }
        }


# Load config at module level
CONFIG = load_config()

# Constants for collection names
COLLECTION_BULLETS = 'bullets'
COLLECTION_JOBS = 'jobs'
COLLECTION_APPROVED_OUTPUTS = 'approved_outputs'

# Configuration constants
BATCH_SIZE = CONFIG.get('vector_store', {}).get('batch_size', 50)
SIMILARITY_THRESHOLD = CONFIG.get('embeddings', {}).get('similarity_threshold', 0.60)
VECTOR_DIMENSIONS = CONFIG.get('embeddings', {}).get('vector_dimensions', 384)
INDEX_RETIRED_BULLETS = CONFIG.get('embeddings', {}).get('index_retired_bullets', False)

# Allowed filter fields per collection (for security validation)
ALLOWED_FILTER_FIELDS: Dict[str, Set[str]] = {
    COLLECTION_BULLETS: {
        'bullet_id', 'user_id', 'experience_id', 'engagement_id', 'text',
        'tags', 'seniority_level', 'bullet_type', 'importance',
        'ai_first_choice', 'retired', 'usage_count'
    },
    COLLECTION_JOBS: {
        'job_profile_id', 'user_id', 'company_id', 'job_title', 'location',
        'seniority', 'job_type_tags', 'responsibilities', 'requirements',
        'nice_to_haves'
    },
    COLLECTION_APPROVED_OUTPUTS: {
        'output_id', 'user_id', 'application_id', 'output_type', 'text',
        'quality_score', 'created_at'
    }
}

# Collection schemas
COLLECTION_SCHEMAS = {
    'bullets': {
        'vector_size': CONFIG.get('embeddings', {}).get('vector_dimensions', 384),
        'distance': 'Cosine',
        'payload_schema': {
            'bullet_id': 'int',
            'user_id': 'int',
            'experience_id': 'int',
            'engagement_id': 'int?',
            'text': 'str',
            'tags': 'list[str]?',
            'seniority_level': 'str?',
            'bullet_type': 'str?',
            'importance': 'str?',
            'ai_first_choice': 'bool',
            'retired': 'bool',
            'usage_count': 'int'
        }
    },
    'jobs': {
        'vector_size': CONFIG.get('embeddings', {}).get('vector_dimensions', 384),
        'distance': 'Cosine',
        'payload_schema': {
            'job_profile_id': 'int',
            'user_id': 'int',
            'company_id': 'int?',
            'job_title': 'str',
            'location': 'str?',
            'seniority': 'str?',
            'job_type_tags': 'list[str]?',
            'responsibilities': 'str',
            'requirements': 'str',
            'nice_to_haves': 'str?'
        }
    },
    'approved_outputs': {
        'vector_size': CONFIG.get('embeddings', {}).get('vector_dimensions', 384),
        'distance': 'Cosine',
        'payload_schema': {
            'output_id': 'int',
            'user_id': 'int',
            'application_id': 'int?',
            'output_type': 'str',  # 'bullet', 'cover_letter_paragraph', 'summary'
            'text': 'str',
            'quality_score': 'float?',
            'created_at': 'str'
        }
    }
}


class BaseVectorStore(ABC):
    """
    Abstract base class for vector store implementations.

    Defines the interface for storing and searching vector embeddings
    with associated metadata payloads.
    """

    @abstractmethod
    async def ensure_collection(self, collection_name: str) -> None:
        """
        Ensure collection exists, creating it if necessary.

        Args:
            collection_name: Name of the collection

        Raises:
            RuntimeError: If collection creation fails
        """
        pass

    @abstractmethod
    async def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> None:
        """
        Upsert points into collection.

        Points format: [{'id': int|str, 'vector': List[float], 'payload': dict}, ...]

        Args:
            collection_name: Name of the collection
            points: List of points to upsert

        Raises:
            ValueError: If points format is invalid
            RuntimeError: If upsert fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in collection.

        Args:
            collection_name: Name of the collection
            query_vector: Query embedding vector
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0-1)
            filters: Optional filters on payload fields

        Returns:
            List of results with format: [{'id': ..., 'score': ..., 'payload': ...}, ...]

        Raises:
            RuntimeError: If search fails
        """
        pass

    @abstractmethod
    async def delete_points(
        self,
        collection_name: str,
        point_ids: List[Any]
    ) -> None:
        """
        Delete points from collection by ID.

        Args:
            collection_name: Name of the collection
            point_ids: List of point IDs to delete

        Raises:
            RuntimeError: If deletion fails
        """
        pass

    @abstractmethod
    async def collection_exists(self, collection_name: str) -> bool:
        """
        Check if collection exists.

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists, False otherwise
        """
        pass


class QdrantVectorStore(BaseVectorStore):
    """
    Qdrant vector store implementation.

    Connects to Qdrant server and provides vector search capabilities.
    Uses singleton pattern to ensure single connection per process.
    """

    _instance: Optional['QdrantVectorStore'] = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_prefix: Optional[str] = None
    ):
        """
        Initialize Qdrant vector store.

        Args:
            host: Qdrant server host (defaults to config)
            port: Qdrant server port (defaults to config)
            collection_prefix: Prefix for collection names (defaults to config)

        Raises:
            ImportError: If qdrant-client not installed
            RuntimeError: If connection to Qdrant fails
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            self.QdrantClient = QdrantClient
            self.Distance = Distance
            self.VectorParams = VectorParams
        except ImportError:
            raise ImportError(
                "qdrant-client package required for Qdrant vector store. "
                "Install with: pip install qdrant-client"
            )

        # Get config values
        vs_config = CONFIG.get('vector_store', {})
        self.host = host or vs_config.get('host', 'localhost')
        self.port = port or vs_config.get('port', 6333)
        self.collection_prefix = collection_prefix or vs_config.get('collection_prefix', 'etps_')

        try:
            self.client = self.QdrantClient(host=self.host, port=self.port)
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to Qdrant at {self.host}:{self.port}: {str(e)}"
            ) from e

        self._initialized = True

    def _get_collection_name(self, name: str) -> str:
        """Get full collection name with prefix."""
        return f"{self.collection_prefix}{name}"

    async def collection_exists(self, collection_name: str) -> bool:
        """
        Check if collection exists.

        Args:
            collection_name: Name of the collection (without prefix)

        Returns:
            True if collection exists, False otherwise
        """
        full_name = self._get_collection_name(collection_name)
        try:
            collections = self.client.get_collections().collections
            return any(c.name == full_name for c in collections)
        except Exception:
            return False

    async def ensure_collection(self, collection_name: str) -> None:
        """
        Ensure collection exists, creating it if necessary.

        Args:
            collection_name: Name of the collection (without prefix)

        Raises:
            ValueError: If collection schema not defined
            RuntimeError: If collection creation fails
        """
        if collection_name not in COLLECTION_SCHEMAS:
            raise ValueError(f"No schema defined for collection: {collection_name}")

        full_name = self._get_collection_name(collection_name)
        schema = COLLECTION_SCHEMAS[collection_name]

        if await self.collection_exists(collection_name):
            return

        try:
            # Map distance string to Qdrant enum
            distance_map = {
                'Cosine': self.Distance.COSINE,
                'Euclidean': self.Distance.EUCLID,
                'Dot': self.Distance.DOT
            }
            distance = distance_map.get(schema['distance'], self.Distance.COSINE)

            self.client.create_collection(
                collection_name=full_name,
                vectors_config=self.VectorParams(
                    size=schema['vector_size'],
                    distance=distance
                )
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create collection {full_name}: {str(e)}"
            ) from e

    async def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> None:
        """
        Upsert points into collection.

        Args:
            collection_name: Name of the collection (without prefix)
            points: List of points with format [{'id': ..., 'vector': ..., 'payload': ...}, ...]

        Raises:
            ValueError: If points format is invalid
            RuntimeError: If upsert fails
        """
        if not points:
            return

        from qdrant_client.models import PointStruct

        full_name = self._get_collection_name(collection_name)

        try:
            # Convert to Qdrant point format
            qdrant_points = []
            for point in points:
                if 'id' not in point or 'vector' not in point:
                    raise ValueError("Each point must have 'id' and 'vector' fields")

                qdrant_points.append(
                    PointStruct(
                        id=point['id'],
                        vector=point['vector'],
                        payload=point.get('payload', {})
                    )
                )

            # Upsert in batches
            batch_size = CONFIG.get('vector_store', {}).get('batch_size', 50)
            for i in range(0, len(qdrant_points), batch_size):
                batch = qdrant_points[i:i + batch_size]
                self.client.upsert(
                    collection_name=full_name,
                    points=batch
                )
        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(
                f"Failed to upsert points to {full_name}: {str(e)}"
            ) from e

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in collection.

        Args:
            collection_name: Name of the collection (without prefix)
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Optional filters (format: {'field': 'value'} or {'field': ['val1', 'val2']})

        Returns:
            List of results: [{'id': ..., 'score': ..., 'payload': ...}, ...]

        Raises:
            RuntimeError: If search fails
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

        full_name = self._get_collection_name(collection_name)

        try:
            # Build filter if provided
            query_filter = None
            if filters:
                # Validate filter fields against allowed fields
                allowed_fields = ALLOWED_FILTER_FIELDS.get(collection_name, set())
                for field in filters.keys():
                    if allowed_fields and field not in allowed_fields:
                        raise ValueError(
                            f"Invalid filter field '{field}' for collection '{collection_name}'. "
                            f"Allowed fields: {sorted(allowed_fields)}"
                        )

                conditions = []
                for field, value in filters.items():
                    if isinstance(value, list):
                        conditions.append(
                            FieldCondition(
                                key=field,
                                match=MatchAny(any=value)
                            )
                        )
                    else:
                        conditions.append(
                            FieldCondition(
                                key=field,
                                match=MatchValue(value=value)
                            )
                        )
                if conditions:
                    query_filter = Filter(must=conditions)

            # Execute search
            results = self.client.search(
                collection_name=full_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )

            # Convert to dict format
            return [
                {
                    'id': result.id,
                    'score': result.score,
                    'payload': result.payload
                }
                for result in results
            ]
        except Exception as e:
            raise RuntimeError(
                f"Failed to search {full_name}: {str(e)}"
            ) from e

    async def delete_points(
        self,
        collection_name: str,
        point_ids: List[Any]
    ) -> None:
        """
        Delete points from collection by ID.

        Args:
            collection_name: Name of the collection (without prefix)
            point_ids: List of point IDs to delete

        Raises:
            RuntimeError: If deletion fails
        """
        if not point_ids:
            return

        full_name = self._get_collection_name(collection_name)

        try:
            self.client.delete(
                collection_name=full_name,
                points_selector=point_ids
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to delete points from {full_name}: {str(e)}"
            ) from e


class MockVectorStore(BaseVectorStore):
    """
    Mock vector store for testing.

    Stores vectors in memory and uses cosine similarity for search.
    Provides deterministic results for testing without requiring Qdrant.
    """

    def __init__(self):
        """Initialize mock vector store with empty collections."""
        self.collections: Dict[str, Dict[Any, Tuple[List[float], Dict]]] = {}

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists in memory."""
        return collection_name in self.collections

    async def ensure_collection(self, collection_name: str) -> None:
        """Create collection in memory if it doesn't exist."""
        if collection_name not in COLLECTION_SCHEMAS:
            raise ValueError(f"No schema defined for collection: {collection_name}")

        if collection_name not in self.collections:
            self.collections[collection_name] = {}

    async def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> None:
        """
        Upsert points into in-memory collection.

        Args:
            collection_name: Name of the collection
            points: List of points

        Raises:
            ValueError: If points format is invalid
        """
        if not points:
            return

        if collection_name not in self.collections:
            await self.ensure_collection(collection_name)

        for point in points:
            if 'id' not in point or 'vector' not in point:
                raise ValueError("Each point must have 'id' and 'vector' fields")

            self.collections[collection_name][point['id']] = (
                point['vector'],
                point.get('payload', {})
            )

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using cosine similarity.

        Args:
            collection_name: Name of the collection
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filters: Optional filters on payload fields

        Returns:
            List of results sorted by similarity score
        """
        if collection_name not in self.collections:
            return []

        # Validate filter fields against allowed fields
        if filters:
            allowed_fields = ALLOWED_FILTER_FIELDS.get(collection_name, set())
            for field in filters.keys():
                if allowed_fields and field not in allowed_fields:
                    raise ValueError(
                        f"Invalid filter field '{field}' for collection '{collection_name}'. "
                        f"Allowed fields: {sorted(allowed_fields)}"
                    )

        results = []
        for point_id, (vector, payload) in self.collections[collection_name].items():
            # Apply filters if provided
            if filters:
                match = True
                for field, value in filters.items():
                    payload_value = payload.get(field)
                    if isinstance(value, list):
                        if payload_value not in value:
                            match = False
                            break
                    else:
                        if payload_value != value:
                            match = False
                            break
                if not match:
                    continue

            # Compute cosine similarity
            similarity = self._cosine_similarity(query_vector, vector)

            # Apply score threshold
            if score_threshold is not None and similarity < score_threshold:
                continue

            results.append({
                'id': point_id,
                'score': similarity,
                'payload': payload.copy()
            })

        # Sort by score descending and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

    async def delete_points(
        self,
        collection_name: str,
        point_ids: List[Any]
    ) -> None:
        """Delete points from in-memory collection."""
        if collection_name not in self.collections:
            return

        for point_id in point_ids:
            self.collections[collection_name].pop(point_id, None)

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score between -1 and 1
        """
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have same dimension")

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        similarity = dot_product / (magnitude1 * magnitude2)
        return max(-1.0, min(1.0, similarity))


# Vector store initialization and operations

async def initialize_collections(vector_store: BaseVectorStore) -> None:
    """
    Initialize all required collections in vector store.

    Args:
        vector_store: Vector store instance

    Raises:
        RuntimeError: If collection creation fails
    """
    for collection_name in COLLECTION_SCHEMAS.keys():
        await vector_store.ensure_collection(collection_name)


async def index_bullet(
    bullet: Any,
    embedding_service: Any,
    vector_store: BaseVectorStore
) -> None:
    """
    Index a single bullet point in vector store.

    Args:
        bullet: Bullet model instance (with id, text, user_id, etc.)
        embedding_service: Embedding service instance
        vector_store: Vector store instance

    Raises:
        RuntimeError: If indexing fails
    """
    # Skip retired bullets if configured
    if bullet.retired and not CONFIG.get('embeddings', {}).get('index_retired_bullets', False):
        return

    # Generate embedding if not already present
    if bullet.embedding:
        embedding = bullet.embedding
    else:
        embedding = await embedding_service.embed_bullet(bullet.text)

    # Build payload
    payload = {
        'bullet_id': bullet.id,
        'user_id': bullet.user_id,
        'experience_id': bullet.experience_id,
        'engagement_id': bullet.engagement_id,
        'text': bullet.text,
        'tags': bullet.tags or [],
        'seniority_level': bullet.seniority_level,
        'bullet_type': bullet.bullet_type,
        'importance': bullet.importance,
        'ai_first_choice': bullet.ai_first_choice,
        'retired': bullet.retired,
        'usage_count': bullet.usage_count
    }

    # Upsert to vector store
    await vector_store.upsert_points(
        collection_name=COLLECTION_BULLETS,
        points=[{
            'id': bullet.id,
            'vector': embedding,
            'payload': payload
        }]
    )


async def index_all_bullets(
    db: Any,
    embedding_service: Any,
    vector_store: BaseVectorStore,
    user_id: Optional[int] = None
) -> int:
    """
    Index all bullets for a user (or all users) in vector store.

    Args:
        db: Database session
        embedding_service: Embedding service instance
        vector_store: Vector store instance
        user_id: Optional user ID to filter bullets

    Returns:
        Number of bullets indexed

    Raises:
        RuntimeError: If indexing fails
    """
    from db.models import Bullet

    # Build query
    query = db.query(Bullet)
    if user_id is not None:
        query = query.filter(Bullet.user_id == user_id)

    # Filter retired bullets if configured
    if not CONFIG.get('embeddings', {}).get('index_retired_bullets', False):
        query = query.filter(Bullet.retired == False)

    bullets = query.all()

    # Index each bullet
    indexed_count = 0
    batch_size = CONFIG.get('vector_store', {}).get('batch_size', 50)
    points_batch = []

    for bullet in bullets:
        # Generate embedding if needed
        if bullet.embedding:
            embedding = bullet.embedding
        else:
            embedding = await embedding_service.embed_bullet(bullet.text)
            bullet.embedding = embedding
            db.add(bullet)

        # Build payload
        payload = {
            'bullet_id': bullet.id,
            'user_id': bullet.user_id,
            'experience_id': bullet.experience_id,
            'engagement_id': bullet.engagement_id,
            'text': bullet.text,
            'tags': bullet.tags or [],
            'seniority_level': bullet.seniority_level,
            'bullet_type': bullet.bullet_type,
            'importance': bullet.importance,
            'ai_first_choice': bullet.ai_first_choice,
            'retired': bullet.retired,
            'usage_count': bullet.usage_count
        }

        points_batch.append({
            'id': bullet.id,
            'vector': embedding,
            'payload': payload
        })

        # Upsert in batches
        if len(points_batch) >= batch_size:
            await vector_store.upsert_points('bullets', points_batch)
            indexed_count += len(points_batch)
            points_batch = []

    # Upsert remaining points
    if points_batch:
        await vector_store.upsert_points('bullets', points_batch)
        indexed_count += len(points_batch)

    # Commit database changes
    db.commit()

    return indexed_count


async def index_job_profile(
    job_profile: Any,
    embedding_service: Any,
    vector_store: BaseVectorStore
) -> None:
    """
    Index a job profile in vector store.

    Args:
        job_profile: JobProfile model instance
        embedding_service: Embedding service instance
        vector_store: Vector store instance

    Raises:
        RuntimeError: If indexing fails
    """
    # Generate embedding if not already present
    if job_profile.embedding:
        embedding = job_profile.embedding
    else:
        embedding = await embedding_service.embed_job_profile(
            title=job_profile.job_title,
            responsibilities=job_profile.responsibilities or '',
            requirements=job_profile.requirements or '',
            nice_to_haves=job_profile.nice_to_haves
        )

    # Build payload
    payload = {
        'job_profile_id': job_profile.id,
        'user_id': job_profile.user_id,
        'company_id': job_profile.company_id,
        'job_title': job_profile.job_title,
        'location': job_profile.location,
        'seniority': job_profile.seniority,
        'job_type_tags': job_profile.job_type_tags or [],
        'responsibilities': job_profile.responsibilities or '',
        'requirements': job_profile.requirements or '',
        'nice_to_haves': job_profile.nice_to_haves or ''
    }

    # Upsert to vector store
    await vector_store.upsert_points(
        collection_name=COLLECTION_JOBS,
        points=[{
            'id': job_profile.id,
            'vector': embedding,
            'payload': payload
        }]
    )


async def search_similar_bullets(
    query_text: str,
    embedding_service: Any,
    vector_store: BaseVectorStore,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for bullets similar to query text.

    Args:
        query_text: Text to search for
        embedding_service: Embedding service instance
        vector_store: Vector store instance
        limit: Maximum number of results
        filters: Optional filters (e.g., {'tags': ['ai_governance'], 'importance': 'high'})

    Returns:
        List of matching bullets with scores

    Raises:
        RuntimeError: If search fails
    """
    # Generate query embedding
    query_embedding = await embedding_service.generate_embedding(query_text)

    # Search vector store
    results = await vector_store.search(
        collection_name=COLLECTION_BULLETS,
        query_vector=query_embedding,
        limit=limit,
        score_threshold=CONFIG.get('embeddings', {}).get('similarity_threshold', 0.60),
        filters=filters
    )

    return results


async def search_similar_jobs(
    job_text: str,
    embedding_service: Any,
    vector_store: BaseVectorStore,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for job profiles similar to given text.

    Args:
        job_text: Job description text to search for
        embedding_service: Embedding service instance
        vector_store: Vector store instance
        limit: Maximum number of results

    Returns:
        List of matching job profiles with scores

    Raises:
        RuntimeError: If search fails
    """
    # Generate query embedding
    query_embedding = await embedding_service.generate_embedding(job_text)

    # Search vector store
    results = await vector_store.search(
        collection_name=COLLECTION_JOBS,
        query_vector=query_embedding,
        limit=limit,
        score_threshold=CONFIG.get('embeddings', {}).get('similarity_threshold', 0.60)
    )

    return results


async def search_bullets_for_job(
    job_profile: Any,
    embedding_service: Any,
    vector_store: BaseVectorStore,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for bullets that match a job profile.

    Uses job profile's embedding to find most relevant resume bullets.

    Args:
        job_profile: JobProfile model instance
        embedding_service: Embedding service instance
        vector_store: Vector store instance
        limit: Maximum number of results

    Returns:
        List of matching bullets with scores

    Raises:
        RuntimeError: If search fails
    """
    # Get or generate job profile embedding
    if job_profile.embedding:
        query_embedding = job_profile.embedding
    else:
        query_embedding = await embedding_service.embed_job_profile(
            title=job_profile.job_title,
            responsibilities=job_profile.responsibilities or '',
            requirements=job_profile.requirements or '',
            nice_to_haves=job_profile.nice_to_haves
        )

    # Search vector store
    results = await vector_store.search(
        collection_name=COLLECTION_BULLETS,
        query_vector=query_embedding,
        limit=limit,
        score_threshold=CONFIG.get('embeddings', {}).get('similarity_threshold', 0.60)
    )

    return results


async def index_approved_output(
    approved_output: Any,  # ApprovedOutput model instance
    embedding_service: Any,
    vector_store: BaseVectorStore
) -> None:
    """
    Index an approved output in vector store for similarity search.

    PII Handling: Sanitizes personal identifiers before storing in the vector
    store payload to prevent PII leakage in logs and search results.

    Args:
        approved_output: ApprovedOutput model instance
        embedding_service: Embedding service instance
        vector_store: Vector store instance

    Raises:
        RuntimeError: If indexing fails
    """
    from utils.pii_sanitizer import sanitize_personal_identifiers

    # Generate embedding if not present
    if approved_output.embedding:
        embedding = approved_output.embedding
    else:
        embedding = await embedding_service.generate_embedding(approved_output.original_text)

    # Sanitize text before storing in payload
    sanitized_text = sanitize_personal_identifiers(approved_output.original_text)

    # Build payload matching COLLECTION_SCHEMAS['approved_outputs']
    payload = {
        'output_id': approved_output.id,
        'user_id': approved_output.user_id,
        'application_id': approved_output.application_id,
        'output_type': approved_output.output_type,
        'text': sanitized_text,  # Store sanitized version
        'quality_score': approved_output.quality_score,
        'created_at': approved_output.created_at.isoformat() if approved_output.created_at else None
    }

    # Upsert to vector store
    await vector_store.upsert_points(
        collection_name=COLLECTION_APPROVED_OUTPUTS,
        points=[{
            'id': approved_output.id,
            'vector': embedding,
            'payload': payload
        }]
    )


# Factory function
def create_vector_store(use_mock: bool = False) -> BaseVectorStore:
    """
    Factory function to create appropriate vector store.

    Args:
        use_mock: If True, return MockVectorStore; otherwise QdrantVectorStore

    Returns:
        Vector store instance

    Example:
        >>> # For production
        >>> store = create_vector_store(use_mock=False)
        >>>
        >>> # For testing
        >>> store = create_vector_store(use_mock=True)
    """
    if use_mock:
        return MockVectorStore()
    else:
        return QdrantVectorStore()
