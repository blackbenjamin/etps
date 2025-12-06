"""
Outputs Router

FastAPI endpoints for approved output management and retrieval.

Note on service creation: The embedding and vector store services use singleton patterns
and are thread-safe. While created synchronously in async endpoints, this is acceptable
for single-user CLI use. For high-concurrency production, these should be initialized
at app startup and injected via FastAPI dependencies.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal

from db.database import get_db
from db.models import ApprovedOutput, User, Application, JobProfile
from schemas.approved_output import (
    ApproveOutputRequest,
    ApproveOutputResponse,
    SimilarOutput,
    SimilarOutputsResponse
)
from services.vector_store import (
    index_approved_output,
    create_vector_store,
    COLLECTION_APPROVED_OUTPUTS
)
from services.embeddings import create_embedding_service


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/approve", response_model=ApproveOutputResponse, status_code=status.HTTP_201_CREATED)
async def approve_output(
    request: ApproveOutputRequest,
    db: Session = Depends(get_db)
) -> ApproveOutputResponse:
    """
    Approve and store an output for future reference.

    Stores the approved output in the database with optional context metadata
    and quality score. Also indexes the output in the vector store for
    semantic similarity search.

    **Request Body:**
    - `user_id`: User ID (required)
    - `output_type`: Type of output - 'resume_bullet', 'cover_letter_paragraph',
      'professional_summary', 'full_resume', or 'full_cover_letter'
    - `original_text`: The approved output text (required, 1-10000 chars)
    - `application_id`: Associated application ID (optional)
    - `job_profile_id`: Associated job profile ID (optional)
    - `context_metadata`: Context metadata dict (optional)
    - `quality_score`: Quality score 0.0-1.0 (optional)

    **Returns:**
    - `approved_output_id`: ID of created output
    - `indexed`: Whether output was successfully indexed in vector store
    - `created_at`: Timestamp of creation

    **Raises:**
    - `404 Not Found`: User, application, or job profile not found
    - `422 Unprocessable Entity`: Invalid request data
    - `500 Internal Server Error`: Unexpected error
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {request.user_id} not found"
            )

        # Validate application if provided
        if request.application_id:
            application = db.query(Application).filter(
                Application.id == request.application_id
            ).first()
            if not application:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Application {request.application_id} not found"
                )
            # Verify application belongs to user
            if application.user_id != request.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Application does not belong to user"
                )

        # Validate job profile if provided
        if request.job_profile_id:
            job_profile = db.query(JobProfile).filter(
                JobProfile.id == request.job_profile_id
            ).first()
            if not job_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job profile {request.job_profile_id} not found"
                )
            # Verify job profile belongs to user
            if job_profile.user_id != request.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Job profile does not belong to user"
                )

        # Create approved output
        approved_output = ApprovedOutput(
            user_id=request.user_id,
            application_id=request.application_id,
            job_profile_id=request.job_profile_id,
            output_type=request.output_type,
            original_text=request.original_text,
            context_metadata=request.context_metadata,
            quality_score=request.quality_score
        )

        db.add(approved_output)
        db.commit()
        db.refresh(approved_output)

        # Index in vector store
        indexed = False
        try:
            embedding_service = create_embedding_service(use_mock=False)
            vector_store = create_vector_store(use_mock=False)

            # Ensure collection exists before indexing
            await vector_store.ensure_collection(COLLECTION_APPROVED_OUTPUTS)

            await index_approved_output(
                approved_output=approved_output,
                embedding_service=embedding_service,
                vector_store=vector_store
            )

            # Store embedding in database
            if not approved_output.embedding:
                embedding = await embedding_service.generate_embedding(approved_output.original_text)
                approved_output.embedding = embedding
                db.add(approved_output)
                db.commit()

            indexed = True
            logger.info(f"Indexed approved output {approved_output.id} in vector store")

        except Exception as e:
            logger.error(f"Failed to index approved output {approved_output.id}: {e}", exc_info=True)
            # Don't fail the request if indexing fails

        return ApproveOutputResponse(
            approved_output_id=approved_output.id,
            user_id=approved_output.user_id,
            output_type=approved_output.output_type,
            original_text=approved_output.original_text,
            quality_score=approved_output.quality_score,
            indexed=indexed,
            created_at=approved_output.created_at.isoformat()
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error in approve_output: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to approve output: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while approving output"
        )


@router.get("/similar", response_model=SimilarOutputsResponse, status_code=status.HTTP_200_OK)
async def get_similar_outputs(
    query_text: str = Query(..., description="Query text to find similar outputs", min_length=1),
    user_id: int = Query(..., description="User ID", gt=0),
    output_type: Optional[Literal[
        'resume_bullet',
        'cover_letter_paragraph',
        'professional_summary',
        'full_resume',
        'full_cover_letter'
    ]] = Query(None, description="Filter by output type"),
    limit: int = Query(5, description="Maximum number of results", gt=0, le=50),
    min_quality_score: Optional[float] = Query(
        None, description="Minimum quality score filter", ge=0.0, le=1.0
    ),
    db: Session = Depends(get_db)
) -> SimilarOutputsResponse:
    """
    Retrieve similar approved outputs for a given query.

    Uses semantic similarity search to find approved outputs that are similar
    to the query text. Results can be filtered by output type and quality score.

    **Query Parameters:**
    - `query_text`: Text to find similar outputs for (required)
    - `user_id`: User ID (required)
    - `output_type`: Filter by output type (optional)
    - `limit`: Maximum number of results (1-50, default 5)
    - `min_quality_score`: Minimum quality score 0.0-1.0 (optional)

    **Returns:**
    - `results`: List of similar outputs with similarity scores
    - `total_found`: Number of results found
    - Applied filters and parameters

    **Raises:**
    - `404 Not Found`: User not found
    - `422 Unprocessable Entity`: Invalid query parameters
    - `500 Internal Server Error`: Unexpected error
    """
    try:
        # Validate user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Import retrieval service
        from services.output_retrieval import retrieve_similar_outputs

        # Create services
        embedding_service = create_embedding_service(use_mock=False)
        vector_store = create_vector_store(use_mock=False)

        # Retrieve similar outputs
        results = await retrieve_similar_outputs(
            query_text=query_text,
            embedding_service=embedding_service,
            vector_store=vector_store,
            user_id=user_id,
            output_type=output_type,
            limit=limit,
            min_quality_score=min_quality_score
        )

        # Convert to response format
        similar_outputs = []
        for result in results:
            payload = result.get('payload', {})
            similar_outputs.append(
                SimilarOutput(
                    output_id=payload.get('output_id'),
                    output_type=payload.get('output_type'),
                    text=payload.get('text', ''),
                    similarity_score=result.get('score', 0.0),
                    quality_score=payload.get('quality_score'),
                    created_at=payload.get('created_at'),
                    application_id=payload.get('application_id')
                )
            )

        return SimilarOutputsResponse(
            query_text=query_text,
            user_id=user_id,
            output_type=output_type,
            results=similar_outputs,
            total_found=len(similar_outputs),
            limit=limit,
            min_quality_score=min_quality_score
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error in get_similar_outputs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to retrieve similar outputs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving similar outputs"
        )
