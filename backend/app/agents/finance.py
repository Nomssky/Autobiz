import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.base_agent import AgentResult, BaseAgent
from app.agents.schemas.finance_output import FinanceOutput
from app.config import settings

logger = logging.getLogger(__name__)

FINANCIAL_PROMPT = """You are a financial analyst. Create a financial plan for a business.

Business model: {business_model}
Target CAC: {target_cac}
Target LTV: {target_ltv}
Features: {features}

Return JSON with:
- pricing_tiers: array of {{name, price, currency, billing_cycle, features[]}}
- setup_cost: float (one-time setup)
- monthly_burn_rate: float
- runway_months: integer
- break_even_month: integer
- projected_revenue_month_12: float
- monthly_projections: array of {{month, revenue, cost, profit, cumulative_profit}} (12 months)
- unit_economics: {{cac, ltv, ltv_to_cac_ratio, payback_months, gross_margin}}
- risk_factors: array of financial risks

Return ONLY valid JSON."""


class FinanceAgent(BaseAgent):
    """AI Finance agent that handles financial planning and analysis using LLM"""

    def __init__(self, business_id: UUID, config: Dict[str, Any]):
        super().__init__(business_id, "finance", config)

    def get_tools(self) -> List:
        return []

    async def execute_task(
        self, task_type: str, input_data: Dict[str, Any], context: Optional[Dict] = None
    ) -> AgentResult:
        if task_type == "setup_pricing_and_payments":
            return await self._setup_pricing_and_payments(input_data)
        elif task_type == "setup_pricing":
            return await self._setup_pricing(input_data)
        elif task_type == "setup_stripe_payments":
            return await self._setup_stripe_payments(input_data)
        elif task_type == "track_revenue":
            return await self._track_revenue(input_data)
        elif task_type == "calculate_unit_economics":
            return await self._calculate_unit_economics(input_data)
        elif task_type == "create_invoice":
            return await self._create_invoice(input_data)
        elif task_type == "generate_financial_projection":
            return await self._generate_financial_projection(input_data)
        elif task_type == "get_current_metrics":
            return await self._get_current_metrics()
        elif task_type == "analyze_performance":
            return await self._analyze_performance(input_data)
        elif task_type == "optimize_pricing":
            return await self._optimize_pricing(input_data)
        else:
            return AgentResult(success=False, output=None, error=f"Unknown task type: {task_type}")

    async def _setup_pricing_and_payments(self, params: Dict[str, Any]) -> AgentResult:
        prompt = FINANCIAL_PROMPT.format(
            business_model=params.get("business_model", "saas"),
            target_cac=params.get("target_cac", 50),
            target_ltv=params.get("target_ltv", 500),
            features=json.dumps(params.get("features", [])),
        )
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a financial analyst.")
            output = json.loads(response)
            validated = FinanceOutput(**output)
            return AgentResult(
                success=True,
                output=validated.model_dump(),
                requires_approval=True,
                approval_proposal={
                    "title": "Approve pricing strategy",
                    "description": f"{len(output.get('pricing_tiers', []))} tiers, break-even month {output.get('break_even_month', 'N/A')}",
                },
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _setup_pricing(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Design pricing tiers for:
Business model: {params.get('business_model', 'saas')}
Target CAC: {params.get('target_cac', 50)}

Return JSON with pricing_tiers array of {{name, price, currency, billing_cycle, features[]}}"""
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a pricing strategist.")
            output = json.loads(response)
            return AgentResult(
                success=True,
                output=output,
                requires_approval=True,
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _setup_stripe_payments(self, params: Dict[str, Any]) -> AgentResult:
        stripe_key = settings.STRIPE_API_KEY or ""
        if not stripe_key or stripe_key == "your-stripe-api-key":
            return AgentResult(
                success=False,
                output=None,
                error="Stripe API key not configured. Set STRIPE_API_KEY in .env",
            )
        try:
            import stripe
            stripe.api_key = stripe_key
            account = stripe.Account.retrieve()
            return AgentResult(
                success=True,
                output={
                    "stripe_mode": "live",
                    "account_id": account.id,
                    "account_configured": True,
                    "payouts_enabled": account.payouts_enabled,
                },
                requires_approval=False,
            )
        except ImportError:
            return AgentResult(
                success=False,
                output=None,
                error="Stripe library not installed. Run: pip install stripe",
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=f"Stripe API error: {e}")

    async def _track_revenue(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Analyze revenue for period: {params.get('period', 'monthly')}
Segment by: {params.get('segment_by', 'plan')}

Return JSON with metrics: {{mrr, arr, new_revenue, churned_revenue, total_customers, avg_revenue_per_user, revenue_growth_rate}}"""
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a revenue analyst.")
            output = json.loads(response)
            return AgentResult(
                success=True,
                output=output,
                requires_approval=False,
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _calculate_unit_economics(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Calculate unit economics:
CAC total spend: {params.get('cac_total_spend', 50000)}
New customers: {params.get('cac_new_customers', 1000)}
ARPU: {params.get('avg_revenue_per_user', 132)}
Customer lifetime months: {params.get('avg_customer_lifetime_months', 24)}

Return JSON with: {{cac, ltv, ltv_to_cac_ratio, payback_months, gross_margin, health_assessment, recommendations[]}}"""
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a financial analyst.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False)
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _create_invoice(self, params: Dict[str, Any]) -> AgentResult:
        stripe_key = settings.STRIPE_API_KEY or ""
        if not stripe_key or stripe_key == "your-stripe-api-key":
            return AgentResult(
                success=False,
                output=None,
                error="Stripe API key not configured. Set STRIPE_API_KEY in .env",
            )
        if not params.get("customer_id"):
            return AgentResult(
                success=False,
                output=None,
                error="customer_id is required to create an invoice",
            )
        try:
            import stripe
            stripe.api_key = stripe_key
            customer = stripe.Customer.retrieve(params["customer_id"])
            invoice = stripe.Invoice.create(
                customer=customer.id,
                collection_method="charge_automatically",
                days_until_due=30,
            )
            stripe.InvoiceItem.create(
                customer=customer.id,
                invoice=invoice.id,
                amount=int(float(params.get("amount", 0)) * 100),
                currency="usd",
            )
            invoice.finalize_invoice()
            return AgentResult(
                success=True,
                output={
                    "invoice_id": invoice.id,
                    "customer_id": customer.id,
                    "amount": params.get("amount", 0),
                    "status": invoice.status,
                    "invoice_url": invoice.hosted_invoice_url,
                    "stripe_mode": "live",
                },
                requires_approval=False,
            )
        except ImportError:
            return AgentResult(
                success=False,
                output=None,
                error="Stripe library not installed. Run: pip install stripe",
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=f"Stripe invoice error: {e}")

    async def _generate_financial_projection(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Generate 12-month financial projections:
Current MRR: {params.get('current_mrr', 45200)}
Growth rate: {params.get('growth_rate', 0.12)}
Churn rate: {params.get('churn_rate', 0.03)}
Operating costs: {params.get('operating_costs', 25000)}

Return JSON with monthly_projections array of {{month, revenue, cost, profit, cumulative_profit}}
and summary with {{projected_mrr_12m, break_even_month}}"""
        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a financial modeling analyst."
            )
            output = json.loads(response)
            return AgentResult(
                success=True,
                output=output,
                requires_approval=False,
                tokens_used=getattr(self.llm, "last_token_usage", {}),
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _get_current_metrics(self) -> AgentResult:
        from app.database import get_db_session
        from app.models.metric import MetricSnapshot
        from sqlalchemy import desc, select

        try:
            with get_db_session() as session:
                result = session.execute(
                    select(MetricSnapshot)
                    .where(MetricSnapshot.business_id == self.business_id)
                    .order_by(desc(MetricSnapshot.created_at))
                    .limit(1)
                )
                latest = result.scalar_one_or_none()
                if not latest:
                    return AgentResult(
                        success=False,
                        output=None,
                        error=f"No metrics found for business {self.business_id}. Record metrics first via POST /api/v1/metrics/",
                    )
                return AgentResult(
                    success=True,
                    output={
                        "daily_revenue": float(latest.daily_revenue or 0),
                        "weekly_revenue": float(latest.weekly_revenue or 0),
                        "monthly_revenue": float(latest.monthly_revenue or 0),
                        "users_count": latest.users_count or 0,
                        "active_users_count": latest.active_users_count or 0,
                        "churn_rate": float(latest.churn_rate or 0),
                        "conversion_rate": float(latest.conversion_rate or 0),
                        "customer_acquisition_cost": float(latest.customer_acquisition_cost or 0),
                        "lifetime_value": float(latest.lifetime_value or 0),
                        "bug_count": latest.bug_count or 0,
                        "support_tickets_count": latest.support_tickets_count or 0,
                        "open_support_tickets": latest.open_support_tickets or 0,
                    },
                    requires_approval=False,
                )
        except Exception as e:
            return AgentResult(success=False, output=None, error=f"Database query failed: {e}")

    async def _analyze_performance(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Analyze financial performance for period: {params.get('period', 'daily')}

Return JSON with: {{revenue_change_percent, expense_change_percent, profit_margin,
optimization_opportunities: [{{type, description, confidence, estimated_impact}}],
anomalies: [], benchmarks: {{industry_avg_conversion, industry_avg_churn}}}}"""
        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a financial performance analyst."
            )
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False)
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _optimize_pricing(self, params: Dict[str, Any]) -> AgentResult:
        prompt = """Optimize pricing strategy for:
Current price sensitivity: moderate
Competitor positioning: mid-market

Return JSON with: {current_analysis: {price_sensitivity, demand_elasticity, competitor_positioning},
recommendation: {action, details, expected_impact},
implementation_steps: []}"""
        try:
            response = await self.llm.ainvoke(
                prompt, system_prompt="You are a pricing optimization analyst."
            )
            output = json.loads(response)
            return AgentResult(
                success=True,
                output=output,
                requires_approval=True,
                approval_proposal={
                    "title": "Approve pricing changes",
                    "description": output.get("recommendation", {}).get("action", ""),
                },
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))
