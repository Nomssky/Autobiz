"""
Integration tests for AutoBiz Engine — Complete Approval Flow.

Test flow: Create Business → Agent creates approval request → CEO approve/reject
→ Notification sent → Next task proceeds → Verify end-to-end
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
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
def override_get_db(setup_db):
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


def _auth_header(ceo_id=None):
    if ceo_id is None:
        ceo_id = uuid4()
    token = create_access_token({"sub": str(ceo_id), "roles": ["ceo"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def ceo_id():
    return uuid4()


@pytest.fixture()
def client(override_get_db):
    return TestClient(app)


class TestApprovalLifecycle:
    """Complete approval lifecycle: Create → Notify → Approve → Verify"""

    def _create_business(self, client, ceo_id, headers):
        resp = client.post(
            "/api/v1/businesses/create",
            json={
                "idea": "Test business for approval flow",
                "ceo_id": str(ceo_id),
            },
            headers=headers,
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_create_approval_request(self, client, ceo_id):
        """Agent creates an approval request for CEO decision."""
        headers = _auth_header(ceo_id)
        business_id = self._create_business(client, ceo_id, headers)

        resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "Increase marketing budget to $10,000",
                "description": "Proposal to increase monthly marketing spend from $5,000 to $10,000",
                "proposed_changes": {
                    "budget_increase": 5000,
                    "new_total": 10000,
                    "channels": ["google_ads", "facebook_ads", "linkedin"],
                    "duration_months": 3,
                },
                "impact_analysis": {
                    "estimated_additional_revenue": 35000,
                    "estimated_cost": 15000,
                    "roi_percent": 233,
                    "users_affected": 10000,
                },
                "urgency": "high",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["urgency"] == "high"
        assert data["title"] == "Increase marketing budget to $10,000"
        assert "id" in data
        self.__class__.approval_id = data["id"]
        self.__class__.business_id = data["business_id"]

    def test_get_pending_approvals(self, client, ceo_id):
        """CEO views all pending approvals."""
        headers = _auth_header(ceo_id)
        resp = client.get("/api/v1/approvals/pending", headers=headers)
        assert resp.status_code == 200
        approvals = resp.json()
        assert isinstance(approvals, list)
        assert len(approvals) >= 1
        pending_ids = [a["id"] for a in approvals]
        assert self.__class__.approval_id in pending_ids

    def test_get_single_approval_detail(self, client, ceo_id):
        """CEO views details of a specific approval request."""
        headers = _auth_header(ceo_id)
        approval_id = self.__class__.approval_id
        resp = client.get(f"/api/v1/approvals/{approval_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == approval_id
        assert data["status"] == "pending"
        assert "proposed_changes" in data
        assert data["proposed_changes"]["new_total"] == 10000

    def test_ceo_approves_request(self, client, ceo_id):
        """CEO approves the request — triggers notification."""
        headers = _auth_header(ceo_id)
        approval_id = self.__class__.approval_id

        resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={
                "decision": "approve",
                "ceo_id": str(ceo_id),
                "comments": "Approved — excellent ROI projection. Proceed with implementation.",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["approved"] is True
        assert result["approval_id"] == approval_id

    def test_approval_status_changes_to_approved(self, client, ceo_id):
        """After decision, approval status reflects the decision."""
        headers = _auth_header(ceo_id)
        approval_id = self.__class__.approval_id
        resp = client.get(f"/api/v1/approvals/{approval_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approve"
        assert data["ceo_decision"] is not None
        assert data["decided_by_ceo_id"] is not None
        assert data["decided_at"] is not None

    def test_cannot_decide_twice(self, client, ceo_id):
        """Already decided approval cannot be re-decided."""
        headers = _auth_header(ceo_id)
        approval_id = self.__class__.approval_id

        resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={
                "decision": "reject",
                "ceo_id": str(ceo_id),
                "comments": "Changed my mind",
            },
            headers=headers,
        )
        assert resp.status_code == 400

    def test_list_approvals_shows_all_statuses(self, client, ceo_id):
        """List endpoint includes the approved request."""
        headers = _auth_header(ceo_id)
        resp = client.get("/api/v1/approvals/", headers=headers)
        assert resp.status_code == 200
        approvals = resp.json()
        assert len(approvals) >= 1
        approval_ids = [a["id"] for a in approvals]
        assert self.__class__.approval_id in approval_ids

    def test_filter_approvals_by_business(self, client, ceo_id):
        """Filter approvals by business ID."""
        headers = _auth_header(ceo_id)
        business_id = self.__class__.business_id
        resp = client.get(
            f"/api/v1/approvals/?business_id={business_id}",
            headers=headers,
        )
        assert resp.status_code == 200
        approvals = resp.json()
        assert all(a["business_id"] == business_id for a in approvals)


class TestApprovalRejection:
    """CEO rejects an approval request flow."""

    def _create_business(self, client, ceo_id, headers):
        resp = client.post(
            "/api/v1/businesses/create",
            json={"idea": "Test business for rejection", "ceo_id": str(ceo_id)},
            headers=headers,
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_create_and_reject(self, client, ceo_id):
        """CEO rejects an approval request."""
        headers = _auth_header(ceo_id)
        business_id = self._create_business(client, ceo_id, headers)

        create_resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "Hire 3 senior engineers",
                "description": "Hiring plan for Q2",
                "proposed_changes": {
                    "headcount": 3,
                    "cost_per_year": 450000,
                    "start_date": "2025-07-01",
                },
                "urgency": "normal",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        approval_id = create_resp.json()["id"]

        reject_resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={
                "decision": "reject",
                "ceo_id": str(ceo_id),
                "comments": "Budget freeze — revisit next quarter",
            },
            headers=headers,
        )
        assert reject_resp.status_code == 200
        result = reject_resp.json()
        assert result["approved"] is False

        get_resp = client.get(f"/api/v1/approvals/{approval_id}", headers=headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["status"] == "reject"


class TestApprovalCancellation:
    """Approval request cancellation flow."""

    def _create_business(self, client, ceo_id, headers):
        resp = client.post(
            "/api/v1/businesses/create",
            json={"idea": "Test business for cancellation", "ceo_id": str(ceo_id)},
            headers=headers,
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_cancel_pending_approval(self, client, ceo_id):
        """Pending approval can be cancelled before decision."""
        headers = _auth_header(ceo_id)
        business_id = self._create_business(client, ceo_id, headers)

        resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "Cancel me",
                "proposed_changes": {"test": True},
                "urgency": "low",
            },
            headers=headers,
        )
        assert resp.status_code == 201
        approval_id = resp.json()["id"]

        cancel_resp = client.delete(
            f"/api/v1/approvals/{approval_id}",
            headers=headers,
        )
        assert cancel_resp.status_code == 204

        get_resp = client.get(f"/api/v1/approvals/{approval_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "cancelled"

    def test_cannot_cancel_decided_approval(self, client, ceo_id):
        """Already decided approval cannot be cancelled."""
        headers = _auth_header(ceo_id)
        business_id = self._create_business(client, ceo_id, headers)

        resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "Decide then cancel",
                "proposed_changes": {"test": True},
                "urgency": "normal",
            },
            headers=headers,
        )
        approval_id = resp.json()["id"]

        client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"decision": "approve", "ceo_id": str(ceo_id)},
            headers=headers,
        )

        cancel_resp = client.delete(
            f"/api/v1/approvals/{approval_id}",
            headers=headers,
        )
        assert cancel_resp.status_code == 400


class TestApprovalViaGateway:
    """Test approval via gateway.create_approval_request (async) with mocked DB."""

    @pytest.mark.asyncio
    async def test_gateway_create_and_notify(self, ceo_id):
        from app.approval.gateway import ApprovalGateway

        with patch.object(ApprovalGateway, "get_db") as mock_get_db, patch.object(
            ApprovalGateway,
            "_notify_agent",
            new_callable=AsyncMock,
        ):
            mock_session = MagicMock()
            mock_session.__aenter__.return_value = mock_session
            mock_get_db.return_value = mock_session
            approval_id = uuid4()

            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.refresh = MagicMock()
            mock_session.close = MagicMock()

            mock_uuid = MagicMock()
            mock_uuid.__aenter__ = AsyncMock(return_value=approval_id)

            gateway = ApprovalGateway()
            with patch.object(gateway.notifier, "notify_ceo", new_callable=AsyncMock):
                result = await gateway.create_approval_request(
                    business_id=uuid4(),
                    task_id=uuid4(),
                    proposal={"title": "Test", "impact_analysis": {}},
                    urgency="normal",
                )
                assert result is not None

    @pytest.mark.asyncio
    async def test_gateway_process_decision(self, ceo_id):
        from app.approval.gateway import ApprovalGateway

        with patch.object(ApprovalGateway, "get_db") as mock_get_db, patch.object(
            ApprovalGateway,
            "_notify_agent",
            new_callable=AsyncMock,
        ):
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session
            mock_session.query = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.close = MagicMock()

            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = MagicMock(
                status="pending",
                task_id=uuid4(),
                expires_at=datetime.utcnow() + timedelta(hours=1),
            )

            gateway = ApprovalGateway()
            with patch.object(gateway.notifier, "notify_ceo", new_callable=AsyncMock):
                result = await gateway.process_decision(
                    approval_id=uuid4(),
                    ceo_id=ceo_id,
                    decision="approve",
                    comments="Approved",
                )
                assert result is True

    @pytest.mark.asyncio
    async def test_gateway_rejects(self, ceo_id):
        from app.approval.gateway import ApprovalGateway

        with patch.object(ApprovalGateway, "get_db") as mock_get_db, patch.object(
            ApprovalGateway,
            "_notify_agent",
            new_callable=AsyncMock,
        ):
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session
            mock_session.query = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.close = MagicMock()

            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = MagicMock(
                status="pending",
                task_id=uuid4(),
                expires_at=datetime.utcnow() + timedelta(hours=1),
            )

            gateway = ApprovalGateway()
            with patch.object(gateway.notifier, "notify_ceo", new_callable=AsyncMock):
                result = await gateway.process_decision(
                    approval_id=uuid4(),
                    ceo_id=ceo_id,
                    decision="reject",
                    comments="Rejected",
                )
                assert result is False


class TestApprovalEdgeCases:
    """Edge cases and error handling for approvals."""

    def _create_business(self, client, ceo_id, headers):
        resp = client.post(
            "/api/v1/businesses/create",
            json={"idea": "Test business for edge case", "ceo_id": str(ceo_id)},
            headers=headers,
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_approval_not_found(self, client, ceo_id):
        headers = _auth_header(ceo_id)
        fake_id = uuid4()
        resp = client.get(f"/api/v1/approvals/{fake_id}", headers=headers)
        assert resp.status_code == 404

    def test_update_pending_approval(self, client, ceo_id):
        headers = _auth_header(ceo_id)
        business_id = self._create_business(client, ceo_id, headers)
        resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "Update me",
                "proposed_changes": {"original": True},
            },
            headers=headers,
        )
        approval_id = resp.json()["id"]

        update_resp = client.patch(
            f"/api/v1/approvals/{approval_id}",
            json={"title": "Updated Title", "description": "Updated desc"},
            headers=headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated desc"
        assert data["status"] == "pending"

    def test_create_approval_with_empty_proposal(self, client, ceo_id):
        headers = _auth_header(ceo_id)
        business_id = self._create_business(client, ceo_id, headers)
        resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "Empty proposal",
                "proposed_changes": {},
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"

    def test_list_all_approvals_no_auth(self, client):
        resp = client.get("/api/v1/approvals/")
        assert resp.status_code == 401

    def test_filter_approvals_by_status(self, client, ceo_id):
        headers = _auth_header(ceo_id)
        resp = client.get("/api/v1/approvals/?status_filter=pending", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
