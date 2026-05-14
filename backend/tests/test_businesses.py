"""Tests for business creation and management endpoints."""

from uuid import uuid4

import pytest
from app.api.dependencies import get_db_session
from app.auth.jwt_handler import create_access_token
from app.main import app
from starlette.testclient import TestClient


class TestBusinessEndpoints:
    """Test the /businesses endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        """Override the app's DB session dependency with the test session."""

        def _override_get_db():
            yield db_session

        app.dependency_overrides[get_db_session] = _override_get_db
        yield
        app.dependency_overrides.clear()

    def _auth_headers(self, ceo_id):
        token = create_access_token({"sub": str(ceo_id), "roles": ["ceo"]})
        return {"Authorization": f"Bearer {token}"}

    def test_create_business(self, db_session):
        """Test creating a new business."""
        ceo_id = uuid4()
        client = TestClient(app)
        response = client.post(
            "/api/v1/businesses/create",
            json={"idea": "AI-powered SaaS platform", "ceo_id": str(ceo_id)},
            headers=self._auth_headers(ceo_id),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "AI-powered SaaS platform"
        assert data["description"] == "AI-powered SaaS platform"
        assert data["status"] == "building"
        assert "id" in data
        assert "created_at" in data
        print("✅ test_create_business PASSED")

    def test_get_business(self, db_session):
        """Test creating and fetching a business."""
        ceo_id = uuid4()
        client = TestClient(app)
        headers = self._auth_headers(ceo_id)

        create_resp = client.post(
            "/api/v1/businesses/create",
            json={"idea": "Test business idea", "ceo_id": str(ceo_id)},
            headers=headers,
        )
        assert create_resp.status_code == 201
        business = create_resp.json()
        business_id = business["id"]

        get_resp = client.get(f"/api/v1/businesses/{business_id}", headers=headers)
        assert get_resp.status_code == 200
        fetched = get_resp.json()
        assert fetched["id"] == business_id
        assert fetched["name"] == "Test business idea"
        print("✅ test_get_business PASSED")

    def test_create_business_no_auth(self):
        """Test that unauthenticated requests are rejected."""
        client = TestClient(app)
        response = client.post(
            "/api/v1/businesses/create",
            json={"idea": "No auth", "ceo_id": str(uuid4())},
        )
        assert response.status_code == 401
        print("✅ test_create_business_no_auth PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
