"""
Output Retrieval Service

Retrieves similar approved outputs for reference during generation.
Enables learning from successful historical outputs.
"""

import logging
from typing import List, Optional, Dict, Any

from services.vector_store import (
    BaseVectorStore,
    COLLECTION_APPROVED_OUTPUTS,
    SIMILARITY_THRESHOLD,
)
from services.embeddings import BaseEmbeddingService


logger = logging.getLogger(__name__)


async def retrieve_similar_outputs(
    query_text: str,
    embedding_service: BaseEmbeddingService,
    vector_store: BaseVectorStore,
    user_id: int,
    output_type: Optional[str] = None,
    limit: int = 5,
    min_quality_score: Optional[float] = None,
    similarity_threshold: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve similar approved outputs for a given query.

    Args:
        query_text: Text to find similar outputs for
        embedding_service: Embedding service instance
        vector_store: Vector store instance
        user_id: User ID to filter results
        output_type: Optional filter by output type ('resume_bullet', 'cover_letter_paragraph', etc.)
        limit: Maximum number of results
        min_quality_score: Minimum quality score filter (0.0-1.0)
        similarity_threshold: Minimum similarity score (defaults to config)

    Returns:
        List of similar outputs with format:
        [{'id': ..., 'score': ..., 'payload': {'text': ..., 'quality_score': ..., ...}}]
    """
    if not query_text or not query_text.strip():
        logger.warning("Empty query text provided to retrieve_similar_outputs")
        return []

    # Use default threshold if not specified
    threshold = similarity_threshold if similarity_threshold is not None else SIMILARITY_THRESHOLD

    # Generate query embedding
    try:
        query_embedding = await embedding_service.generate_embedding(query_text)
    except Exception as e:
        logger.error(f"Failed to generate embedding for query: {e}")
        return []

    # Build filters
    filters: Dict[str, Any] = {'user_id': user_id}
    if output_type:
        filters['output_type'] = output_type

    # Search vector store
    try:
        results = await vector_store.search(
            collection_name=COLLECTION_APPROVED_OUTPUTS,
            query_vector=query_embedding,
            limit=limit * 2 if min_quality_score else limit,  # Get extra for quality filtering
            score_threshold=threshold,
            filters=filters
        )
    except Exception as e:
        logger.error(f"Vector store search failed: {e}")
        return []

    # Filter by quality score if specified
    if min_quality_score is not None:
        results = [
            r for r in results
            if (r.get('payload', {}).get('quality_score') or 0) >= min_quality_score
        ]

    # Limit to requested count
    return results[:limit]


async def retrieve_similar_bullets(
    job_profile: Any,  # JobProfile model instance
    embedding_service: BaseEmbeddingService,
    vector_store: BaseVectorStore,
    user_id: int,
    limit: int = 10,
    min_quality_score: float = 0.7
) -> List[Dict[str, Any]]:
    """
    Retrieve similar approved bullet points for a job profile.

    Uses job profile content to find relevant historical bullets.

    Args:
        job_profile: JobProfile model instance
        embedding_service: Embedding service instance
        vector_store: Vector store instance
        user_id: User ID to filter results
        limit: Maximum number of results
        min_quality_score: Minimum quality score filter

    Returns:
        List of similar bullets with scores
    """
    # Build query from job profile
    query_parts = [job_profile.job_title]
    if job_profile.requirements:
        query_parts.append(job_profile.requirements[:500])  # Limit for embedding
    if job_profile.responsibilities:
        query_parts.append(job_profile.responsibilities[:500])

    query_text = "\n".join(query_parts)

    return await retrieve_similar_outputs(
        query_text=query_text,
        embedding_service=embedding_service,
        vector_store=vector_store,
        user_id=user_id,
        output_type='resume_bullet',
        limit=limit,
        min_quality_score=min_quality_score,
        similarity_threshold=0.60  # Lower threshold for bullets
    )


async def retrieve_similar_summaries(
    job_profile: Any,
    embedding_service: BaseEmbeddingService,
    vector_store: BaseVectorStore,
    user_id: int,
    limit: int = 3,
    min_quality_score: float = 0.75
) -> List[Dict[str, Any]]:
    """
    Retrieve similar approved professional summaries for a job profile.

    Args:
        job_profile: JobProfile model instance
        embedding_service: Embedding service instance
        vector_store: Vector store instance
        user_id: User ID to filter results
        limit: Maximum number of results
        min_quality_score: Minimum quality score filter

    Returns:
        List of similar summaries with scores
    """
    query_text = f"{job_profile.job_title}\n{job_profile.requirements or ''}"

    return await retrieve_similar_outputs(
        query_text=query_text,
        embedding_service=embedding_service,
        vector_store=vector_store,
        user_id=user_id,
        output_type='professional_summary',
        limit=limit,
        min_quality_score=min_quality_score
    )


async def retrieve_similar_cover_letter_paragraphs(
    job_profile: Any,
    embedding_service: BaseEmbeddingService,
    vector_store: BaseVectorStore,
    user_id: int,
    limit: int = 5,
    min_quality_score: float = 0.70
) -> List[Dict[str, Any]]:
    """
    Retrieve similar approved cover letter paragraphs for a job profile.

    Args:
        job_profile: JobProfile model instance
        embedding_service: Embedding service instance
        vector_store: Vector store instance
        user_id: User ID to filter results
        limit: Maximum number of results
        min_quality_score: Minimum quality score filter

    Returns:
        List of similar paragraphs with scores
    """
    # Include company name if available for better matching
    query_parts = [job_profile.job_title]
    if hasattr(job_profile, 'company') and job_profile.company:
        query_parts.append(job_profile.company.name if hasattr(job_profile.company, 'name') else str(job_profile.company))
    if job_profile.requirements:
        query_parts.append(job_profile.requirements[:300])

    query_text = "\n".join(query_parts)

    return await retrieve_similar_outputs(
        query_text=query_text,
        embedding_service=embedding_service,
        vector_store=vector_store,
        user_id=user_id,
        output_type='cover_letter_paragraph',
        limit=limit,
        min_quality_score=min_quality_score
    )


def format_examples_for_prompt(
    similar_outputs: List[Dict[str, Any]],
    max_examples: int = 3,
    include_quality_score: bool = True
) -> str:
    """
    Format similar outputs for inclusion in an LLM prompt.

    PII Handling: Text retrieved from vector store payloads is already
    sanitized (personal identifiers replaced with placeholders), so it's
    safe to include in prompts sent to LLMs.

    Args:
        similar_outputs: List of similar outputs from retrieval
        max_examples: Maximum number of examples to include
        include_quality_score: Whether to show quality scores

    Returns:
        Formatted string for prompt inclusion
    """
    if not similar_outputs:
        return ""

    examples = similar_outputs[:max_examples]
    lines = ["**Reference Examples (Approved):**"]

    for idx, example in enumerate(examples, 1):
        text = example.get('payload', {}).get('text', '')
        quality = example.get('payload', {}).get('quality_score')
        similarity = example.get('score', 0)

        if include_quality_score and quality is not None:
            lines.append(f"{idx}. (Quality: {quality:.0%}, Similarity: {similarity:.0%})")
        else:
            lines.append(f"{idx}. (Similarity: {similarity:.0%})")

        # Truncate long examples
        if len(text) > 500:
            text = text[:497] + "..."
        lines.append(f"   {text}")
        lines.append("")

    lines.append("Use these as style references, but create unique content.\n")

    return "\n".join(lines)
