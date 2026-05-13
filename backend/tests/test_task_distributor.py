import pytest
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.orchestrator.task_distributor import TaskDistributor


@pytest.fixture
def distributor():
    return TaskDistributor()


def test_task_routing_exists():
    """Test that all expected task types have routes"""
    expected_tasks = [
        "validate_business_idea", "market_analysis", "competitor_research",
        "trend_analysis", "generate_application", "fix_bug", "implement_feature",
        "deploy", "generate_image", "create_logo", "design_banner", "edit_image",
        "create_brand_identity", "create_social_post", "write_blog_post",
        "create_email_campaign", "analyze_performance", "generate_hashtags",
        "setup_pricing_and_payments", "track_revenue", "calculate_unit_economics",
        "process_ticket", "auto_respond", "escalate_ticket",
        "search_knowledge_base", "analyze_sentiment", "generate_support_report",
    ]

    for task in expected_tasks:
        assert task in TaskDistributor.TASK_ROUTING, f"Missing route for {task}"


def test_priority_levels():
    """Test priority level mapping"""
    assert TaskDistributor.PRIORITY_LEVELS["critical"] == 5
    assert TaskDistributor.PRIORITY_LEVELS["high"] == 4
    assert TaskDistributor.PRIORITY_LEVELS["normal"] == 3
    assert TaskDistributor.PRIORITY_LEVELS["low"] == 2
    assert TaskDistributor.PRIORITY_LEVELS["background"] == 1


def test_add_task(distributor):
    """Test adding a task to the queue"""
    task_id = distributor.add_task(
        task_type="market_analysis",
        input_data={"idea": "Test business"},
        priority="high"
    )

    assert task_id is not None
    assert len(distributor.task_queue) == 1
    assert distributor.task_queue[0]["task_type"] == "market_analysis"
    assert distributor.task_queue[0]["priority"] == "high"
    assert distributor.task_queue[0]["priority_score"] == 4


def test_add_task_with_dependency(distributor):
    """Test adding a task with dependency tracking"""
    task_id = distributor.add_task(
        task_type="market_analysis",
        input_data={},
        depends_on=["dep_task_1"]
    )

    assert "dep_task_1" in distributor.pending_dependencies


def test_get_queue_status_empty(distributor):
    """Test queue status when empty"""
    status = distributor.get_queue_status()

    assert status["pending"] == 0
    assert status["completed"] == 0
    assert status["failed"] == 0
    assert status["is_processing"] is False


def test_priority_ordering(distributor):
    """Test that tasks are ordered by priority"""
    distributor.add_task("market_analysis", {}, priority="low")
    distributor.add_task("generate_application", {}, priority="critical")
    distributor.add_task("create_social_post", {}, priority="normal")

    # Critical should be first, then normal, then low
    priorities = [t["priority_score"] for t in distributor.task_queue]
    # Sort check: should be descending
    assert priorities == sorted(priorities, reverse=True)
