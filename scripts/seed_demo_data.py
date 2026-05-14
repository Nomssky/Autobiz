#!/usr/bin/env python3
"""Seed demo data into AutoBiz Engine for staging/testing."""
import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost/autobiz_engine")


def main():
    from app.database import SessionLocal
    from app.models.agent_task import AgentTask
    from app.models.approval_request import ApprovalRequest
    from app.models.business import Business
    from app.models.metric import MetricSnapshot

    db = SessionLocal()
    try:
        ceo_id = uuid4()

        biz = Business(
            name="AI E-Commerce Engine",
            description="AI-powered product recommendation engine for e-commerce",
            ceo_id=ceo_id,
            status="operating",
            current_phase="operation",
        )
        db.add(biz)
        db.flush()

        for i in range(5):
            task = AgentTask(
                business_id=biz.id,
                role_name=["researcher", "developer", "designer", "marketer", "finance"][i],
                task_type=[
                    "market_research",
                    "application_generation",
                    "brand_identity",
                    "marketing_strategy",
                    "financial_modeling",
                ][i],
                status="completed",
                priority=5 - i,
            )
            db.add(task)
        db.flush()

        for day in range(30):
            metric = MetricSnapshot(
                business_id=biz.id,
                recorded_by_role="finance",
                daily_revenue=1000 + day * 50,
                users_count=100 + day * 10,
                churn_rate=0.03 - day * 0.001,
            )
            db.add(metric)

        approval = ApprovalRequest(
            business_id=biz.id,
            title="Launch Marketing Campaign",
            description="Approve $5,000 marketing budget for Q2 launch",
            proposed_changes={"budget": 5000, "channels": ["google_ads", "social_media"]},
            urgency="high",
            status="pending",
        )
        db.add(approval)

        db.commit()
        print(f"Seeded demo business: {biz.id}")
        print(f"  Name: {biz.name}")
        print("  Tasks: 5 created")
        print("  Metrics: 30 days")
        print("  Approvals: 1 pending")

    finally:
        db.close()


if __name__ == "__main__":
    main()
