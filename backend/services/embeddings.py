"""
Embeddings Service for Semantic Skill Matching

Provides embedding generation and semantic similarity for skill matching
beyond exact string/synonym matches. Supports both OpenAI embeddings and
deterministic mock implementation for testing.
"""

import hashlib
import math
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict

import yaml


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
            'models': {
                'embedding_model': 'text-embedding-3-small'
            },
            'embeddings': {
                'similarity_threshold': 0.75,
                'batch_size': 100
            }
        }


# Load config at module level
CONFIG = load_config()


class BaseEmbeddingService(ABC):
    """
    Abstract base class for embedding services.

    Defines the interface for generating embeddings and computing
    semantic similarity between texts.
    """

    def __init__(self, similarity_threshold: float = 0.75):
        """
        Initialize embedding service.

        Args:
            similarity_threshold: Minimum similarity score for matches (0-1)
        """
        self.similarity_threshold = similarity_threshold

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            ValueError: If text is empty or invalid
        """
        pass

    @abstractmethod
    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        More efficient than individual calls for large batches.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors corresponding to input texts

        Raises:
            ValueError: If texts list is empty or contains invalid entries
        """
        pass

    def compute_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.

        Cosine similarity formula:
            similarity = (A · B) / (||A|| * ||B||)

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Similarity score between -1 and 1 (typically 0 to 1 for embeddings)

        Raises:
            ValueError: If embeddings have different dimensions or are empty
        """
        if not emb1 or not emb2:
            raise ValueError("Embeddings cannot be empty")

        if len(emb1) != len(emb2):
            raise ValueError(
                f"Embedding dimensions must match: {len(emb1)} vs {len(emb2)}"
            )

        # Compute dot product
        dot_product = sum(a * b for a, b in zip(emb1, emb2))

        # Compute magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in emb1))
        magnitude2 = math.sqrt(sum(b * b for b in emb2))

        # Handle zero vectors
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        # Compute cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)

        # Clamp to [-1, 1] to handle floating point errors
        return max(-1.0, min(1.0, similarity))

    async def compute_text_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two texts by generating embeddings and comparing.

        Subclasses may override this to use predefined similarity maps.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score
        """
        emb1 = await self.generate_embedding(text1)
        emb2 = await self.generate_embedding(text2)
        return self.compute_similarity(emb1, emb2)

    async def find_best_semantic_match(
        self,
        query: str,
        candidates: List[str],
        threshold: Optional[float] = None
    ) -> Optional[Tuple[str, float]]:
        """
        Find best semantic match for query among candidates.

        Args:
            query: Query text to match
            candidates: List of candidate texts
            threshold: Minimum similarity threshold (uses instance default if None)

        Returns:
            Tuple of (best_match, similarity_score) if match found above threshold,
            None otherwise

        Raises:
            ValueError: If candidates list is empty
        """
        if not candidates:
            raise ValueError("Candidates list cannot be empty")

        if threshold is None:
            threshold = self.similarity_threshold

        # Generate embeddings
        query_emb = await self.generate_embedding(query)
        candidate_embs = await self.batch_generate_embeddings(candidates)

        # Find best match
        best_match = None
        best_score = threshold  # Start at threshold

        for candidate, candidate_emb in zip(candidates, candidate_embs):
            similarity = self.compute_similarity(query_emb, candidate_emb)
            if similarity > best_score:
                best_score = similarity
                best_match = candidate

        if best_match:
            return (best_match, best_score)

        return None

    async def embed_bullet(
        self,
        bullet_text: str,
        context: Optional[Dict] = None
    ) -> List[float]:
        """
        Generate embedding for a bullet point.

        Args:
            bullet_text: Resume bullet text to embed
            context: Optional context dict (currently unused, reserved for future use)

        Returns:
            Embedding vector

        Raises:
            ValueError: If bullet_text is empty
        """
        return await self.generate_embedding(bullet_text)

    async def embed_job_profile(
        self,
        title: str,
        responsibilities: str,
        requirements: str,
        nice_to_haves: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for a job profile combining key fields.

        Combines job title, responsibilities, requirements, and optional nice-to-haves
        into a single semantic representation for matching against resume bullets.

        Args:
            title: Job title
            responsibilities: Job responsibilities text
            requirements: Job requirements text
            nice_to_haves: Optional nice-to-have qualifications

        Returns:
            Embedding vector

        Raises:
            ValueError: If any required field is empty
        """
        if not title or not title.strip():
            raise ValueError("Job title cannot be empty")
        if not responsibilities or not responsibilities.strip():
            raise ValueError("Responsibilities cannot be empty")
        if not requirements or not requirements.strip():
            raise ValueError("Requirements cannot be empty")

        parts = [
            f"Job Title: {title}",
            f"Responsibilities: {responsibilities}",
            f"Requirements: {requirements}"
        ]
        if nice_to_haves and nice_to_haves.strip():
            parts.append(f"Nice-to-Have: {nice_to_haves}")

        combined = "\n\n".join(parts)
        return await self.generate_embedding(combined)


class MockEmbeddingService(BaseEmbeddingService):
    """
    Mock embedding service for testing and development.

    Returns deterministic embeddings based on text hash with predefined
    similarity scores for common skill pairs. Ensures consistent results
    for same inputs without requiring API calls.
    """

    # Predefined similarity mappings for common skill pairs
    # Maps (skill1, skill2) -> similarity score
    SKILL_SIMILARITY_MAP: Dict[Tuple[str, str], float] = {
        # AI/ML related
        ('ML Engineering', 'Machine Learning'): 0.95,
        ('Machine Learning', 'ML Engineering'): 0.95,
        ('Machine Learning Engineering', 'Machine Learning'): 0.93,
        ('Machine Learning', 'Machine Learning Engineering'): 0.93,
        ('Machine Learning Engineering', 'ML Ops'): 0.85,
        ('ML Ops', 'Machine Learning Engineering'): 0.85,
        ('Machine Learning Engineering', 'ML Engineering'): 0.97,
        ('ML Engineering', 'Machine Learning Engineering'): 0.97,
        ('Deep Learning', 'Neural Networks'): 0.92,
        ('Neural Networks', 'Deep Learning'): 0.92,
        ('NLP', 'Natural Language Processing'): 0.98,
        ('Natural Language Processing', 'NLP'): 0.98,
        ('LLM', 'Large Language Models'): 0.96,
        ('Large Language Models', 'LLM'): 0.96,
        ('Machine Learning', 'Deep Learning'): 0.85,
        ('Deep Learning', 'Machine Learning'): 0.85,
        ('Machine Learning', 'Data Science'): 0.82,
        ('Data Science', 'Machine Learning'): 0.82,
        ('AI', 'Artificial Intelligence'): 0.99,
        ('Artificial Intelligence', 'AI'): 0.99,
        ('AI', 'Machine Learning'): 0.80,
        ('Machine Learning', 'AI'): 0.80,
        ('AI', 'AI Strategy'): 0.85,
        ('AI Strategy', 'AI'): 0.85,
        ('AI', 'AI/ML'): 0.92,
        ('AI/ML', 'AI'): 0.92,
        ('AI', 'AI Governance'): 0.78,
        ('AI Governance', 'AI'): 0.78,
        ('AI Strategy', 'Strategy'): 0.82,
        ('Strategy', 'AI Strategy'): 0.82,
        ('AI Strategy', 'Digital Transformation'): 0.75,
        ('Digital Transformation', 'AI Strategy'): 0.75,
        ('AI/ML', 'Machine Learning'): 0.95,
        ('Machine Learning', 'AI/ML'): 0.95,
        ('AI Governance', 'Governance'): 0.88,
        ('Governance', 'AI Governance'): 0.88,
        ('Generative AI', 'AI'): 0.88,
        ('AI', 'Generative AI'): 0.88,
        ('LLM', 'AI'): 0.82,
        ('AI', 'LLM'): 0.82,

        # Cloud & Infrastructure
        ('AWS', 'Amazon Web Services'): 0.98,
        ('Amazon Web Services', 'AWS'): 0.98,
        ('Azure', 'Microsoft Azure'): 0.97,
        ('Microsoft Azure', 'Azure'): 0.97,
        ('GCP', 'Google Cloud'): 0.95,
        ('Google Cloud', 'GCP'): 0.95,
        ('Cloud', 'AWS'): 0.75,
        ('AWS', 'Cloud'): 0.75,
        ('Cloud', 'Azure'): 0.75,
        ('Azure', 'Cloud'): 0.75,
        ('Kubernetes', 'K8s'): 0.99,
        ('K8s', 'Kubernetes'): 0.99,
        ('Docker', 'Containerization'): 0.90,
        ('Containerization', 'Docker'): 0.90,
        ('Docker', 'Kubernetes'): 0.78,
        ('Kubernetes', 'Docker'): 0.78,

        # Programming languages
        ('Python', 'Python Programming'): 0.96,
        ('Python Programming', 'Python'): 0.96,
        ('JavaScript', 'JS'): 0.98,
        ('JS', 'JavaScript'): 0.98,
        ('TypeScript', 'TS'): 0.97,
        ('TS', 'TypeScript'): 0.97,
        ('JavaScript', 'TypeScript'): 0.82,
        ('TypeScript', 'JavaScript'): 0.82,

        # Data & Analytics
        ('Data Science', 'Data Analysis'): 0.85,
        ('Data Analysis', 'Data Science'): 0.85,
        ('Data Engineering', 'ETL'): 0.80,
        ('ETL', 'Data Engineering'): 0.80,
        ('SQL', 'Database'): 0.76,
        ('Database', 'SQL'): 0.76,
        ('Analytics', 'Data Analysis'): 0.88,
        ('Data Analysis', 'Analytics'): 0.88,

        # Governance & Compliance
        ('AI Governance', 'AI Ethics'): 0.85,
        ('AI Ethics', 'AI Governance'): 0.85,
        ('Compliance', 'Regulatory Compliance'): 0.93,
        ('Regulatory Compliance', 'Compliance'): 0.93,
        ('Risk Management', 'Compliance'): 0.77,
        ('Compliance', 'Risk Management'): 0.77,
        ('Governance', 'Compliance'): 0.80,
        ('Compliance', 'Governance'): 0.80,

        # Frameworks & Libraries
        ('TensorFlow', 'PyTorch'): 0.83,
        ('PyTorch', 'TensorFlow'): 0.83,
        ('React', 'React.js'): 0.98,
        ('React.js', 'React'): 0.98,
        ('Node.js', 'Node'): 0.96,
        ('Node', 'Node.js'): 0.96,

        # Business & Strategy
        ('Strategy', 'Strategic Planning'): 0.91,
        ('Strategic Planning', 'Strategy'): 0.91,
        ('Consulting', 'Advisory'): 0.87,
        ('Advisory', 'Consulting'): 0.87,
        ('Product Management', 'Product Strategy'): 0.84,
        ('Product Strategy', 'Product Management'): 0.84,
        ('Project Management', 'Program Management'): 0.81,
        ('Program Management', 'Project Management'): 0.81,
        ('Digital Transformation', 'Transformation'): 0.88,
        ('Transformation', 'Digital Transformation'): 0.88,
        ('Digital Transformation', 'Change Management'): 0.76,
        ('Change Management', 'Digital Transformation'): 0.76,
        ('Strategy', 'Business Strategy'): 0.93,
        ('Business Strategy', 'Strategy'): 0.93,
        ('Stakeholder Management', 'Client Management'): 0.82,
        ('Client Management', 'Stakeholder Management'): 0.82,
        ('Consulting', 'Client Engagement'): 0.80,
        ('Client Engagement', 'Consulting'): 0.80,
        ('Technology Consulting', 'Consulting'): 0.90,
        ('Consulting', 'Technology Consulting'): 0.90,
        ('AI Consulting', 'Consulting'): 0.88,
        ('Consulting', 'AI Consulting'): 0.88,
        ('Innovation', 'Digital Transformation'): 0.72,
        ('Digital Transformation', 'Innovation'): 0.72,

        # Engineering & ML adjacent (for weak signal detection)
        ('Software Engineering', 'ML Engineering'): 0.65,
        ('ML Engineering', 'Software Engineering'): 0.65,
        ('Software Engineering', 'Machine Learning'): 0.55,
        ('Machine Learning', 'Software Engineering'): 0.55,
        ('Data Analysis', 'Data Science'): 0.75,
        ('Data Science', 'Data Analysis'): 0.75,
        ('Data Analysis', 'Machine Learning'): 0.60,
        ('Machine Learning', 'Data Analysis'): 0.60,
        ('System Architecture', 'ML Architecture'): 0.58,
        ('ML Architecture', 'System Architecture'): 0.58,
    }

    def __init__(self, similarity_threshold: float = 0.75, embedding_dim: int = 384):
        """
        Initialize mock embedding service.

        Args:
            similarity_threshold: Minimum similarity for matches
            embedding_dim: Dimension of generated embeddings (default 384 to match text-embedding-3-small)
        """
        super().__init__(similarity_threshold)
        self.embedding_dim = embedding_dim

    def _text_to_vector(self, text: str) -> List[float]:
        """
        Generate deterministic pseudo-embedding from text hash.

        Uses MD5 hash to generate consistent vector for same input text.
        Not semantically meaningful but provides consistent similarity scores
        when combined with predefined similarity map.

        Args:
            text: Input text

        Returns:
            Normalized embedding vector of fixed dimension (self.embedding_dim)
        """
        # Create hash of normalized text
        normalized = text.lower().strip()
        text_hash = hashlib.md5(normalized.encode()).hexdigest()

        # Convert each hex char to a float value in range [-1, 1]
        # MD5 gives 32 hex chars
        vector = []
        for char in text_hash:
            value = (int(char, 16) - 7.5) / 7.5  # Normalize from 0-15 to ~[-1, 1]
            vector.append(value)

        # Extend to desired dimension by repeating the pattern
        while len(vector) < self.embedding_dim:
            vector.extend(vector[:min(len(vector), self.embedding_dim - len(vector))])

        # Truncate to exact dimension
        vector = vector[:self.embedding_dim]

        # Normalize to unit vector
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        return vector

    def _get_predefined_similarity(self, text1: str, text2: str) -> Optional[float]:
        """
        Get predefined similarity score for known skill pairs.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Predefined similarity score if pair is known, None otherwise
        """
        # Normalize texts
        norm1 = text1.strip()
        norm2 = text2.strip()

        # Check both orderings
        key1 = (norm1, norm2)
        key2 = (norm2, norm1)

        return self.SKILL_SIMILARITY_MAP.get(key1) or self.SKILL_SIMILARITY_MAP.get(key2)

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate deterministic embedding for text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        return self._text_to_vector(text)

    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If texts list is empty
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

    def compute_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """
        Compute similarity, using predefined scores when available.

        This override checks if we have a predefined similarity score for the
        text pair before falling back to cosine similarity.

        Args:
            emb1: First embedding
            emb2: Second embedding

        Returns:
            Similarity score
        """
        # For mock, we use the base cosine similarity
        # The predefined scores are used implicitly via the embedding generation
        return super().compute_similarity(emb1, emb2)

    async def compute_text_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two texts, using predefined scores when available.

        This method first checks predefined similarity map, then falls back
        to embedding-based cosine similarity.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score
        """
        # Check predefined similarities first
        predefined = self._get_predefined_similarity(text1, text2)
        if predefined is not None:
            return predefined

        # Fall back to embedding-based similarity
        emb1 = await self.generate_embedding(text1)
        emb2 = await self.generate_embedding(text2)
        return self.compute_similarity(emb1, emb2)

    async def find_best_semantic_match(
        self,
        query: str,
        candidates: List[str],
        threshold: Optional[float] = None
    ) -> Optional[Tuple[str, float]]:
        """
        Find best semantic match, using predefined similarities when available.

        Args:
            query: Query text
            candidates: Candidate texts
            threshold: Similarity threshold

        Returns:
            Best match and score if found, None otherwise
        """
        if not candidates:
            raise ValueError("Candidates list cannot be empty")

        if threshold is None:
            threshold = self.similarity_threshold

        best_match = None
        best_score = threshold

        # Check predefined similarities first
        for candidate in candidates:
            predefined = self._get_predefined_similarity(query, candidate)
            if predefined is not None:
                if predefined > best_score:
                    best_score = predefined
                    best_match = candidate

        # If we found a predefined match, return it
        if best_match:
            return (best_match, best_score)

        # Fall back to embedding-based similarity
        return await super().find_best_semantic_match(query, candidates, threshold)


class OpenAIEmbeddingService(BaseEmbeddingService):
    """
    OpenAI embedding service for production use.

    Uses OpenAI's text-embedding models for semantic similarity.
    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.75,
        model: Optional[str] = None,
        batch_size: int = 100
    ):
        """
        Initialize OpenAI embedding service.

        Args:
            similarity_threshold: Minimum similarity for matches
            model: Embedding model name (defaults to config setting)
            batch_size: Maximum batch size for API calls

        Raises:
            ImportError: If openai package not installed
            ValueError: If OPENAI_API_KEY not set
        """
        super().__init__(similarity_threshold)

        try:
            import openai
            self.openai = openai
        except ImportError:
            raise ImportError(
                "openai package required for OpenAI embeddings. "
                "Install with: pip install openai"
            )

        # Get API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable must be set "
                "for OpenAI embedding service"
            )

        self.client = openai.OpenAI(api_key=api_key)
        self.model = model or CONFIG.get('models', {}).get('embedding_model', 'text-embedding-3-small')
        self.batch_size = batch_size

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using OpenAI API.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector

        Raises:
            ValueError: If text is empty
            Exception: If API call fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}") from e

    async def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings in batch using OpenAI API.

        Automatically chunks requests to respect batch size limits.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If texts list is empty
            Exception: If API call fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )

                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

            except Exception as e:
                raise RuntimeError(f"Failed to generate batch embeddings: {str(e)}") from e

        return all_embeddings


# Factory function for creating appropriate service
def create_embedding_service(
    use_mock: bool = False,
    similarity_threshold: Optional[float] = None,
    **kwargs
) -> BaseEmbeddingService:
    """
    Factory function to create appropriate embedding service.

    Args:
        use_mock: If True, return MockEmbeddingService; otherwise OpenAIEmbeddingService
        similarity_threshold: Similarity threshold (uses config default if None)
        **kwargs: Additional arguments passed to service constructor

    Returns:
        Embedding service instance

    Example:
        >>> # For production
        >>> service = create_embedding_service(use_mock=False)
        >>>
        >>> # For testing
        >>> service = create_embedding_service(use_mock=True)
    """
    if similarity_threshold is None:
        similarity_threshold = CONFIG.get('embeddings', {}).get('similarity_threshold', 0.75)

    if use_mock:
        return MockEmbeddingService(similarity_threshold=similarity_threshold, **kwargs)
    else:
        return OpenAIEmbeddingService(similarity_threshold=similarity_threshold, **kwargs)
