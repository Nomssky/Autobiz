import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from uuid import UUID

from app.agents.designer import DesignerAgent
from app.agents.developer import DeveloperAgent
from app.agents.finance import FinanceAgent
from app.agents.marketer import MarketerAgent
from app.agents.researcher import ResearcherAgent
from app.agents.support import SupportAgent
from app.agents.base_agent import AgentResult
from app.approval.gateway import approval_gateway
from app.approval.notifier import ApprovalNotifier
from app.database import get_db_session
from app.models import Business

logger = logging.getLogger(__name__)


class BusinessPhase(str, Enum):
    INITIALIZATION = "initialization"
    RESEARCH = "research"
    DEVELOPMENT = "development"
    DESIGN = "design"
    MARKETING_PREP = "marketing_prep"
    FINANCE_SETUP = "finance_setup"
    LAUNCH = "launch"
    OPERATING = "operating"
    SCALING = "scaling"
    ARCHIVED = "archived"


class PhaseManager:
    """Manages business lifecycle phases and orchestrates AI agents"""

    def __init__(self, business_id: UUID):
        self.business_id = business_id
        self.agents: Dict[str, Any] = {}
        self.notifier = ApprovalNotifier()
        self._operation_active = False

    async def initialize_agents(self):
        """Initialize all AI agents for this business"""
        config = self._load_business_config()

        self.agents = {
            "researcher": ResearcherAgent(self.business_id, config.get("researcher", {})),
            "developer": DeveloperAgent(self.business_id, config.get("developer", {})),
            "designer": DesignerAgent(self.business_id, config.get("designer", {})),
            "marketer": MarketerAgent(self.business_id, config.get("marketer", {})),
            "finance": FinanceAgent(self.business_id, config.get("finance", {})),
            "support": SupportAgent(self.business_id, config.get("support", {})),
        }
        logger.info(f"Initialized {len(self.agents)} agents for business {self.business_id}")

    async def execute_build_phase(self, business_idea: str) -> Dict[str, Any]:
        """Execute complete build phase from idea to launch"""

        logger.info(f"Starting build phase for business {self.business_id}")

        # Track phase results
        phase_results: Dict[str, Any] = {}

        # --- Phase 1: Research ---
        logger.info("Phase 1: Market Research")
        try:
            research_result = await self.agents["researcher"].execute_task(
                "validate_business_idea", {"idea": business_idea}
            )
        except Exception as e:
            logger.error(f"Research phase failed: {e}")
            return {"success": False, "phase": "research", "error": str(e)}

        if not research_result.success:
            return {"success": False, "phase": "research", "error": research_result.error}

        phase_results["research"] = research_result.output
        self._update_phase(BusinessPhase.RESEARCH, research_result.output)

        # --- Phase 2: Development ---
        logger.info("Phase 2: Development")
        research_out = research_result.output or {}
        dev_spec = {
            "business_name": research_out.get("business_name", "Unknown"),
            "description": research_out.get("description", ""),
            "features": research_out.get("recommended_features", []),
            "tech_stack": research_out.get("tech_stack", "default"),
        }

        try:
            dev_result = await self.agents["developer"].execute_task(
                "generate_application", dev_spec
            )
        except Exception as e:
            logger.error(f"Development phase failed: {e}")
            return {"success": False, "phase": "development", "error": str(e)}

        if not dev_result.success:
            return {"success": False, "phase": "development", "error": dev_result.error}

        phase_results["development"] = dev_result.output
        self._update_phase(BusinessPhase.DEVELOPMENT, dev_result.output)

        # If development requires approval, wait for it
        if dev_result.requires_approval and dev_result.approval_proposal:
            approved = await self._wait_for_approval(dev_result.approval_proposal, urgency="high")
            if not approved:
                return {
                    "success": False,
                    "phase": "development",
                    "error": "CEO rejected development",
                }

        # --- Phase 3: Design ---
        logger.info("Phase 3: Design")
        try:
            design_result = await self.agents["designer"].execute_task(
                "create_brand_identity",
                {
                    "business_name": research_out.get("business_name", "Unknown"),
                    "target_audience": research_out.get("target_audience", []),
                    "brand_personality": research_out.get("brand_personality", "professional"),
                },
            )
        except Exception as e:
            logger.error(f"Design phase failed: {e}")
            design_result = AgentResult(success=False, output={}, error=str(e))

        if design_result.success:
            phase_results["design"] = design_result.output
        self._update_phase(BusinessPhase.DESIGN, design_result.output or {})

        # --- Phase 4: Marketing Preparation ---
        logger.info("Phase 4: Marketing Strategy")
        try:
            marketing_result = await self.agents["marketer"].execute_task(
                "create_launch_strategy",
                {
                    "business_description": research_out.get("description", ""),
                    "target_audience": research_out.get("target_audience", []),
                    "unique_selling_points": research_out.get("usp", []),
                    "launch_timeline": "2 weeks",
                },
            )
        except Exception as e:
            logger.error(f"Marketing phase failed: {e}")
            marketing_result = AgentResult(success=False, output={}, error=str(e))

        if marketing_result.success:
            phase_results["marketing"] = marketing_result.output
        self._update_phase(BusinessPhase.MARKETING_PREP, marketing_result.output or {})

        # --- Phase 5: Finance Setup ---
        logger.info("Phase 5: Finance Configuration")
        try:
            finance_result = await self.agents["finance"].execute_task(
                "setup_pricing_and_payments",
                {
                    "business_model": research_out.get("business_model", "saas"),
                    "target_cac": research_out.get("estimated_cac", 50),
                    "target_ltv": research_out.get("estimated_ltv", 500),
                    "features": research_out.get("recommended_features", []),
                },
            )
        except Exception as e:
            logger.error(f"Finance phase failed: {e}")
            finance_result = AgentResult(success=False, output={}, error=str(e))

        if finance_result.requires_approval and finance_result.approval_proposal:
            approved = await self._wait_for_approval(
                finance_result.approval_proposal, urgency="high"
            )
            if not approved:
                return {"success": False, "phase": "finance", "error": "CEO rejected pricing"}

        if finance_result.success:
            phase_results["finance"] = finance_result.output
        self._update_phase(BusinessPhase.FINANCE_SETUP, finance_result.output or {})

        # --- Phase 6: Launch ---
        logger.info("Phase 6: Launching Business")

        launch_proposal = {
            "title": f"LAUNCH: {research_out.get('business_name', 'Business')}",
            "description": f"Ready to launch {research_out.get('business_name', 'business')}",
            "impact_analysis": {
                "initial_investment": (phase_results.get("finance") or {}).get("setup_cost", 0),
                "projected_monthly_revenue": (phase_results.get("finance") or {})
                .get("financial_projections", {})
                .get("month_12_revenue", 0),
                "break_even_month": (phase_results.get("finance") or {})
                .get("financial_projections", {})
                .get("break_even_month", 6),
            },
            "staging_url": (phase_results.get("development") or {}).get("staging_url", ""),
            "design_preview": (phase_results.get("design") or {}).get("preview_url", ""),
        }

        approved = await self._wait_for_approval(launch_proposal, urgency="critical")

        if not approved:
            return {"success": False, "phase": "launch", "error": "CEO rejected launch"}

        # Execute launch
        launch_result = await self._execute_launch(phase_results)

        if launch_result["success"]:
            self._update_phase(
                BusinessPhase.OPERATING, {"launched_at": datetime.utcnow().isoformat()}
            )
            await self.notifier.notify_ceo_about_approval(
                {
                    "title": f"Business Launched: {research_out.get('business_name', 'Business')}",
                    "description": f"Successfully launched at {launch_result.get('url', 'N/A')}",
                    "urgency": "normal",
                    "business_id": str(self.business_id),
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

        return {
            "success": launch_result["success"],
            "business_url": launch_result.get("url"),
            "phases": phase_results,
        }

    async def execute_operate_phase(self) -> Dict[str, Any]:
        """Execute continuous operation phase"""

        logger.info(f"Starting operate phase for business {self.business_id}")
        self._operation_active = True

        # Start background operation tasks concurrently
        operation_tasks = [
            self._continuous_support(),
            self._continuous_marketing(),
            self._continuous_monitoring(),
            self._continuous_optimization(),
        ]

        await asyncio.gather(*operation_tasks, return_exceptions=True)

        return {"success": True, "operations_running": len(operation_tasks), "status": "operating"}

    async def stop_operate_phase(self):
        """Stop the continuous operation phase"""
        self._operation_active = False
        logger.info(f"Stopped operate phase for business {self.business_id}")

    async def _continuous_support(self):
        """Run support agent continuously"""
        while self._operation_active:
            try:
                result = await self.agents["support"].execute_task(
                    "process_pending_tickets", {"batch_size": 20}
                )

                if result.success:
                    processed = result.output.get("processed_count", 0)
                    if processed > 0:
                        logger.info(f"Support: Processed {processed} tickets")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Support agent error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _continuous_marketing(self):
        """Run marketing agent on schedule"""
        while self._operation_active:
            try:
                result = await self.agents["marketer"].execute_task("execute_scheduled_content", {})

                if result.success and result.output.get("posts_made", 0) > 0:
                    logger.info(f"Marketing: Posted {result.output['posts_made']} contents")

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Marketing agent error: {str(e)}")
                await asyncio.sleep(3600)

    async def _continuous_monitoring(self):
        """Monitor business metrics and alert on anomalies"""
        while self._operation_active:
            try:
                metrics = await self.agents["finance"].execute_task("get_current_metrics", {})

                if metrics.success:
                    anomalies = await self._detect_anomalies(metrics.output)

                    for anomaly in anomalies:
                        if anomaly["severity"] == "critical":
                            await self.notifier.send_system_alert(
                                anomaly["type"], anomaly["message"], severity="critical"
                            )

                        if anomaly["type"] == "revenue_drop":
                            await self.agents["marketer"].execute_task(
                                "create_retention_campaign", {"reason": anomaly["message"]}
                            )

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Monitoring error: {str(e)}")
                await asyncio.sleep(900)

    async def _continuous_optimization(self):
        """Continuously optimize business performance"""
        while self._operation_active:
            try:
                performance = await self.agents["finance"].execute_task(
                    "analyze_performance", {"period": "daily"}
                )

                if performance.success and performance.output.get("optimization_opportunities"):
                    for opportunity in performance.output["optimization_opportunities"]:
                        if opportunity.get("confidence", 0) > 0.8:
                            if opportunity.get("type") == "price_optimization":
                                result = await self.agents["finance"].execute_task(
                                    "optimize_pricing", opportunity
                                )
                                if result.requires_approval:
                                    logger.info(
                                        f"Price optimization needs approval: {result.approval_proposal}"
                                    )

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Optimization error: {str(e)}")
                await asyncio.sleep(7200)

    def _update_phase(self, phase: BusinessPhase, data: Dict[str, Any]):
        """Update business phase in database"""
        try:
            with get_db_session() as session:
                from sqlalchemy import select

                result = session.execute(
                    select(Business).where(Business.id == self.business_id)
                )
                business = result.scalar_one_or_none()
                if business:
                    business.current_phase = phase.value
                    business.extra_metadata = {**business.extra_metadata, phase.value: data}
                    session.commit()
                    logger.info(f"Phase updated to: {phase.value}")
        except Exception as e:
            logger.error(f"Phase update failed: {str(e)}")

    async def _wait_for_approval(self, proposal: Dict[str, Any], urgency: str = "normal") -> bool:
        """Wait for CEO approval on a proposal"""

        approval_id = await approval_gateway.create_approval_request(
            self.business_id, None, proposal, urgency
        )

        logger.info(f"Waiting for approval (ID: {approval_id}, urgency: {urgency})")

        timeout = 3600 if urgency == "critical" else 86400
        start_time = datetime.utcnow()

        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            try:
                with get_db_session() as session:
                    from app.models import ApprovalRequest
                    from sqlalchemy import select

                    result = session.execute(
                        select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
                    )
                    approval = result.scalar_one_or_none()

                    if approval:
                        if approval.status == "approved":
                            logger.info(f"Approval {approval_id} accepted")
                            return True
                        elif approval.status == "rejected":
                            logger.info(f"Approval {approval_id} rejected")
                            return False

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Approval polling error: {str(e)}")
                await asyncio.sleep(30)

        logger.warning(f"Approval {approval_id} timed out after {timeout}s")
        return False

    async def _execute_launch(self, phase_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual launch of the business"""

        dev_output = phase_results.get("development", {})

        if dev_output:
            try:
                deploy_result = await self.agents["developer"].execute_task(
                    "deploy",
                    {
                        "environment": (
                            "production" if dev_output.get("ready_for_deployment") else "staging"
                        ),
                        "version": dev_output.get("version", "1.0.0"),
                        "code": dev_output,
                        "changelog": "Initial launch",
                    },
                )
                if not deploy_result.success:
                    return {"success": False, "error": deploy_result.error}
            except Exception as e:
                logger.error(f"Launch deployment failed: {e}")
                return {"success": False, "error": str(e)}

        # Activate marketing campaigns
        try:
            marketing_budget = (phase_results.get("finance") or {}).get("setup_cost", 1000)
            await self.agents["marketer"].execute_task(
                "activate_launch_campaigns",
                {"launch_date": datetime.utcnow().isoformat(), "budget": marketing_budget},
            )
        except Exception as e:
            logger.warning(f"Marketing activation failed: {e}")

        # Update business record
        try:
            with get_db_session() as session:
                from sqlalchemy import select

                result = session.execute(
                    select(Business).where(Business.id == self.business_id)
                )
                business = result.scalar_one_or_none()
                if business:
                    business.status = "operating"
                    business.launched_at = datetime.utcnow()
                    session.commit()
        except Exception as e:
            logger.error(f"Business record update failed: {e}")

        return {
            "success": True,
            "url": (phase_results.get("development") or {}).get(
                "staging_url", "http://localhost:8000"
            ),
            "marketing_active": True,
        }

    async def _detect_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in business metrics"""
        anomalies = []

        if metrics.get("revenue_change_percent", 0) < -20:
            anomalies.append(
                {
                    "type": "revenue_drop",
                    "severity": "critical",
                    "message": f"Revenue dropped {abs(metrics['revenue_change_percent'])}%",
                }
            )

        if metrics.get("churn_rate", 0) > 0.1:
            anomalies.append(
                {
                    "type": "high_churn",
                    "severity": "high",
                    "message": f"Churn rate at {metrics['churn_rate'] * 100}%",
                }
            )

        if metrics.get("bug_count", 0) > 10:
            anomalies.append(
                {
                    "type": "bug_spike",
                    "severity": "high",
                    "message": f"{metrics['bug_count']} active bugs reported",
                }
            )

        return anomalies

    def _load_business_config(self) -> Dict[str, Any]:
        """Load business-specific configuration"""
        try:
            with get_db_session() as session:
                from sqlalchemy import select

                result = session.execute(
                    select(Business).where(Business.id == self.business_id)
                )
                business = result.scalar_one_or_none()
                return business.config if business else {}
        except Exception as e:
            logger.error(f"Config load failed for business {self.business_id}: {e}")
            raise
