import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


@pytest.mark.asyncio
async def test_build_business_task_registered():
    """Test that build_business task is registered in Celery"""
    from app.workers.build_tasks import build_business
    assert build_business.name == "build_tasks.build_business"


@pytest.mark.asyncio
async def test_operate_business_task_registered():
    """Test that operate_business task is registered in Celery"""
    from app.workers.build_tasks import operate_business
    assert operate_business.name == "build_tasks.operate_business"


@pytest.mark.asyncio
async def test_continuous_support_task_registered():
    """Test that continuous_support task is registered"""
    from app.workers.operate_tasks import continuous_support
    assert continuous_support.name == "operate_tasks.continuous_support"


@pytest.mark.asyncio
async def test_continuous_marketing_task_registered():
    """Test that continuous_marketing task is registered"""
    from app.workers.operate_tasks import continuous_marketing
    assert continuous_marketing.name == "operate_tasks.continuous_marketing"


@pytest.mark.asyncio
async def test_monitor_metrics_task_registered():
    """Test that monitor_business_metrics task is registered"""
    from app.workers.monitoring_tasks import monitor_business_metrics
    assert monitor_business_metrics.name == "monitoring_tasks.monitor_business_metrics"


@pytest.mark.asyncio
async def test_monitor_support_task_registered():
    """Test that monitor_support_quality task is registered"""
    from app.workers.monitoring_tasks import monitor_support_quality
    assert monitor_support_quality.name == "monitoring_tasks.monitor_support_quality"


@pytest.mark.asyncio
async def test_health_check_task_registered():
    """Test that health_check task is registered"""
    from app.workers.monitoring_tasks import health_check
    assert health_check.name == "monitoring_tasks.health_check"


@pytest.mark.asyncio
async def test_process_phase_approvals_task_registered():
    """Test that process_phase_approvals task is registered"""
    from app.workers.build_tasks import process_phase_approvals
    assert process_phase_approvals.name == "build_tasks.process_phase_approvals"


@pytest.mark.asyncio
async def test_celery_app_config():
    """Test Celery app configuration"""
    from app.workers.celery_app import celery_app

    assert celery_app.conf.broker_url == "redis://localhost:6379/0"
    assert celery_app.conf.result_backend == "redis://localhost:6379/0"
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.task_time_limit == 3600


@pytest.mark.asyncio
async def test_send_support_report_task_registered():
    """Test that send_support_report task is registered"""
    from app.workers.operate_tasks import send_support_report
    assert send_support_report.name == "operate_tasks.send_support_report"
