"""Tests for metrics endpoints."""
import pytest
from uuid import uuid4
from starlette.testclient import TestClient

from app.main import app
from app.api.dependencies import get_db_session
from app.auth.jwt_handler import create_access_token


class TestMetricsEndpoints:
    """Test the /metrics endpoints."""

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
            id=uuid4(), name="TestBiz", description="Test",
            ceo_id=ceo_id, status="building", current_phase="initialization",
            business_metadata={}, extra_metadata={},
        )
        db_session.add(biz)
        db_session.flush()
        return biz.id

    def test_create_and_get_metric(self, db_session):
        ceo_id = uuid4()
        business_id = self._create_business(db_session, ceo_id)
        client = TestClient(app)
        headers = self._auth_headers(ceo_id)

        resp = client.post(
            "/api/v1/metrics/",
            json={
                "business_id": str(business_id),
                "recorded_by_role": "finance",
                "daily_revenue": 1500.50,
                "users_count": 400,
                "active_users_count": 320,
                "bug_count": 2,
            },
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["daily_revenue"] == 1500.5
        assert data["users_count"] == 400
        metric_id = data["id"]

        resp = client.get(f"/api/v1/metrics/{metric_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == metric_id

    def test_metrics_by_business(self, db_session):
        ceo_id = uuid4()
        business_id = self._create_business(db_session, ceo_id)
        client = TestClient(app)
        headers = self._auth_headers(ceo_id)

        client.post(
            "/api/v1/metrics/",
            json={
                "business_id": str(business_id),
                "recorded_by_role": "finance",
                "daily_revenue": 100.00,
                "users_count": 100,
            },
            headers=headers,
        )

        resp = client.get(f"/api/v1/metrics/?business_id={business_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["recorded_by_role"] == "finance"

    def test_realtime_metrics(self, db_session):
        ceo_id = uuid4()
        client = TestClient(app)
        headers = self._auth_headers(ceo_id)
        business_id = uuid4()

        resp = client.get(f"/api/v1/metrics/{business_id}/realtime", headers=headers)
        assert resp.status_code == 404

    def test_metric_summary(self, db_session):
        ceo_id = uuid4()
        client = TestClient(app)
        headers = self._auth_headers(ceo_id)
        business_id = uuid4()

        resp = client.get(f"/api/v1/metrics/{business_id}/summary", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("snapshot_count", 0) == 0 or "message" in data


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
