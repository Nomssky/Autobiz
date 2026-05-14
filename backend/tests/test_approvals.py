"""Tests for approval endpoints."""

from uuid import uuid4

import pytest
from app.api.dependencies import get_db_session
from app.auth.jwt_handler import create_access_token
from app.main import app
from starlette.testclient import TestClient


class TestApprovalEndpoints:
    """Test the /approvals endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        def _override_get_db():
            yield db_session

        app.dependency_overrides[get_db_session] = _override_get_db
        yield
        app.dependency_overrides.clear()

    def _auth_headers(self, ceo_id):
        token = create_access_token({"sub": str(ceo_id), "roles": ["ceo"]})
        return {"Authorization": f"Bearer {token}"}

    def _create_business(self, db_session, ceo_id):
        from app.models.business import Business

        biz = Business(
            id=uuid4(),
            name="TestBiz",
            description="Test",
            ceo_id=ceo_id,
            status="building",
            current_phase="initialization",
            business_metadata={},
            extra_metadata={},
        )
        db_session.add(biz)
        db_session.flush()
        return biz.id

    def test_create_and_get_approval(self, db_session):
        ceo_id = uuid4()
        business_id = self._create_business(db_session, ceo_id)
        client = TestClient(app)
        headers = self._auth_headers(ceo_id)

        resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "Test Approval",
                "description": "Test description",
                "proposed_changes": {"key": "value"},
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        approval_id = data["id"]
        assert data["status"] == "pending"

        resp = client.get(f"/api/v1/approvals/{approval_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == approval_id

    def test_pending_approvals(self, db_session):
        ceo_id = uuid4()
        business_id = self._create_business(db_session, ceo_id)
        client = TestClient(app)
        headers = self._auth_headers(ceo_id)

        client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "Pending Test",
                "proposed_changes": {"test": True},
            },
            headers=headers,
        )

        resp = client.get("/api/v1/approvals/pending", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_decide_approval(self, db_session):
        ceo_id = uuid4()
        business_id = self._create_business(db_session, ceo_id)
        client = TestClient(app)
        headers = self._auth_headers(ceo_id)

        resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "To approve",
                "proposed_changes": {"budget": 1000},
            },
            headers=headers,
        )
        approval_id = resp.json()["id"]

        resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"decision": "approve", "ceo_id": str(ceo_id), "comments": "Looks good"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["approved"] is True

    def test_reject_approval(self, db_session):
        ceo_id = uuid4()
        business_id = self._create_business(db_session, ceo_id)
        client = TestClient(app)
        headers = self._auth_headers(ceo_id)

        resp = client.post(
            "/api/v1/approvals/",
            json={
                "business_id": str(business_id),
                "title": "To reject",
                "proposed_changes": {"budget": 9999},
            },
            headers=headers,
        )
        approval_id = resp.json()["id"]

        resp = client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json={"decision": "reject", "ceo_id": str(ceo_id), "comments": "Budget too high"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["approved"] is False


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
