import os
import sys
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.orchestrator.phase_manager import BusinessPhase, PhaseManager


@pytest.fixture
def phase_manager():
    """Create a PhaseManager instance with mocked database"""
    with patch("app.orchestrator.phase_manager.get_db_session"), patch(
        "app.orchestrator.phase_manager.approval_gateway"
    ), patch("app.orchestrator.phase_manager.NotificationService"):
        pm = PhaseManager(uuid4())
        pm.agents = {}
        pm.notifier = Mock()
        yield pm


@pytest.mark.asyncio
async def test_phase_manager_initialization(phase_manager):
    """Test that PhaseManager initializes correctly"""
    assert phase_manager.business_id is not None
    assert phase_manager.agents == {}
    assert phase_manager.notifier is not None


@pytest.mark.asyncio
async def test_business_phase_enum():
    """Test BusinessPhase enum values"""
    assert BusinessPhase.INITIALIZATION.value == "initialization"
    assert BusinessPhase.RESEARCH.value == "research"
    assert BusinessPhase.DEVELOPMENT.value == "development"
    assert BusinessPhase.DESIGN.value == "design"
    assert BusinessPhase.MARKETING_PREP.value == "marketing_prep"
    assert BusinessPhase.FINANCE_SETUP.value == "finance_setup"
    assert BusinessPhase.LAUNCH.value == "launch"
    assert BusinessPhase.OPERATING.value == "operating"
    assert BusinessPhase.SCALING.value == "scaling"
    assert BusinessPhase.ARCHIVED.value == "archived"


@pytest.mark.asyncio
async def test_detect_anomalies_revenue_drop(phase_manager):
    """Test anomaly detection for revenue drops"""
    metrics = {"revenue_change_percent": -25, "churn_rate": 0.05, "bug_count": 2}
    anomalies = await phase_manager._detect_anomalies(metrics)

    assert len(anomalies) > 0
    assert any(a["type"] == "revenue_drop" for a in anomalies)
    anomaly = next(a for a in anomalies if a["type"] == "revenue_drop")
    assert anomaly["severity"] == "critical"
    assert "25" in anomaly["message"]


@pytest.mark.asyncio
async def test_detect_anomalies_high_churn(phase_manager):
    """Test anomaly detection for high churn"""
    metrics = {"revenue_change_percent": 5, "churn_rate": 0.15, "bug_count": 2}
    anomalies = await phase_manager._detect_anomalies(metrics)

    assert any(a["type"] == "high_churn" for a in anomalies)
    anomaly = next(a for a in anomalies if a["type"] == "high_churn")
    assert anomaly["severity"] == "high"


@pytest.mark.asyncio
async def test_detect_anomalies_bug_spike(phase_manager):
    """Test anomaly detection for bug spike"""
    metrics = {"revenue_change_percent": 5, "churn_rate": 0.05, "bug_count": 15}
    anomalies = await phase_manager._detect_anomalies(metrics)

    assert any(a["type"] == "bug_spike" for a in anomalies)
    anomaly = next(a for a in anomalies if a["type"] == "bug_spike")
    assert anomaly["severity"] == "high"
    assert "15" in anomaly["message"]


@pytest.mark.asyncio
async def test_detect_anomalies_no_anomalies(phase_manager):
    """Test anomaly detection with healthy metrics"""
    metrics = {"revenue_change_percent": 5, "churn_rate": 0.02, "bug_count": 2}
    anomalies = await phase_manager._detect_anomalies(metrics)

    assert len(anomalies) == 0


@pytest.mark.asyncio
async def test_stop_operate_phase(phase_manager):
    """Test stopping the operate phase"""
    phase_manager._operation_active = True
    assert phase_manager._operation_active is True

    await phase_manager.stop_operate_phase()
    assert phase_manager._operation_active is False
