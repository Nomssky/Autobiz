from datetime import datetime, timedelta
from uuid import UUID

import stripe
from app.api.dependencies import get_current_user, get_db_session
from app.config import settings
from app.models.agent_execution import AgentExecution
from app.models.subscription import Subscription
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/billing", tags=["billing"])

MONTHLY_BUDGET = 50.0
COST_PER_TOKEN = 0.000002


@router.get("/usage", summary="Get current billing period usage")
def get_usage(
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user),
):
    sub = db.execute(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status == "active",
        )
    ).scalar_one_or_none()

    monthly_budget = sub.get_ai_budget() if sub else MONTHLY_BUDGET
    businesses_limit = sub.get_businesses_limit() if sub else 1

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = db.execute(
        select(
            func.coalesce(func.sum(AgentExecution.input_tokens + AgentExecution.output_tokens), 0),
            func.coalesce(func.sum(AgentExecution.cost_usd), 0.0),
            func.count(AgentExecution.id),
        ).where(
            AgentExecution.created_at >= month_start,
        )
    )
    total_tokens, total_cost, total_executions = result.one()

    cost_decimal = float(total_cost)
    tokens_used = int(total_tokens)
    budget_used_pct = round((cost_decimal / monthly_budget) * 100, 1) if monthly_budget > 0 else 0

    return {
        "tier": sub.tier if sub else "starter",
        "subscription_status": sub.status if sub else "none",
        "period_start": month_start.isoformat(),
        "period_end": (now.replace(day=1) + timedelta(days=32)).replace(day=1).isoformat(),
        "usage": {
            "tokens_used": tokens_used,
            "total_cost": round(cost_decimal, 4),
            "total_executions": total_executions,
            "monthly_budget": monthly_budget,
            "budget_used_percent": budget_used_pct,
        },
        "limits": {
            "businesses_limit": businesses_limit,
            "ai_budget_monthly": monthly_budget,
        },
        "needs_upgrade": budget_used_pct > 80,
    }


@router.get("/cost/{business_id}", summary="Cost breakdown per agent role")
def get_cost_breakdown(
    business_id: UUID,
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user),
):
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    results = db.execute(
        select(
            AgentExecution.role_name,
            func.sum(AgentExecution.input_tokens + AgentExecution.output_tokens).label("tokens"),
            func.sum(AgentExecution.cost_usd).label("cost"),
            func.count(AgentExecution.id).label("executions"),
        )
        .where(
            AgentExecution.business_id == business_id,
            AgentExecution.created_at >= month_start,
        )
        .group_by(AgentExecution.role_name)
    ).all()

    breakdown = []
    total_cost = 0.0
    for row in results:
        cost = float(row.cost or 0)
        total_cost += cost
        breakdown.append(
            {
                "role": row.role_name,
                "tokens": int(row.tokens or 0),
                "cost": round(cost, 4),
                "executions": row.executions,
            }
        )

    return {
        "business_id": str(business_id),
        "period": "monthly",
        "total_cost": round(total_cost, 4),
        "breakdown": breakdown,
    }


@router.post("/upgrade", summary="Create Stripe checkout session")
def create_checkout_session(
    tier: str,
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user),
):
    if tier not in ("starter", "growth", "enterprise"):
        raise HTTPException(status_code=400, detail="Invalid tier")

    price_ids = {
        "starter": "price_starter_monthly",
        "growth": "price_growth_monthly",
    }

    sub = db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    ).scalar_one_or_none()

    stripe.api_key = settings.STRIPE_API_KEY

    try:
        if sub and sub.stripe_customer_id:
            customer_id = sub.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                metadata={"user_id": str(user_id)},
            )
            customer_id = customer.id

        if tier == "enterprise":
            return {
                "type": "contact_sales",
                "message": "Contact sales@autobiz.ai for enterprise pricing",
            }

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_ids[tier], "quantity": 1}],
            mode="subscription",
            success_url="https://autobiz.ai/billing?success=true",
            cancel_url="https://autobiz.ai/billing?canceled=true",
            metadata={"user_id": str(user_id), "tier": tier},
        )
        return {"url": session.url, "session_id": session.id}

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Stripe package missing despite being in requirements.txt. Re-run: pip install -r requirements.txt",
        )


@router.get("/portal", summary="Get Stripe customer portal URL")
def get_portal_url(
    db: Session = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user),
):
    sub = db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    ).scalar_one_or_none()

    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No active subscription found")

    stripe.api_key = settings.STRIPE_API_KEY
    session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url="https://autobiz.ai/billing",
    )
    return {"url": session.url}
