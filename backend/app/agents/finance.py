from typing import Dict, Any, List, Optional
from uuid import UUID
import json
import logging
from app.agents.base_agent import BaseAgent, AgentResult
from app.agents.schemas.finance_output import FinanceOutput

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
        self,
        task_type: str,
        input_data: Dict[str, Any],
        context: Optional[Dict] = None
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
            return AgentResult(
                success=False,
                output=None,
                error=f"Unknown task type: {task_type}"
            )

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
            return AgentResult(success=True, output=output, requires_approval=True,
                               tokens_used=getattr(self.llm, "last_token_usage", {}))
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _setup_stripe_payments(self, params: Dict[str, Any]) -> AgentResult:
        return AgentResult(
            success=True,
            output={"stripe_mode": params.get("stripe_mode", "test"), "account_configured": True},
            requires_approval=False,
        )

    async def _track_revenue(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Analyze revenue for period: {params.get('period', 'monthly')}
Segment by: {params.get('segment_by', 'plan')}

Return JSON with metrics: {{mrr, arr, new_revenue, churned_revenue, total_customers, avg_revenue_per_user, revenue_growth_rate}}"""
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a revenue analyst.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False,
                               tokens_used=getattr(self.llm, "last_token_usage", {}))
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
        return AgentResult(
            success=True,
            output={
                "invoice_id": f"inv_{abs(hash(str(params.get('customer_id', '')))) % 10000000:07d}",
                "customer_id": params.get("customer_id", ""),
                "amount": params.get("amount", 0),
                "status": "draft",
            },
            requires_approval=params.get("amount", 0) > 10000,
        )

    async def _generate_financial_projection(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Generate 12-month financial projections:
Current MRR: {params.get('current_mrr', 45200)}
Growth rate: {params.get('growth_rate', 0.12)}
Churn rate: {params.get('churn_rate', 0.03)}
Operating costs: {params.get('operating_costs', 25000)}

Return JSON with monthly_projections array of {{month, revenue, cost, profit, cumulative_profit}}
and summary with {{projected_mrr_12m, break_even_month}}"""
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a financial modeling analyst.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False,
                               tokens_used=getattr(self.llm, "last_token_usage", {}))
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _get_current_metrics(self) -> AgentResult:
        return AgentResult(
            success=True,
            output={
                "daily_revenue": 1450.75,
                "weekly_revenue": 10155.25,
                "monthly_revenue": 45200.00,
                "users_count": 342,
                "active_users_count": 278,
                "churn_rate": 0.028,
                "conversion_rate": 0.045,
                "customer_acquisition_cost": 48.50,
                "lifetime_value": 3172.00,
                "bug_count": 3,
                "support_tickets_count": 12,
                "open_support_tickets": 5,
            },
            requires_approval=False,
        )

    async def _analyze_performance(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Analyze financial performance for period: {params.get('period', 'daily')}

Return JSON with: {{revenue_change_percent, expense_change_percent, profit_margin,
optimization_opportunities: [{{type, description, confidence, estimated_impact}}],
anomalies: [], benchmarks: {{industry_avg_conversion, industry_avg_churn}}}}"""
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a financial performance analyst.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=False)
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))

    async def _optimize_pricing(self, params: Dict[str, Any]) -> AgentResult:
        prompt = f"""Optimize pricing strategy for:
Current price sensitivity: moderate
Competitor positioning: mid-market

Return JSON with: {{current_analysis: {{price_sensitivity, demand_elasticity, competitor_positioning}},
recommendation: {{action, details, expected_impact}},
implementation_steps: []}}"""
        try:
            response = await self.llm.ainvoke(prompt, system_prompt="You are a pricing optimization analyst.")
            output = json.loads(response)
            return AgentResult(success=True, output=output, requires_approval=True,
                               approval_proposal={"title": "Approve pricing changes", "description": output.get("recommendation", {}).get("action", "")})
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))
