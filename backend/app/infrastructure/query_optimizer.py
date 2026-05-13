"""
Query Performance Profiler & N+1 Detector
Utilities to identify and fix common database performance issues.
"""
import time
import logging
from functools import wraps
from typing import Any, Callable, TypeVar, ParamSpec
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger("db.performance")

# ---- N+1 Query Detection ----

class N1Detector:
    """
    Context manager to detect potential N+1 query patterns.

    Usage:
        with N1Detector("load_business_tasks") as detector:
            # Code that might trigger N+1 queries
            businesses = db.query(Business).all()
            for b in businesses:
                _ = b.tasks  # Might trigger N+1

        detector.report()  # Logs warning if N+1 detected
    """

    def __init__(self, label: str, threshold: int = 5):
        """
        Args:
            label: Descriptive label for this query section.
            threshold: Number of similar queries before flagging as N+1.
        """
        self.label = label
        self.threshold = threshold
        self.queries: list[dict] = []
        self._original_execute = None

    def __enter__(self):
        # Patch SQLAlchemy to track queries
        from sqlalchemy import engine
        self._original_execute = engine.Engine.execute
        engine.Engine.execute = self._tracked_execute  # type: ignore
        return self

    def __exit__(self, *args):
        if self._original_execute:
            engine.Engine.execute = self._original_execute

    def _tracked_execute(self, *args, **kwargs):
        start = time.perf_counter()
        result = self._original_execute(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000

        # Extract SQL statement
        statement = args[1] if len(args) > 1 else str(kwargs.get("statement", ""))
        self.queries.append({
            "statement": str(statement)[:200],
            "elapsed_ms": elapsed,
        })
        return result

    def report(self) -> list[dict]:
        """Analyze and log potential N+1 patterns."""
        if len(self.queries) > self.threshold:
            logger.warning(
                "⚠️  POTENTIAL N+1 DETECTED [%s]: %d queries executed",
                self.label,
                len(self.queries),
            )
            # Log unique statements
            unique_stmts = {}
            for q in self.queries:
                stmt = q["statement"]
                if stmt not in unique_stmts:
                    unique_stmts[stmt] = {"count": 0, "total_ms": 0}
                unique_stmts[stmt]["count"] += 1
                unique_stmts[stmt]["total_ms"] += q["elapsed_ms"]

            for stmt, stats in unique_stmts.items():
                if stats["count"] > 1:
                    logger.warning(
                        "   Repeated %dx (avg %.1fms): %s...",
                        stats["count"],
                        stats["total_ms"] / stats["count"],
                        stmt[:100],
                    )
        return self.queries


# ---- Query Timing Decorator ----

P = ParamSpec("P")
R = TypeVar("R")


def log_query_time(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that logs database query execution time.
    Useful for identifying slow queries during development.

    Usage:
        @log_query_time
        def get_business_with_tasks(db: Session, business_id: UUID) -> Business:
            query = select(Business).where(Business.id == business_id).options(
                selectinload(Business.tasks)
            )
            return db.execute(query).scalar_one()
    """
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if elapsed_ms > 100:  # Log queries slower than 100ms
            logger.warning(
                "🐢 Slow query [%s]: %.1fms",
                func.__name__,
                elapsed_ms,
            )
        else:
            logger.debug(
                "✓ Query [%s]: %.1fms",
                func.__name__,
                elapsed_ms,
            )
        return result
    return wrapper


# ---- SQLAlchemy Event Listener for Query Counting ----

_query_counts: dict[str, int] = {}
_query_total_time: dict[str, float] = {}


def install_query_monitor(engine: Engine):
    """
    Install SQLAlchemy event listeners to track all queries.

    Usage:
        from app.database import engine
        install_query_monitor(engine)
    """
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start_times = conn.info.get("query_start_time", [])
        if start_times:
            elapsed = (time.perf_counter() - start_times.pop()) * 1000
            # Track by statement pattern (simplified — strip parameters)
            stmt_key = statement.split("WHERE")[0].strip()[:80] if "WHERE" in statement else statement[:80]
            _query_counts[stmt_key] = _query_counts.get(stmt_key, 0) + 1
            _query_total_time[stmt_key] = _query_total_time.get(stmt_key, 0) + elapsed


def get_query_stats() -> dict[str, Any]:
    """Get accumulated query statistics."""
    stats = []
    for stmt, count in _query_counts.items():
        avg_time = (_query_total_time.get(stmt, 0) / count) if count > 0 else 0
        stats.append({
            "query": stmt,
            "count": count,
            "avg_ms": round(avg_time, 2),
            "total_ms": round(_query_total_time.get(stmt, 0), 2),
        })
    stats.sort(key=lambda x: x["total_ms"], reverse=True)
    return {"total_unique_queries": len(stats), "queries": stats}


def reset_query_stats():
    """Reset query statistics counters."""
    _query_counts.clear()
    _query_total_time.clear()


# ---- Eager Loading Helper ----

def eager_load_options(relations: list[str]):
    """
    Helper to create selectinload options for common query patterns.

    Usage:
        businesses = db.query(Business).options(
            *eager_load_options(["tasks", "metrics"])
        ).all()

    Args:
        relations: List of relationship names to eagerly load.

    Returns:
        List of selectinload options for SQLAlchemy queries.
    """
    from sqlalchemy.orm import selectinload
    return [selectinload(relation) for relation in relations]