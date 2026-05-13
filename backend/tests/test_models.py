import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.business import Business
from app.models.agent_task import AgentTask
from app.models.approval_request import ApprovalRequest
from app.models.metric import MetricSnapshot
from app.models.user_feedback import UserFeedback
from app.models.deployment import Deployment

# Use SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_business_model(db_session):
    """Test creating a business."""
    business = Business(
        id=uuid4(),
        name="Test Business",
        description="A test business",
        ceo_id=uuid4(),
        status="building",
        current_phase="initialization"
    )
    db_session.add(business)
    db_session.commit()
    
    # Query the business
    queried_business = db_session.query(Business).filter(Business.id == business.id).first()
    assert queried_business is not None
    assert queried_business.name == "Test Business"
    assert queried_business.description == "A test business"
    assert queried_business.status == "building"

def test_agent_task_model(db_session):
    """Test creating an agent task."""
    business_id = uuid4()
    task = AgentTask(
        id=uuid4(),
        business_id=business_id,
        role_name="developer",
        task_type="generate_application",
        status="pending",
        priority=3
    )
    db_session.add(task)
    db_session.commit()
    
    # Query the task
    queried_task = db_session.query(AgentTask).filter(AgentTask.id == task.id).first()
    assert queried_task is not None
    assert queried_task.role_name == "developer"
    assert queried_task.task_type == "generate_application"
    assert queried_task.priority == 3

def test_approval_request_model(db_session):
    """Test creating an approval request."""
    business_id = uuid4()
    task_id = uuid4()
    approval = ApprovalRequest(
        id=uuid4(),
        business_id=business_id,
        task_id=task_id,
        title="Test Approval",
        description="A test approval request",
        proposed_changes={"key": "value"},
        impact_analysis={"impact": "low"},
        urgency="normal",
        status="pending"
    )
    db_session.add(approval)
    db_session.commit()
    
    # Query the approval request
    queried_approval = db_session.query(ApprovalRequest).filter(ApprovalRequest.id == approval.id).first()
    assert queried_approval is not None
    assert queried_approval.title == "Test Approval"
    assert queried_approval.description == "A test approval request"
    assert queried_approval.status == "pending"

def test_metric_snapshot_model(db_session):
    """Test creating a metric snapshot."""
    business_id = uuid4()
    metric = MetricSnapshot(
        id=uuid4(),
        business_id=business_id,
        recorded_by_role="finance",
        daily_revenue=100.50,
        weekly_revenue=700.00,
        monthly_revenue=3000.00,
        users_count=150,
        active_users_count=120
    )
    db_session.add(metric)
    db_session.commit()
    
    # Query the metric
    queried_metric = db_session.query(MetricSnapshot).filter(MetricSnapshot.id == metric.id).first()
    assert queried_metric is not None
    assert queried_metric.recorded_by_role == "finance"
    assert queried_metric.daily_revenue == 100.50
    assert queried_metric.users_count == 150

def test_user_feedback_model(db_session):
    """Test creating user feedback."""
    business_id = uuid4()
    feedback = UserFeedback(
        id=uuid4(),
        business_id=business_id,
        user_id="user123",
        feedback_type="bug",
        content="This is a test bug report",
        sentiment_score=-0.5
    )
    db_session.add(feedback)
    db_session.commit()
    
    # Query the feedback
    queried_feedback = db_session.query(UserFeedback).filter(UserFeedback.id == feedback.id).first()
    assert queried_feedback is not None
    assert queried_feedback.user_id == "user123"
    assert queried_feedback.feedback_type == "bug"
    assert queried_feedback.content == "This is a test bug report"
    assert queried_feedback.sentiment_score == -0.5

def test_deployment_model(db_session):
    """Test creating a deployment."""
    business_id = uuid4()
    deployment = Deployment(
        id=uuid4(),
        business_id=business_id,
        version="v1.0.0",
        environment="staging",
        status="deploying",
        triggered_by_role="developer"
    )
    db_session.add(deployment)
    db_session.commit()
    
    # Query the deployment
    queried_deployment = db_session.query(Deployment).filter(Deployment.id == deployment.id).first()
    assert queried_deployment is not None
    assert queried_deployment.version == "v1.0.0"
    assert queried_deployment.environment == "staging"
    assert queried_deployment.status == "deploying"