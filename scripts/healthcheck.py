#!/usr/bin/env python3
"""Health check script — verifies API and database connectivity."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database import get_engine  # noqa: E402


def check_database():
    """Test database connectivity and table existence."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            assert result.scalar() == 1
        print("✅ Database: connected")
        return True
    except Exception as e:
        print(f"❌ Database: {e}")
        return False


def check_tables():
    """Verify all expected tables exist."""
    try:
        from app.database import engine

        inspector = __import__("sqlalchemy").inspect(engine)
        tables = inspector.get_table_names()
        expected = [
            "businesses",
            "ai_tasks",
            "approval_requests",
            "deployments",
            "metrics_snapshots",
            "user_feedback",
            "agent_executions",
        ]
        missing = [t for t in expected if t not in tables]
        if missing:
            print(f"⚠️  Missing tables: {missing}")
            return False
        print(f"✅ Tables: {len(tables)} tables found")
        return True
    except Exception as e:
        print(f"❌ Tables: {e}")
        return False


def check_api():
    """Test API health endpoint."""
    try:
        import httpx

        with httpx.Client(timeout=10) as client:
            url = os.environ.get("API_URL", "http://localhost:8000")
            r = client.get(f"{url}/health")
            assert r.status_code == 200
            data = r.json()
            print(f"✅ API: {data.get('status')} (database: {data.get('database', '?')})")
            return True
    except Exception as e:
        print(f"❌ API: {e}")
        return False


def main():
    results = []
    results.append(("Database", check_database()))
    results.append(("Tables", check_tables()))
    results.append(("API", check_api()))

    print()
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"{'=' * 40}")
    print(f"Results: {passed}/{total}")

    if passed == total:
        print("✨ All checks passed!")
        sys.exit(0)
    else:
        print("❌ Some checks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
