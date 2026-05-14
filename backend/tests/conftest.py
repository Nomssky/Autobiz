"""Shared test fixtures for the AutoBiz Engine API test suite."""

from uuid import uuid4

import pytest
from app.models.approval_request import ApprovalRequest
from app.models.base import Base
from app.models.business import Business
from app.models.metric import MetricSnapshot
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use SQLite in-memory for fast, isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _fk_pragma_on_connect(dbapi_connection, connection_record):
    """Enable foreign key enforcement for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


event.listen(engine, "connect", _fk_pragma_on_connect)


@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db_engine):
    """Provide a transactional test session with rolled-back state."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def sample_business(db_session) -> Business:
    """Create a sample business for use in tests."""
    ceo_id = uuid4()
    business = Business(
        name="TestCo",
        description="A test business",
        ceo_id=ceo_id,
        status="building",
        current_phase="initialization",
    )
    db_session.add(business)
    db_session.flush()
    return business


@pytest.fixture()
def sample_approval(db_session, sample_business) -> ApprovalRequest:
    """Create a sample approval request linked to the sample business."""
    approval = ApprovalRequest(
        business_id=sample_business.id,
        title="Test Approval",
        description="A test approval request",
        proposed_changes={"key": "value"},
        impact_analysis={"impact": "low"},
        urgency="normal",
        status="pending",
    )
    db_session.add(approval)
    db_session.flush()
    return approval


@pytest.fixture()
def sample_metric(db_session, sample_business) -> MetricSnapshot:
    """Create a sample metric snapshot linked to the sample business."""
    metric = MetricSnapshot(
        business_id=sample_business.id,
        recorded_by_role="finance",
        daily_revenue=1450.75,
        weekly_revenue=10155.25,
        monthly_revenue=43500.00,
        users_count=342,
        active_users_count=278,
        churn_rate=0.028,
        bug_count=3,
        support_tickets_count=12,
        open_support_tickets=5,
        conversion_rate=0.045,
        customer_acquisition_cost=25.50,
        lifetime_value=480.00,
        custom_metrics={"nps_score": 72},
    )
    db_session.add(metric)
    db_session.flush()
    return metric


@pytest.fixture()
def ceo_id():
    """Return a fixed UUID representing an authenticated CEO user."""
    return uuid4()


@pytest.fixture()
def ceo_headers(ceo_id):
    """Return auth headers with a valid JWT for the test CEO."""
    from app.auth.jwt_handler import create_access_token

    token = create_access_token({"sub": str(ceo_id), "roles": ["ceo"]})
    return {"Authorization": f"Bearer {token}"}
