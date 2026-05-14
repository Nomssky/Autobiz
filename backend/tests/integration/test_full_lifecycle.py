"""
Integration tests for AutoBiz Engine — Full Business Lifecycle.

Test flow: Create Business → AI Research → Development → Design → Finance → Launch → Operate → Scale
"""

import os
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.api.dependencies import get_db_session
from app.auth.jwt_handler import create_access_token
from app.main import app
from app.models.base import Base
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

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


# ====== Helpers ======


def _create_business(client, auth_headers, idea="AI-powered e-commerce personalization engine"):
    """Helper to create a business and return its ID."""
    resp = client.post(
        "/api/v1/businesses/create",
        json={"idea": idea},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ====== Full Lifecycle Tests ======


class TestBusinessCreation:
    """Phase 0: Business Creation"""

    def test_create_business_from_idea(self, client, ceo_id, auth_headers):
        """Create a business from an idea — entry point of the lifecycle."""
        response = client.post(
            "/api/v1/businesses/create",
            json={
                "idea": "AI-powered e-commerce personalization engine",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "building"
        assert "id" in data
        print(f"\n🏢 Business created: {data['id']}")

    def test_get_business_details(self, client, auth_headers):
        """Retrieve business details."""
        business_id = _create_business(client, auth_headers)

        response = client.get(f"/api/v1/businesses/{business_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == business_id
        assert data["status"] == "building"


class TestBuildPipeline:
    """Phase 1-3: Build Pipeline — Research, Development, Design tasks created."""

    def test_timeline_has_phases(self, client, auth_headers):
        """Build pipeline should create agent task phases."""
        business_id = _create_business(client, auth_headers)

        response = client.get(f"/api/v1/businesses/{business_id}/timeline", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "phases" in data

    def test_business_transitioned_after_creation(self, client, auth_headers):
        """After build pipeline, business should be in building or later phase."""
        business_id = _create_business(client, auth_headers)
        response = client.get(f"/api/v1/businesses/{business_id}", headers=auth_headers)
        data = response.json()
        assert data["status"] in ["building", "operating", "failed"]


class TestApprovalWorkflow:
    """Phase 4: Approval workflows during build."""

    def test_create_and_decide_approval(self, client, ceo_id, auth_headers):
        """Create an approval request and approve it."""
        business_id = _create_business(client, auth_headers)

        resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": business_id,
                "title": "Approve marketing budget",
                "description": "Initial $5,000 marketing spend for launch",
                "proposed_changes": {"budget": 5000},
                "impact_analysis": {"estimated_cost": 5000},
                "urgency": "high",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        approval_id = data["id"]

        # CEO approves
        resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"decision": "approve", "ceo_id": str(ceo_id), "comments": "Approved"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["approved"] is True

        # Cannot re-decide
        resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"decision": "reject", "ceo_id": str(ceo_id)},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestMetricsLifecycle:
    """Phase 5-6: Metrics — Record and retrieve operational data."""

    def test_record_and_summarize_metrics(self, client, auth_headers):
        """Record metrics and retrieve summary."""
        business_id = _create_business(client, auth_headers)

        for day in range(7):
            resp = client.post(
                "/api/v1/metrics/",
                json={
                    "business_id": business_id,
                    "recorded_by_role": "finance",
                    "daily_revenue": 500 + day * 50,
                    "users_count": 100 + day * 20,
                    "churn_rate": round(0.03 + day * 0.002, 4),
                },
                headers=auth_headers,
            )
            assert resp.status_code == 201

        resp = client.get(
            f"/api/v1/metrics/{business_id}/summary?days=7", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["snapshot_count"] >= 7
        assert data["avg_daily_revenue"] > 0


class TestLaunch:
    """Phase 7: Launch the business."""

    def test_launch_business(self, client, auth_headers):
        """Launch a business from building to operating."""
        business_id = _create_business(client, auth_headers)
        resp = client.post(f"/api/v1/businesses/{business_id}/launch", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "operating"
        assert data["launched_at"] is not None
        print(f"\n🚀 Business launched at {data['launched_at']}")

    def test_launch_twice_fails(self, client, auth_headers):
        """Already launched business cannot be launched again."""
        business_id = _create_business(client, auth_headers)
        client.post(f"/api/v1/businesses/{business_id}/launch", headers=auth_headers)
        resp = client.post(f"/api/v1/businesses/{business_id}/launch", headers=auth_headers)
        assert resp.status_code == 400


class TestArchive:
    """Phase 8: Archive business."""

    def test_archive_business(self, client, auth_headers):
        """Archive a business."""
        business_id = _create_business(client, auth_headers)
        resp = client.delete(f"/api/v1/businesses/{business_id}", headers=auth_headers)
        assert resp.status_code == 204


# ====== Utility Tests ======


class TestErrorHandling:
    """Test error cases and edge conditions."""

    def test_create_duplicate_business(self, client, ceo_id, auth_headers):
        """Creating same business twice should both succeed (different IDs)."""
        resp1 = client.post(
            "/api/v1/businesses/create",
            json={"idea": "Test business"},
            headers=auth_headers,
        )
        resp2 = client.post(
            "/api/v1/businesses/create",
            json={"idea": "Test business"},
            headers=auth_headers,
        )
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
