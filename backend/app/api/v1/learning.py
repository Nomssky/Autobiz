"""Learning agent API endpoints — self-improving agent feedback loop."""

from typing import Optional
from uuid import UUID

from app.agents.learning.feedback_processor import FeedbackProcessor
from app.agents.learning.prompt_optimizer import PromptOptimizer
from app.agents.learning.success_evaluator import SuccessEvaluator
from app.api.dependencies import get_db_session, require_ceo
from app.schemas import AgentFeedbackRequest
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post(
    "/feedback",
    summary="Submit feedback for agent learning",
)
def submit_feedback(
    request: AgentFeedbackRequest,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Submit user feedback for agent improvement pipeline."""
    # Verify business exists
    from app.models.business import Business
    from app.models.user_feedback import UserFeedback
    from sqlalchemy import select

    result = db.execute(select(Business).where(Business.id == request.business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    # Create feedback record
    feedback = UserFeedback(
        business_id=request.business_id,
        user_id=request.user_id,
        feedback_type=request.feedback_type,
        content=request.content,
        sentiment_score=request.sentiment_score,
    )
    db.add(feedback)
    db.flush()
    db.refresh(feedback)

    # Process for agent learning
    processor = FeedbackProcessor(db)
    learning_signal = processor.process_for_agent_learning(request.business_id, feedback)

    return {
        "feedback_id": str(feedback.id),
        "status": "processed",
        "learning_actions": learning_signal["learning_actions"],
    }


@router.get(
    "/evaluation/{business_id}",
    summary="Get agent performance evaluation",
)
def get_evaluation(
    business_id: UUID,
    role: Optional[str] = None,
    days: int = 30,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get agent performance evaluation for a business."""
    evaluator = SuccessEvaluator(db)

    if role:
        result = evaluator.evaluate_agent(business_id, role, days)
    else:
        result = evaluator.evaluate_business(business_id, days)

    return result


@router.get(
    "/suggestions/{business_id}",
    summary="Get improvement suggestions",
)
def get_suggestions(
    business_id: UUID,
    role: Optional[str] = None,
    days: int = 30,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get AI-generated improvement suggestions for agents."""
    evaluator = SuccessEvaluator(db)

    if role:
        result = evaluator.evaluate_agent(business_id, role, days)
        suggestions = result.get("suggestions", [])
    else:
        result = evaluator.evaluate_business(business_id, days)
        suggestions = []
        for eval_item in result.get("evaluations", []):
            suggestions.extend(eval_item.get("suggestions", []))

    return {
        "business_id": str(business_id),
        "suggestions": suggestions,
        "total_suggestions": len(suggestions),
    }


@router.post(
    "/optimize-prompt",
    summary="Get optimized agent prompt",
)
def optimize_prompt(
    business_id: UUID,
    role_name: str,
    original_prompt: str,
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Get an AI-optimized version of an agent prompt based on execution history."""
    optimizer = PromptOptimizer(db)
    evaluator = SuccessEvaluator(db)

    stats = evaluator.evaluate_agent(business_id, role_name)
    optimized = optimizer.generate_optimized_prompt(
        original_prompt=original_prompt,
        role_name=role_name,
        business_context={
            "business_id": str(business_id),
            "stats": stats,
        },
        execution_stats=stats,
    )

    return {
        "original": original_prompt,
        "optimized": optimized,
        "optimizations_applied": optimized != original_prompt,
        "execution_stats": stats,
    }


@router.post(
    "/retrain",
    summary="Trigger embedding retraining",
)
def trigger_retrain(
    db: Session = Depends(get_db_session),
    _: UUID = Depends(require_ceo),
):
    """Trigger the embedding retraining pipeline (async recommended)."""
    import os
    import subprocess
    import sys

    script_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "scripts", "retrain_embeddings.py"
    )

    # In production, run as Celery task
    subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return {
        "status": "retraining_triggered",
        "message": "Embedding retraining started in background",
    }
