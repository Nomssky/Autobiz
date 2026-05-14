from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from app.api.dependencies import get_db_session
from app.models.subscription import TIER_LIMITS, Subscription
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class StripeWebhookEvent(BaseModel):
    event_type: str
    data: Dict[str, Any]


def _map_tier(price_id: str) -> str:
    mapping = {
        "price_starter_monthly": "starter",
        "price_growth_monthly": "growth",
        "price_enterprise_monthly": "enterprise",
    }
    return mapping.get(price_id, "starter")


def _get_or_create_subscription(user_id: UUID, db: Session) -> Subscription:
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if not sub:
        limits = TIER_LIMITS["starter"]
        sub = Subscription(
            user_id=user_id,
            tier="starter",
            status="active",
            businesses_limit=limits["businesses"],
            ai_budget_monthly=limits["ai_budget"],
        )
        db.add(sub)
        db.flush()
    return sub


@router.post("/stripe/checkout", summary="Stripe checkout webhook")
async def stripe_checkout_webhook(
    event: StripeWebhookEvent,
    db: Session = Depends(get_db_session),
):
    if event.event_type != "checkout.session.completed":
        return {"status": "ignored", "event_type": event.event_type}

    data = event.data
    user_id = data.get("metadata", {}).get("user_id")
    tier = data.get("metadata", {}).get("tier", "starter")
    stripe_subscription_id = data.get("subscription")
    stripe_customer_id = data.get("customer")

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id in metadata")

    user_uuid = UUID(user_id)
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["starter"])

    sub = _get_or_create_subscription(user_uuid, db)
    sub.tier = tier
    sub.stripe_subscription_id = stripe_subscription_id
    sub.stripe_customer_id = stripe_customer_id
    sub.status = "active"
    sub.businesses_limit = limits["businesses"]
    sub.ai_budget_monthly = limits["ai_budget"]
    sub.current_period_start = datetime.utcnow()

    db.commit()
    return {"status": "activated", "tier": tier, "user_id": user_id}


@router.post("/stripe/subscription", summary="Stripe subscription webhook")
async def stripe_subscription_webhook(
    event: StripeWebhookEvent,
    db: Session = Depends(get_db_session),
):
    data = event.data
    stripe_sub_id = data.get("id") or data.get("subscription")

    if not stripe_sub_id:
        return {"status": "ignored"}

    sub = (
        db.query(Subscription).filter(Subscription.stripe_subscription_id == stripe_sub_id).first()
    )

    if not sub:
        return {"status": "not_found"}

    if event.event_type == "customer.subscription.updated":
        sub.status = data.get("status", sub.status)
        if data.get("current_period_end"):
            sub.current_period_end = datetime.fromtimestamp(data["current_period_end"])
        if data.get("cancel_at_period_end"):
            sub.cancel_at_period_end = data["cancel_at_period_end"]

    elif event.event_type == "customer.subscription.deleted":
        sub.status = "canceled"
        sub.cancel_at_period_end = False

    elif event.event_type == "invoice.paid":
        sub.status = "active"
        if data.get("period_end"):
            sub.current_period_end = datetime.fromtimestamp(data["period_end"])

    elif event.event_type == "invoice.payment_failed":
        sub.status = "past_due"

    db.commit()
    return {"status": "synced", "subscription_id": stripe_sub_id}


@router.post("/stripe/invoice", summary="Stripe invoice webhook")
async def stripe_invoice_webhook(
    event: StripeWebhookEvent,
    db: Session = Depends(get_db_session),
):
    return await stripe_subscription_webhook(event, db)


@router.post("/stripe/payment", summary="Stripe payment webhook")
async def stripe_payment_webhook(event: StripeWebhookEvent):
    return {"status": "received", "event_type": event.event_type}


@router.post("/{webhook_type}", summary="Generic webhook endpoint")
async def generic_webhook(webhook_type: str, payload: Dict[str, Any]):
    return {"status": "received", "webhook_type": webhook_type}
