'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { MetricsAreaChart, MetricsBarChart, MetricsPieChart } from '@/components/ui/MetricsChart';
import { AgentActivityFeed } from '@/components/ui/AgentActivityFeed';

interface BusinessDetail {
  id: string;
  name: string;
  description: string | null;
  status: string;
  current_phase: string;
  created_at: string;
}

interface AgentTask {
  id: string;
  role_name: string;
  task_type: string;
  status: string;
  output_data?: any;
  created_at: string;
}

function RiskGauge({ score }: { score: number }) {
  const color = score > 70 ? 'text-red-400' : score > 40 ? 'text-yellow-400' : 'text-green-400';
  const bgColor = score > 70 ? 'bg-red-500' : score > 40 ? 'bg-yellow-500' : 'bg-green-500';
  const label = score > 70 ? 'High Risk' : score > 40 ? 'Medium Risk' : 'Low Risk';

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <h3 className="text-sm font-medium text-white mb-4">Risk Assessment</h3>
      <div className="flex flex-col items-center">
        <div className="relative w-32 h-32 mb-3">
          <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 36 36">
            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none" stroke="#334155" strokeWidth="3" />
            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none" stroke={bgColor} strokeWidth="3"
              strokeDasharray={`${score}, 100`} />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-2xl font-bold ${color}`}>{score}</span>
          </div>
        </div>
        <span className={`text-sm font-medium ${color}`}>{label}</span>
      </div>
    </div>
  );
}

function CompetitorTable({ competitors }: { competitors: any[] }) {
  if (!competitors?.length) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h3 className="text-sm font-medium text-white mb-4">Competitor Landscape</h3>
        <p className="text-sm text-slate-500 text-center py-8">No competitor data available</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <h3 className="text-sm font-medium text-white mb-4">Competitor Landscape</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left py-2 text-slate-400 font-medium">Name</th>
              <th className="text-right py-2 text-slate-400 font-medium">Market Share</th>
              <th className="text-right py-2 text-slate-400 font-medium">Strengths</th>
            </tr>
          </thead>
          <tbody>
            {competitors.map((c: any, i: number) => (
              <tr key={i} className="border-b border-slate-700/50">
                <td className="py-2 text-white">{c.name}</td>
                <td className="py-2 text-right text-slate-300">
                  {c.market_share != null ? `${c.market_share}%` : '—'}
                </td>
                <td className="py-2 text-right text-slate-300">
                  {c.strengths?.length ? c.strengths[0] : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function NextActionCard({ action }: { action: { title: string; description: string; priority: string } | null }) {
  if (!action) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h3 className="text-sm font-medium text-white mb-4">Recommended Next Action</h3>
        <p className="text-sm text-slate-500 text-center py-8">Awaiting agent analysis</p>
      </div>
    );
  }

  const priorityColors: Record<string, string> = {
    high: 'bg-red-500/20 text-red-400 border-red-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-green-500/20 text-green-400 border-green-500/30',
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <h3 className="text-sm font-medium text-white mb-4">Recommended Next Action</h3>
      <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-white">{action.title}</h4>
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${priorityColors[action.priority] || priorityColors.medium}`}>
            {action.priority}
          </span>
        </div>
        <p className="text-sm text-slate-400">{action.description}</p>
      </div>
    </div>
  );
}

function extractResearcherInsights(output: any) {
  if (!output) return null;
  try {
    const data = typeof output === 'string' ? JSON.parse(output) : output;
    return {
      market_size_usd: data.market_size_usd,
      opportunity_score: data.opportunity_score,
      competitors: data.competitors || [],
      target_audience: data.target_audience || [],
    };
  } catch {
    return null;
  }
}

function extractFinanceInsights(output: any) {
  if (!output) return null;
  try {
    const data = typeof output === 'string' ? JSON.parse(output) : output;
    return {
      monthly_projections: data.monthly_projections || data.financial_projections,
      setup_cost: data.setup_cost,
      break_even_month: data.break_even_month,
      pricing_tiers: data.pricing_tiers || data.pricing_strategy?.tiers,
    };
  } catch {
    return null;
  }
}

export default function IntelligencePage() {
  const params = useParams();
  const businessId = params.id as string;

  const [business, setBusiness] = useState<BusinessDetail | null>(null);
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!businessId) return;
    Promise.all([
      api.get(`/businesses/${businessId}`),
      api.get(`/businesses/${businessId}/timeline`),
    ]).then(([bizData, timelineData]) => {
      setBusiness(bizData);
      setTasks(timelineData.phases || []);
    }).catch((err: any) => {
      setError(err.message || 'Failed to load intelligence data');
    }).finally(() => {
      setLoading(false);
    });
  }, [businessId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 p-8">
        <div className="max-w-6xl mx-auto space-y-6 animate-pulse">
          <div className="h-8 bg-slate-800 rounded w-64" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-40 bg-slate-800 rounded-xl" />)}
          </div>
          <div className="h-80 bg-slate-800 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-2">Failed to load intelligence data</p>
          <p className="text-slate-500 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const researcherOutput = tasks.find(t => t.role_name === 'researcher')?.output_data;
  const financeOutput = tasks.find(t => t.role_name === 'finance')?.output_data;
  const devOutput = tasks.find(t => t.role_name === 'developer')?.output_data;

  const researcherInsights = extractResearcherInsights(researcherOutput);
  const financeInsights = extractFinanceInsights(financeOutput);

  const nextAction = tasks
    .filter(t => t.status === 'pending' || t.status === 'running')
    .map(t => ({
      title: t.task_type.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
      description: `Agent ${t.role_name} is processing this task`,
      priority: t.status === 'running' ? 'high' : 'medium',
    }))[0] || null;

  const opportunityScore = researcherInsights?.opportunity_score ?? 65;

  const costProjectionData = financeInsights?.monthly_projections
    ? (Array.isArray(financeInsights.monthly_projections)
        ? financeInsights.monthly_projections.map((p: any) => ({
            name: `M${p.month || p.month_ || p.monthly || ''}`,
            revenue: p.revenue || p.mrr || 0,
            cost: p.cost || p.expenses || 0,
            profit: p.profit || p.net_profit || 0,
          }))
        : Object.entries(financeInsights.monthly_projections).map(([k, v]: [string, any]) => ({
            name: k,
            revenue: v.revenue || v.mrr || 0,
            cost: v.cost || v.expenses || 0,
          })))
    : [];

  const pricingData = financeInsights?.pricing_tiers
    ? (Array.isArray(financeInsights.pricing_tiers)
        ? financeInsights.pricing_tiers.map((t: any) => ({
            name: t.name || t.tier || '',
            value: t.price || t.amount || 0,
          }))
        : [])
    : [];

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-white">Business Intelligence</h1>
          <p className="text-slate-400 mt-1">{business?.name || 'Loading...'}</p>
        </div>

        {/* Top KPI Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">Market Opportunity</p>
            <p className="text-2xl font-bold text-white">{opportunityScore}/100</p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">Setup Cost</p>
            <p className="text-2xl font-bold text-white">
              ${financeInsights?.setup_cost?.toLocaleString() || '—'}
            </p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">Break-Even</p>
            <p className="text-2xl font-bold text-white">
              {financeInsights?.break_even_month ? `Month ${financeInsights.break_even_month}` : '—'}
            </p>
          </div>
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <p className="text-xs text-slate-400 mb-1">Agent Tasks</p>
            <p className="text-2xl font-bold text-white">{tasks.length}</p>
          </div>
        </div>

        {/* Middle Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <RiskGauge score={opportunityScore} />
          <CompetitorTable competitors={researcherInsights?.competitors || []} />
          <NextActionCard action={nextAction} />
        </div>

        {/* Cost Projection Chart */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-sm font-medium text-white mb-4">12-Month Cost Projection</h3>
          {costProjectionData.length > 0 ? (
            <MetricsAreaChart
              data={costProjectionData}
              dataKey="revenue"
              name="Revenue"
              height={300}
            />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-slate-500 text-sm">
              No projection data available. Run a finance agent to generate projections.
            </div>
          )}
        </div>

        {/* Bottom Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Pricing Table */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-sm font-medium text-white mb-4">Pricing Tiers</h3>
            {pricingData.length > 0 ? (
              <MetricsPieChart
                data={pricingData}
                dataKey="value"
                name="Price"
                height={250}
              />
            ) : (
              <div className="flex items-center justify-center h-[250px] text-slate-500 text-sm">
                No pricing data available
              </div>
            )}
          </div>

          {/* Activity Feed */}
          <AgentActivityFeed
            title="Agent Activity"
            activities={tasks.map(t => ({
              role: t.role_name,
              task: t.task_type,
              status: (t.status as any),
              time: new Date(t.created_at).toLocaleDateString(),
            }))}
            businessId={businessId}
          />
        </div>
      </div>
    </div>
  );
}
