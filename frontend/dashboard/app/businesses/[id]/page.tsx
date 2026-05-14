'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useRealtimeMetrics } from '@/hooks/useRealtimeMetrics';
import { useApprovals } from '@/hooks/useApprovals';
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';
import { MetricsBarChart, MetricsLineChart, MetricsAreaChart } from '@/components/ui/MetricsChart';

interface Props {
  params: { id: string };
}

function ApprovalCard({ title, status, urgency, amount, onClick }: {
  title: string;
  status: string;
  urgency: string;
  amount: string;
  onClick?: () => void;
}) {
  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-500/20 text-yellow-400',
    approved: 'bg-green-500/20 text-green-400',
    rejected: 'bg-red-500/20 text-red-400',
  };

  return (
    <div
      onClick={onClick}
      className={`flex items-center justify-between p-3 rounded-lg bg-slate-700/50 border border-slate-600 transition-colors ${
        onClick ? 'cursor-pointer hover:bg-slate-700/80' : ''
      }`}
    >
      <div>
        <p className="text-sm font-medium text-white">{title}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[status] || statusColors.pending}`}>
            {status}
          </span>
          <span className="text-xs text-slate-500">{urgency}</span>
        </div>
      </div>
      <span className="text-sm font-medium text-slate-300">{amount}</span>
    </div>
  );
}

function AgentActivityItem({ role, task, status, time }: {
  role: string;
  task: string;
  status: string;
  time: string;
}) {
  const statusColors: Record<string, string> = {
    completed: 'text-green-400',
    running: 'text-blue-400',
    pending: 'text-yellow-400',
    failed: 'text-red-400',
  };

  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
      <div>
        <p className="text-sm text-white font-medium">{role}</p>
        <p className="text-xs text-slate-400">
          {task} — <span className={statusColors[status] || 'text-slate-400'}>{status}</span>
        </p>
      </div>
      <p className="text-xs text-slate-500">{time}</p>
    </div>
  );
}

export default function BusinessDetailPage({ params }: Props) {
  const router = useRouter();
  const { id } = params;

  // Real-time metrics via polling hook
  const { metrics, loading: metricsLoading, error: metricsError } = useRealtimeMetrics({
    businessId: id,
    refreshInterval: 5000, // Update every 5 seconds
  });

  // Approvals with real-time updates
  const { approvals, loading: approvalsLoading, refetch: refetchApprovals } = useApprovals({
    businessId: id,
    skip: 0,
    limit: 10,
  });

  // Realtime WebSocket updates
  const { isConnected: wsConnected } = useRealtimeUpdates({
    businessId: id,
    onMetricsUpdate: () => {
      // Metrics updated via useRealtimeMetrics interval
    },
    onApprovalUpdate: () => {
      refetchApprovals();
    },
  });

  // Business data
  const [business, setBusiness] = useState<any>(null);
  const [businessLoading, setBusinessLoading] = useState(true);
  const [agentTasks, setAgentTasks] = useState<any[]>([]);

  const fetchBusiness = useCallback(async () => {
    try {
      const data = await api.getBusiness(id);
      setBusiness(data);
    } catch {
      setBusiness(null);
    } finally {
      setBusinessLoading(false);
    }
  }, [id]);

  const fetchAgentTasks = useCallback(async () => {
    try {
      // Fetch recent agent tasks from business timeline
      const timeline = await api.getBusinessTimeline(id);
      if (timeline?.phases) {
        setAgentTasks(
          timeline.phases
            .filter((p: any) => p.task_type !== 'init')
            .slice(0, 5)
            .map((p: any) => ({
              role: p.role_name,
              task: p.task_type.replace(/_/g, ' '),
              status: p.status === 'completed' ? 'completed' :
                      p.status === 'running' ? 'running' : 'pending',
              time: p.completed_at
                ? new Date(p.completed_at).toLocaleString()
                : p.created_at
                  ? new Date(p.created_at).toLocaleString()
                  : 'N/A',
            }))
        );
      }
    } catch {
      setAgentTasks([]);
    }
  }, [id]);

  useEffect(() => {
    fetchBusiness();
    fetchAgentTasks();
  }, [fetchBusiness, fetchAgentTasks]);

  // Derived metrics for charts
  const chartData = metrics
    ? [
        { name: 'Revenue', value: metrics.current.revenue },
        { name: 'Users', value: metrics.current.users },
        { name: 'Active', value: metrics.current.active_users },
        { name: 'Bugs', value: metrics.current.bugs },
        { name: 'Tickets', value: metrics.current.support_tickets },
      ]
    : [];

  const trendData = metrics
    ? [
        { name: 'Revenue Growth', value: metrics.trends.revenue_growth },
        { name: 'User Growth', value: metrics.trends.user_growth },
        { name: 'Churn Rate', value: metrics.trends.churn_rate },
      ]
    : [];

  if (businessLoading || metricsLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {business?.name || 'Business'}
          </h1>
          <p className="text-slate-400 mt-1">
            {business?.description || 'Monitor operations, approvals, and metrics'}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => router.push(`/businesses/${id}/approvals`)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors"
          >
            Manage Approvals
          </button>
          <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg font-medium text-sm transition-colors border border-slate-600">
            Archive
          </button>
        </div>
      </div>

      {/* Realtime connection status */}
      <div className="flex items-center gap-2 mb-6 text-sm text-slate-500">
        <span
          className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-yellow-500'}`}
        />
        <span>
          {wsConnected ? 'Live updates active' : 'Connecting...'} — refreshing every 5s
        </span>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Business Overview */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Business Overview</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-slate-500">Business ID</p>
                <p className="font-mono text-blue-400 text-sm">{business?.id || id}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Status</p>
                <span
                  className={`inline-block mt-1 px-3 py-1 rounded-full text-xs font-medium ${
                    business?.status === 'operating'
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                      : business?.status === 'building'
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
                  }`}
                >
                  {business?.status || 'Unknown'}
                </span>
              </div>
              <div>
                <p className="text-sm text-slate-500">CEO</p>
                <p className="text-sm text-slate-300">
                  {business?.ceo_id || 'CEO ID'}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Current Phase</p>
                <p className="text-sm text-slate-300 capitalize">
                  {business?.current_phase || 'N/A'}
                </p>
              </div>
            </div>

            {/* Alerts */}
            {metrics?.alerts && metrics.alerts.length > 0 && (
              <div className="mt-4 space-y-2">
                <h4 className="text-sm font-medium text-slate-300">Active Alerts</h4>
                <div className="flex flex-wrap gap-2">
                  {metrics.alerts.map((alert, i) => (
                    <span
                      key={i}
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        alert.type === 'error'
                          ? 'bg-red-500/20 text-red-400'
                          : alert.type === 'warning'
                          ? 'bg-yellow-500/20 text-yellow-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}
                    >
                      {alert.message}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Current Metrics Chart */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Live Metrics</h3>
            {metrics ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="h-64">
                  <MetricsBarChart
                    data={chartData}
                    dataKey="value"
                    name="Current Value"
                    color="#3b82f6"
                    height={200}
                  />
                </div>
                <div className="h-64">
                  <MetricsAreaChart
                    data={trendData}
                    dataKey="value"
                    name="Trend"
                    color="#10b981"
                    height={200}
                  />
                </div>
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">No metrics data available</p>
            )}
          </div>

          {/* Approvals */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recent Approvals</h3>
            {approvalsLoading ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto" />
              </div>
            ) : approvals.length > 0 ? (
              <div className="space-y-3">
                {approvals.map((approval: any) => (
                  <ApprovalCard
                    key={approval.id}
                    title={approval.title || 'Untitled'}
                    status={approval.status}
                    urgency={approval.urgency || 'normal'}
                    amount={approval.impact_analysis?.estimated_cost
                      ? `$${approval.impact_analysis.estimated_cost}`
                      : '—'}
                    onClick={() => router.push(`/businesses/${id}/approvals`)}
                  />
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-4">No approvals yet</p>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <button
                onClick={() => router.push(`/businesses/${id}/approvals/new`)}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors text-left"
              >
                + New Approval Request
              </button>
              <button className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg font-medium text-sm transition-colors text-left border border-slate-600">
                📊 Request Metrics Snapshot
              </button>
              <button className="w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg font-medium text-sm transition-colors text-left border border-slate-600">
                🔬 Run Semantic Search
              </button>
            </div>
          </div>

          {/* Agent Activity */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Agent Activity</h3>
            {agentTasks.length > 0 ? (
              <div className="space-y-3">
                {agentTasks.slice(0, 5).map((task, i) => (
                  <AgentActivityItem
                    key={i}
                    role={task.role}
                    task={task.task}
                    status={task.status}
                    time={task.time}
                  />
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-sm text-center py-4">No agent activity yet</p>
            )}
          </div>

          {/* Connection Status */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <h4 className="text-sm font-medium text-white mb-2">System Status</h4>
            <div className="space-y-2 text-xs text-slate-400">
              <div className="flex justify-between">
                <span>WebSocket</span>
                <span className={wsConnected ? 'text-green-400' : 'text-yellow-400'}>
                  {wsConnected ? 'Connected' : 'Connecting...'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Metrics</span>
                <span className={metrics ? 'text-green-400' : 'text-red-400'}>
                  {metrics ? 'Active' : 'Unavailable'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Approvals</span>
                <span className="text-blue-400">{approvals.length} total</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}