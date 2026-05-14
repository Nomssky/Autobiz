#!/usr/bin/env python3
"""Database initialization and setup script for AutoBiz Engine."""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def get_database_url():
    """Get database URL from environment or use default."""
    return os.getenv("DATABASE_URL", "postgresql://user:password@localhost/autobiz_engine")


def init_database():
    """Initialize database tables from SQLAlchemy models."""
    from app.database import engine, init_db

    print("Connecting to database...")
    print(f"Engine: {engine.url}")

    try:
        # Create all tables defined by models
        init_db()
        print("✅ All tables created successfully!")

        # Verify tables exist
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\nTables created ({len(tables)}):")
        for table in sorted(tables):
            print(f"  - {table}")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        raise


def drop_database():
    """Drop all database tables."""
    from app.database import drop_db, engine

    confirm = input("Are you sure you want to drop ALL tables? (yes/no): ")
    if confirm.lower() != "yes":
        print("Aborted.")
        return False

    try:
        drop_db()
        print("✅ All tables dropped successfully!")

        # Verify tables are gone
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if tables:
            print(f"Warning: {len(tables)} tables still exist: {tables}")
        else:
            print("No tables remaining.")

        return True

    except Exception as e:
        print(f"❌ Failed to drop tables: {e}")
        raise


def run_migrations():
    """Run Alembic migrations."""
    import subprocess

    backend_dir = Path(__file__).parent.parent / "backend"
    result = subprocess.run(
        ["alembic", "upgrade", "head"], cwd=str(backend_dir), capture_output=True, text=True
    )

    if result.returncode == 0:
        print("✅ Migrations applied successfully!")
        print(result.stdout)
    else:
        print(f"❌ Migration failed: {result.stderr}")
        print(result.stdout)

    return result.returncode == 0


def check_connection():
    """Check database connectivity."""
    from app.database import get_engine

    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(engine.dialect.text("SELECT 1"))
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AutoBiz Engine Database Setup")
    parser.add_argument(
        "action", choices=["init", "drop", "migrate", "check", "full"], help="Action to perform"
    )

    args = parser.parse_args()

    if args.action == "check":
        check_connection()
    elif args.action == "init":
        init_database()
    elif args.action == "drop":
        drop_database()
    elif args.action == "migrate":
        run_migrations()
    elif args.action == "full":
        print("Running full database setup...")
        check_connection()
        init_database()
        run_migrations()
        print("\n✅ Full setup complete!")


if __name__ == "__main__":
    main()
