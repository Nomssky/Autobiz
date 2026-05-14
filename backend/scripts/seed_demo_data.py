"""Seed demo data for the AutoBiz Engine application.

Run with:
    python scripts/seed_demo_data.py
"""

import os
import sys

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from app.config import settings

# Override DB to SQLite for seeding if using default postgres (which may not be available)
if "postgresql" in settings.DATABASE_URL and not os.environ.get("SEED_USE_POSTGRES"):
    print("PostgreSQL not configured; set DATABASE_URL or SEED_USE_POSTGRES=1 to seed Postgres.")
    print("To seed SQLite, set: DATABASE_URL=sqlite:///./test.db")
    sys.exit(0)

from datetime import datetime, timezone
from uuid import uuid4

from app.models.agent_task import AgentTask
from app.models.approval_request import ApprovalRequest
from app.models.base import Base
from app.models.business import Business
from app.models.deployment import Deployment
from app.models.metric import MetricSnapshot
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def seed():
    """Seed demo data into the database."""
    engine = create_engine(settings.DATABASE_URL, echo=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if data already exists
        existing = db.query(Business).first()
        if existing:
            print("Demo data already exists. Skipping.")
            return

        ceo_id = uuid4()
        now = datetime.now(timezone.utc)

        # 1. Create a business
        business = Business(
            id=uuid4(),
            name="Acme AI Solutions",
            description="An AI-powered advisory platform for small businesses.",
            ceo_id=ceo_id,
            status="operating",
            current_phase="operation",
            business_metadata={
                "industry": "SaaS",
                "founded_by": "CEO Demo",
            },
            extra_metadata={},
            launched_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(business)
        db.flush()

        # 2. Create approval request
        approval = ApprovalRequest(
            id=uuid4(),
            business_id=business.id,
            task_id=None,
            title="Launch marketing campaign",
            description="Approve $2000 budget for Q1 social media campaign.",
            proposed_changes={"budget": 2000, "channel": "social_media"},
            impact_analysis={"expected_roi": "150%", "risk": "low"},
            urgency="high",
            status="pending",
            ceo_decision=None,
            decided_by_ceo_id=None,
            decided_at=None,
            expires_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
            notification_sent_at=None,
            created_at=now,
            updated_at=now,
        )
        db.add(approval)

        # 3. Create agent tasks
        tasks = [
            AgentTask(
                id=uuid4(),
                business_id=business.id,
                role_name="researcher",
                task_type="market_research",
                status="completed",
                input_data={"topic": "competitor analysis"},
                output_data={"summary": "3 competitors identified"},
                error_message=None,
                priority=3,
                requires_approval=False,
                approved_by_ceo_at=None,
                approval_request_id=None,
                started_at=now,
                completed_at=now,
                retry_count=0,
                created_at=now,
                updated_at=now,
            ),
            AgentTask(
                id=uuid4(),
                business_id=business.id,
                role_name="developer",
                task_type="build_website",
                status="running",
                input_data={"pages": ["home", "pricing", "contact"]},
                output_data=None,
                error_message=None,
                priority=4,
                requires_approval=True,
                approved_by_ceo_at=None,
                approval_request_id=approval.id,
                started_at=now,
                completed_at=None,
                retry_count=0,
                created_at=now,
                updated_at=now,
            ),
        ]
        db.add_all(tasks)

        # 4. Create metric snapshot
        metric = MetricSnapshot(
            id=uuid4(),
            business_id=business.id,
            recorded_by_role="finance",
            daily_revenue=1450.75,
            weekly_revenue=10155.25,
            monthly_revenue=43500.00,
            users_count=342,
            active_users_count=278,
            churn_rate=0.028,
            bug_count=3,
            support_tickets_count=12,
            open_support_tickets=5,
            conversion_rate=0.045,
            customer_acquisition_cost=25.50,
            lifetime_value=480.00,
            custom_metrics={"nps_score": 72},
            created_at=now,
            updated_at=now,
        )
        db.add(metric)

        # 5. Create deployment
        deployment = Deployment(
            id=uuid4(),
            business_id=business.id,
            version="v1.0.0",
            environment="production",
            status="live",
            changes={"features": ["landing_page", "pricing_tiers"]},
            triggered_by_role="developer",
            approved_by_ceo_id=ceo_id,
            deployed_at=now,
            rollback_at=None,
            created_at=now,
            updated_at=now,
        )
        db.add(deployment)

        # 6. Create a second business (building)
        business2 = Business(
            id=uuid4(),
            name="DataForge Labs",
            description="Data analytics pipeline for e-commerce.",
            ceo_id=uuid4(),
            status="building",
            current_phase="design",
            business_metadata={"industry": "Analytics"},
            extra_metadata={},
            launched_at=None,
            created_at=now,
            updated_at=now,
        )
        db.add(business2)

        db.commit()
        print("✅ Demo data seeded successfully!")
        print(f"   - 2 businesses: '{business.name}' (operating), '{business2.name}' (building)")
        print("   - 1 approval request (pending)")
        print("   - 2 agent tasks")
        print("   - 1 metric snapshot")
        print("   - 1 deployment (live)")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
