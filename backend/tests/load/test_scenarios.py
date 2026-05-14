"""
Test scenarios for creating 100 businesses simultaneously.
Run with: pytest tests/load/test_scenarios.py -v --tb=short
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import uuid4

import pytest
from app.api.dependencies import get_db_session
from app.main import app
from starlette.testclient import TestClient

NUM_BUSINESSES = 100
MAX_WORKERS = 20  # Concurrent threads


def _override_get_db():
    """Override dependency — reuse same session for all concurrent requests."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestConcurrentBusinessCreation:
    """Test creating 100 businesses simultaneously to validate load handling."""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        app.dependency_overrides[get_db_session] = _override_get_db
        yield
        app.dependency_overrides.clear()

    def test_create_100_businesses_concurrently(self, db_session):
        """Create 100 businesses in parallel and verify all succeed."""
        client = TestClient(app, raise_server_exceptions=False)
        results = []
        errors = []

        def create_business(index):
            ceo_id = str(uuid4())
            idea = f"Concurrent test business #{index} — AI SaaS for industry {index}"
            try:
                resp = client.post(
                    "/api/v1/businesses/create",
                    json={"idea": idea, "ceo_id": ceo_id},
                )
                return {"index": index, "status_code": resp.status_code, "response": resp.json()}
            except Exception as e:
                return {"index": index, "status_code": None, "error": str(e)}

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(create_business, i) for i in range(NUM_BUSINESSES)]
            for future in as_completed(futures):
                result = future.result()
                if result["status_code"] == 201:
                    results.append(result)
                else:
                    errors.append(result)

        elapsed = time.time() - start_time

        # Verify results
        success_count = len(results)
        error_count = len(errors)

        print(f"\n✅ Created {success_count}/{NUM_BUSINESSES} businesses in {elapsed:.2f}s")
        if errors:
            print(f"❌ Errors: {error_count}")
            for err in errors[:5]:  # Show first 5 errors
                print(
                    f"   Index {err['index']}: status={err['status_code']}, error={err.get('error', 'N/A')}"
                )

        # Assertions
        assert success_count == NUM_BUSINESSES, (
            f"Expected {NUM_BUSINESSES} successful creations, got {success_count}. "
            f"Errors: {error_count}"
        )
        assert elapsed < 60, f"Creating 100 businesses took {elapsed:.2f}s (> 60s threshold)"

        # Verify each business was persisted
        assert len(client.get("/api/v1/businesses/").json()) >= NUM_BUSINESSES

    def test_concurrent_list_during_creation(self, db_session):
        """Verify list endpoint remains responsive during concurrent writes."""
        client = TestClient(app, raise_server_exceptions=False)

        # Pre-create some businesses
        for i in range(10):
            client.post(
                "/api/v1/businesses/create",
                json={"idea": f"Pre-test business {i}", "ceo_id": str(uuid4())},
            )

        list_results = []
        list_errors = []

        def list_businesses():
            try:
                resp = client.get("/api/v1/businesses/")
                return {"status_code": resp.status_code, "count": len(resp.json())}
            except Exception as e:
                return {"status_code": None, "error": str(e)}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(list_businesses) for _ in range(20)]
            for future in as_completed(futures):
                result = future.result()
                if result["status_code"] == 200:
                    list_results.append(result)
                else:
                    list_errors.append(result)

        assert (
            len(list_results) == 20
        ), f"Expected 20 successful list calls, got {len(list_results)}"
        assert len(list_errors) == 0, f"List errors during load: {list_errors}"

    def test_api_responsiveness_under_load(self, db_session):
        """Verify API response times stay acceptable under load."""
        client = TestClient(app, raise_server_exceptions=False)
        response_times = []

        for i in range(50):
            ceo_id = str(uuid4())
            start = time.time()
            _ = client.post(
                "/api/v1/businesses/create",
                json={"idea": f"Perf test business {i}", "ceo_id": ceo_id},
            )
            elapsed_ms = (time.time() - start) * 1000
            response_times.append(elapsed_ms)

        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]

        print(f"\n⏱  Avg: {avg_time:.0f}ms | P95: {p95_time:.0f}ms | Max: {max_time:.0f}ms")

        # Thresholds: avg < 500ms, P95 < 1000ms
        assert avg_time < 500, f"Average response time {avg_time:.0f}ms exceeds 500ms threshold"
        assert p95_time < 1000, f"P95 response time {p95_time:.0f}ms exceeds 1000ms threshold"
