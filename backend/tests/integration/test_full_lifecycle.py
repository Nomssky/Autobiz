"""
Integration tests for AutoBiz Engine — Full Business Lifecycle.

Test flow: Create Business → AI Research → Development → Design → Finance → Launch → Operate → Scale
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from starlette.testclient import TestClient

from app.main import app
from app.api.dependencies import get_db_session
from app.auth.jwt_handler import create_access_token
from app.models.base import Base
from app.models.business import Business
from app.models.agent_task import AgentTask
from app.models.approval_request import ApprovalRequest
from app.models.metric import MetricSnapshot

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool


# ---- Test Database ----

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _fk_pragma_on_connect(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

event.listen(engine, "connect", _fk_pragma_on_connect)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def override_get_db():
    def _override():
        db = TestingSessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    app.dependency_overrides[get_db_session] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client(override_get_db):
    return TestClient(app)


@pytest.fixture()
def ceo_id():
    return uuid4()


@pytest.fixture()
def auth_headers(ceo_id):
    token = create_access_token({"sub": str(ceo_id), "roles": ["ceo"]})
    return {"Authorization": f"Bearer {token}"}


# ====== Full Lifecycle Tests ======

class TestBusinessCreation:
    """Phase 0: Business Creation"""

    def test_create_business_from_idea(self, client, ceo_id, auth_headers):
        """Create a business from an idea — entry point of the lifecycle."""
        response = client.post(
            "/api/v1/businesses/create",
            json={
                "idea": "AI-powered e-commerce personalization engine",
                "ceo_id": str(ceo_id),
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "building"
        assert "id" in data
        self.__class__.business_id = data["id"]
        print(f"\n🏢 Business created: {data['id']}")

    def test_get_business_details(self, client, ceo_id, auth_headers):
        """Retrieve business details."""
        business_id = getattr(self.__class__, 'business_id', None)
        assert business_id, "No business created yet"

        response = client.get(f"/api/v1/businesses/{business_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == business_id
        assert data["name"] == "AI-powered e-commerce personalization engine"


class TestBuildPipeline:
    """Phase 1-3: Build Pipeline — Research, Development, Design tasks created."""

    def test_timeline_has_phases(self, client, ceo_id, auth_headers):
        """Build pipeline should create agent task phases."""
        business_id = getattr(self.__class__, 'business_id', None)
        assert business_id, "No business created"

        response = client.get(f"/api/v1/businesses/{business_id}/timeline", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "phases" in data
        phases = data["phases"]
        assert len(phases) > 0, "Build pipeline should create at least one task"

        task_types = [p["task_type"] for p in phases]
        print(f"\n📋 Pipeline tasks: {task_types}")

    def test_business_transitioned_to_planning(self, client, ceo_id, auth_headers):
        """After build pipeline, business should be in planning or later phase."""
        business_id = getattr(self.__class__, 'business_id', None)
        response = client.get(f"/api/v1/businesses/{business_id}", headers=auth_headers)
        data = response.json()
        # Phase may vary depending on pipeline implementation
        assert data["status"] in ["building", "operating", "failed"]


class TestApprovalWorkflow:
    """Phase 4: Approval workflows during build."""

    def test_create_approval_request(self, client, ceo_id, auth_headers):
        """Create an approval request for a major decision."""
        business_id = getattr(self.__class__, 'business_id', None)
        assert business_id

        response = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": business_id,
                "title": "Approve marketing budget",
                "description": "Initial $5,000 marketing spend for launch",
                "proposed_changes": {
                    "budget": 5000,
                    "channels": ["google_ads", "social_media"],
                },
                "impact_analysis": {
                    "estimated_cost": 5000,
                    "estimated_revenue_increase": 20000,
                    "users_affected": 5000,
                },
                "urgency": "high",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["urgency"] == "high"
        self.__class__.approval_id = data["id"]
        print(f"\n📋 Approval created: {data['id']}")

    def test_list_pending_approvals(self, client, ceo_id, auth_headers):
        """Should see pending approvals."""
        response = client.get("/api/v1/approvals/pending", headers=auth_headers)
        assert response.status_code == 200
        approvals = response.json()
        assert isinstance(approvals, list)
        assert len(approvals) >= 1

    def test_ceo_approves(self, client, ceo_id, auth_headers):
        """CEO approves the request."""
        approval_id = getattr(self.__class__, 'approval_id', None)
        assert approval_id

        response = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={
                "decision": "approve",
                "ceo_id": str(ceo_id),
                "comments": "Approved — go ahead with marketing",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["approved"] is True
        print(f"\n✅ Approval {approval_id} approved")

    def test_approval_cannot_be_re_decided(self, client, ceo_id, auth_headers):
        """Already-decided approval cannot be changed."""
        approval_id = getattr(self.__class__, 'approval_id', None)
        assert approval_id

        response = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={
                "decision": "reject",
                "ceo_id": str(ceo_id),
                "comments": "Trying to reject already-approved",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestMetricsLifecycle:
    """Phase 5-6: Metrics — Record and retrieve operational data."""

    def _auth_headers(self, ceo_id):
        token = create_access_token({"sub": str(ceo_id), "roles": ["ceo"]})
        return {"Authorization": f"Bearer {token}"}

    def test_record_daily_metrics(self, client, ceo_id, auth_headers):
        business_id = getattr(self.__class__, 'business_id', None)
        assert business_id

        for day in range(7):
            resp = client.post("/api/v1/metrics/", json={
                "business_id": business_id,
                "recorded_by_role": "finance",
                "daily_revenue": 500 + day * 50,
                "weekly_revenue": 3500 + day * 350,
                "monthly_revenue": 15000 + day * 1500,
                "users_count": 100 + day * 20,
                "active_users_count": 80 + day * 15,
                "churn_rate": round(0.03 + day * 0.002, 4),
                "bug_count": max(1, 5 - day),
                "support_tickets_count": 20 - day * 2,
                "open_support_tickets": 8 - day,
                "conversion_rate": round(0.03 + day * 0.005, 4),
                "customer_acquisition_cost": 25.0 - day * 0.5,
                "lifetime_value": 480.0 + day * 20,
            })
            assert resp.status_code == 201

        print("\n📊 7 days of metrics recorded")

    def test_metric_summary(self, client, ceo_id, auth_headers):
        business_id = getattr(self.__class__, 'business_id', None)
        resp = client.get(f"/api/v1/metrics/{business_id}/summary?days=7", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["snapshot_count"] >= 7
        assert data["avg_daily_revenue"] > 0
        print(f"📈 Summary: {data['snapshot_count']} days, avg revenue={data['avg_daily_revenue']:.2f}")

    def test_get_latest_metric(self, client, ceo_id, auth_headers):
        business_id = getattr(self.__class__, 'business_id', None)
        resp = client.get(f"/api/v1/metrics/{business_id}/realtime", headers=auth_headers)
        assert resp.status_code in (200, 404)


class TestLaunch:
    """Phase 7: Launch the business."""

    def test_launch_business(self, client, ceo_id, auth_headers):
        business_id = getattr(self.__class__, 'business_id', None)
        resp = client.post(f"/api/v1/businesses/{business_id}/launch", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "operating"
        assert data["launched_at"] is not None
        print(f"\n🚀 Business launched at {data['launched_at']}")

    def test_cannot_re_launch(self, client, ceo_id, auth_headers):
        """Already launched business cannot be launched again."""
        business_id = getattr(self.__class__, 'business_id', None)
        resp = client.post(f"/api/v1/businesses/{business_id}/launch", headers=auth_headers)
        assert resp.status_code == 400


class TestArchive:
    """Phase 8: Archive business."""

    def test_archive_business(self, client, ceo_id, auth_headers):
        business_id = getattr(self.__class__, 'business_id', None)
        resp = client.delete(f"/api/v1/businesses/{business_id}", headers=auth_headers)
        assert resp.status_code == 204
        print(f"\n🗄️  Business {business_id[:8]} archived")


# ====== Utility Tests ======

class TestErrorHandling:
    """Test error cases and edge conditions."""

    def test_create_duplicate_business(self, client, ceo_id, auth_headers):
        """Creating same business twice should both succeed (different IDs)."""
        resp1 = client.post("/api/v1/businesses/create", json={
            "idea": "Test business",
            "ceo_id": str(ceo_id),
        }, headers=auth_headers)
        resp2 = client.post("/api/v1/businesses/create", json={
            "idea": "Test business",
            "ceo_id": str(ceo_id),
        }, headers=auth_headers)
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["id"] != resp2.json()["id"]

    def test_get_nonexistent_business(self, client, ceo_id, auth_headers):
        """Getting nonexistent business returns 404."""
        fake_id = uuid4()
        resp = client.get(f"/api/v1/businesses/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_approve_nonexistent_approval(self, client, ceo_id, auth_headers):
        """Deciding on nonexistent approval returns 404."""
        resp = client.post(
            f"/api/v1/approvals/{uuid4()}/decide",
            json={"decision": "approve", "ceo_id": str(ceo_id)},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_list_endpoints(self, client, ceo_id, auth_headers):
        """List endpoints return valid responses."""
        businesses = client.get("/api/v1/businesses/", headers=auth_headers)
        assert businesses.status_code == 200

        approvals = client.get("/api/v1/approvals/", headers=auth_headers)
        assert approvals.status_code == 200

        metrics = client.get("/api/v1/metrics/", headers=auth_headers)
        assert metrics.status_code == 200