"""Feedback processor — collects and processes user feedback for agent improvement."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import UUID

from app.models.user_feedback import UserFeedback

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """Processes user feedback to generate insights for agent improvement."""

    def __init__(self, db_session):
        self.db = db_session

    def collect_feedback_for_business(self, business_id: UUID, days: int = 30) -> List[Dict]:
        """Collect recent feedback for a business."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        from sqlalchemy import desc, select

        result = self.db.execute(
            select(UserFeedback)
            .where(UserFeedback.business_id == business_id)
            .where(UserFeedback.created_at >= cutoff)
            .order_by(desc(UserFeedback.created_at))
        )
        feedbacks = result.scalars().all()

        return [self._feedback_to_dict(f) for f in feedbacks]

    def analyze_sentiment_distribution(self, business_id: UUID, days: int = 30) -> Dict:
        """Analyze sentiment distribution of feedback."""
        feedbacks = self.collect_feedback_for_business(business_id, days)

        if not feedbacks:
            return {"total": 0, "sentiment_breakdown": {}, "avg_score": 0.0}

        sentiment_types = {}
        total_score = 0.0

        for f in feedbacks:
            ftype = f["feedback_type"] or "unspecified"
            sentiment_types[ftype] = sentiment_types.get(ftype, 0) + 1
            if f["sentiment_score"] is not None:
                total_score += f["sentiment_score"]

        avg_score = total_score / len(feedbacks)

        return {
            "total": len(feedbacks),
            "sentiment_breakdown": sentiment_types,
            "avg_score": round(avg_score, 3),
            "positive_pct": round(
                sum(1 for f in feedbacks if (f["sentiment_score"] or 0) > 0) / len(feedbacks) * 100,
                1,
            ),
            "negative_pct": round(
                sum(1 for f in feedbacks if (f["sentiment_score"] or 0) < 0) / len(feedbacks) * 100,
                1,
            ),
        }

    def extract_key_themes(self, business_id: UUID, days: int = 30) -> List[Dict]:
        """Extract key themes from feedback using LLM analysis."""
        feedbacks = self.collect_feedback_for_business(business_id, days)

        if not feedbacks:
            return []

        texts = [f.get("content", "") for f in feedbacks if f.get("content")]
        if not texts:
            return []

        import json as _json
        combined = "\n".join(f"- {t[:200]}" for t in texts[:50])
        logger.info(f"Analyzing {len(texts)} feedback items for business {business_id}")

        from app.agents.llm_factory import create_llm
        import asyncio

        llm = create_llm()
        prompt = f"""Analyze these customer feedback items and extract key themes.

Feedback:
{combined}

Return ONLY a JSON array of objects with:
- theme: short name of the theme
- mentions: number of mentions (count from the data)
- sentiment: overall sentiment (positive/negative/mixed)
- sample_comments: array of up to 3 representative quotes

Return max 5 themes."""
        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(
                llm.ainvoke(prompt, system_prompt="You are a feedback analysis AI.")
            )
            themes = _json.loads(response)
            if isinstance(themes, list):
                return themes
            raise ValueError(f"LLM returned non-list: {response}")
        except Exception as e:
            raise RuntimeError(f"Theme extraction failed: {e}")
        finally:
            loop.close()

    def generate_improvement_recommendations(self, business_id: UUID, days: int = 30) -> List[Dict]:
        """Generate actionable improvement recommendations from feedback."""
        analysis = self.analyze_sentiment_distribution(business_id, days)
        themes = self.extract_key_themes(business_id, days)

        recommendations = []

        if analysis["negative_pct"] > 30:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "urgent_fix",
                    "description": "High negative feedback rate detected. Investigate top complaints.",
                    "estimated_impact": "Customer retention improvement",
                }
            )

        for theme in themes:
            if theme["sentiment"] == "negative" and theme["mentions"] >= 5:
                recommendations.append(
                    {
                        "priority": "medium",
                        "category": "feature_improvement",
                        "description": f"Improve '{theme['theme']}' area ({theme['mentions']} mentions)",
                        "estimated_impact": f"Reduce complaints about {theme['theme']}",
                    }
                )

        return recommendations

    def process_for_agent_learning(self, business_id: UUID, feedback: UserFeedback) -> Dict:
        """Process a single feedback item for agent learning pipeline."""
        learning_signal = {
            "business_id": str(business_id),
            "feedback_id": str(feedback.id),
            "type": feedback.feedback_type,
            "content": feedback.content,
            "sentiment": feedback.sentiment_score,
            "processed_by_ai": True,
            "learning_actions": [],
        }

        # Determine which agents should learn from this feedback
        if feedback.feedback_type == "bug":
            learning_signal["learning_actions"].append(
                {
                    "agent": "developer",
                    "action": "fix_bug",
                    "priority": "high" if (feedback.sentiment_score or 0) < -0.5 else "medium",
                }
            )
        elif feedback.feedback_type == "feature_request":
            learning_signal["learning_actions"].append(
                {
                    "agent": "researcher",
                    "action": "evaluate_feature",
                    "priority": "medium",
                }
            )
        elif feedback.feedback_type == "complaint":
            learning_signal["learning_actions"].append(
                {
                    "agent": "support",
                    "action": "improve_response",
                    "priority": "high",
                }
            )

        return learning_signal

    def _feedback_to_dict(self, feedback: UserFeedback) -> Dict:
        """Convert UserFeedback model to dict."""
        return {
            "id": feedback.id,
            "business_id": feedback.business_id,
            "user_id": feedback.user_id,
            "feedback_type": feedback.feedback_type,
            "content": feedback.content,
            "sentiment_score": feedback.sentiment_score,
            "processed_by_ai": feedback.processed_by_ai,
            "processed_at": feedback.processed_at.isoformat() if feedback.processed_at else None,
            "action_taken": feedback.action_taken,
            "created_at": feedback.created_at.isoformat(),
        }
