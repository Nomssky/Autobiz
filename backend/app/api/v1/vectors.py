"""Vector memory API endpoints — semantic search and knowledge management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.api.dependencies import get_db_session, require_ceo
from app.infrastructure.vector_store import VectorStore
from app.schemas import (
    VectorSearchRequest,
    VectorSearchResponse,
    VectorUpsertRequest,
    KnowledgeEntryResponse,
)
from app.models.business import Business

router = APIRouter(prefix="/vectors", tags=["vectors"])


def get_vector_store() -> VectorStore:
    """Initialize and return vector store instance."""
    return VectorStore({
        "backend": "qdrant",
        "collection_name": "autobiz_knowledge",
        "dimension": 1536,
    })


@router.post(
    "/search",
    response_model=VectorSearchResponse,
    summary="Semantic search across business knowledge",
)
def search_vectors(
    request: VectorSearchRequest,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Search for semantically similar knowledge entries."""
    # Verify business exists
    from sqlalchemy import select

    result = db.execute(
        select(Business).where(Business.id == request.business_id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    try:
        vs = get_vector_store()
        # In production: use real embeddings from OpenAI/Cohere
        # Here we use mock vectors for demonstration
        mock_query_vector = [0.1] * 1536

        results = vs.search(
            query_vector=mock_query_vector,
            top_k=request.top_k,
        )

        return VectorSearchResponse(
            query=request.query,
            business_id=request.business_id,
            results=results,
            count=len(results),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}",
        )


@router.post(
    "/upsert",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Upsert knowledge entries into vector store",
)
def upsert_vectors(
    request: VectorUpsertRequest,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Insert or update knowledge entries in the vector store."""
    try:
        vs = get_vector_store()
        vs.upsert(request.vectors)
        return {
            "status": "success",
            "upserted_count": len(request.vectors),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector upsert failed: {str(e)}",
        )


@router.get(
    "/{business_id}/knowledge",
    response_model=List[KnowledgeEntryResponse],
    summary="List knowledge entries for a business",
)
def list_knowledge(
    business_id: UUID,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """List knowledge entries sourced from business tasks and feedback."""
    from sqlalchemy import select, desc
    from app.models.agent_task import AgentTask
    from app.models.user_feedback import UserFeedback

    # Get completed tasks with output data
    tasks_result = db.execute(
        select(AgentTask)
        .where(AgentTask.business_id == business_id)
        .where(AgentTask.status == "completed")
        .where(AgentTask.output_data.is_not(None))
        .order_by(desc(AgentTask.completed_at))
        .offset(skip)
        .limit(limit)
    )
    tasks = tasks_result.scalars().all()

    # Get processed feedback
    feedback_result = db.execute(
        select(UserFeedback)
        .where(UserFeedback.business_id == business_id)
        .where(UserFeedback.processed_by_ai == True)
        .order_by(desc(UserFeedback.created_at))
        .offset(skip)
        .limit(limit)
    )
    feedbacks = feedback_result.scalars().all()

    entries = []
    for t in tasks:
        entries.append(KnowledgeEntryResponse(
            id=f"task-{t.id}",
            source="agent_task",
            content=str(t.output_data),
            role=t.role_name,
            task_type=t.task_type,
            created_at=t.completed_at,
        ))

    for f in feedbacks:
        entries.append(KnowledgeEntryResponse(
            id=f"feedback-{f.id}",
            source="user_feedback",
            content=f.content,
            role=f.feedback_type or "feedback",
            task_type=None,
            created_at=f.created_at,
        ))

    return entries


@router.get(
    "/stats",
    response_model=dict,
    summary="Get vector store statistics",
)
def get_vector_stats(
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get statistics about the vector store."""
    try:
        vs = get_vector_store()
        count = vs.count()
        return {
            "total_vectors": count,
            "backend": vs.backend,
            "collection": vs._collection,
        }
    except Exception as e:
        return {
            "total_vectors": 0,
            "backend": "unavailable",
            "error": str(e),
        }