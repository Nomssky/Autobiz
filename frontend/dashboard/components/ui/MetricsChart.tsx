'use client';

import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart,
} from 'recharts';
import { useRealtimeMetrics } from '@/app/hooks/useRealtimeMetrics';

interface MetricChartProps {
  data?: any[];
  dataKey: string;
  name: string;
  color?: string;
  type?: 'bar' | 'line' | 'area' | 'pie';
  height?: number;
  businessId?: string;
  loading?: boolean;
  error?: string | null;
}

const CHART_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

function LoadingState({ height }: { height: number }) {
  return (
    <div style={{ height }} className="flex items-center justify-center text-slate-500 text-sm">
      <div className="animate-pulse flex flex-col items-center gap-2">
        <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        <span>Loading chart...</span>
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center h-full text-red-400 text-sm">
      <div className="flex flex-col items-center gap-2">
        <span className="text-lg">⚠</span>
        <span>{message}</span>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex items-center justify-center h-full text-slate-500 text-sm">
      <div className="flex flex-col items-center gap-2">
        <span className="text-lg text-slate-600">—</span>
        <span>No data available</span>
      </div>
    </div>
  );
}

export function MetricsBarChart({ data, dataKey, name, color = '#3b82f6', height = 300, loading, error }: MetricChartProps) {
  if (loading) return <LoadingState height={height} />;
  if (error) return <ErrorState message={error} />;
  if (!data?.length) return <EmptyState />;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
        <YAxis stroke="#94a3b8" fontSize={12} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#f1f5f9' }}
        />
        <Bar dataKey={dataKey} fill={color} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function MetricsLineChart({ data, dataKey, name, color = '#3b82f6', height = 300, loading, error }: MetricChartProps) {
  if (loading) return <LoadingState height={height} />;
  if (error) return <ErrorState message={error} />;
  if (!data?.length) return <EmptyState />;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
        <YAxis stroke="#94a3b8" fontSize={12} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#f1f5f9' }}
        />
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          dot={{ fill: color, r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function MetricsAreaChart({ data, dataKey, name, color = '#3b82f6', height = 300, loading, error }: MetricChartProps) {
  if (loading) return <LoadingState height={height} />;
  if (error) return <ErrorState message={error} />;
  if (!data?.length) return <EmptyState />;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id={`color-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
        <YAxis stroke="#94a3b8" fontSize={12} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#f1f5f9' }}
        />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          fillOpacity={1}
          fill={`url(#color-${dataKey})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function MetricsPieChart({ data, dataKey, name, height = 300, loading, error }: MetricChartProps) {
  if (loading) return <LoadingState height={height} />;
  if (error) return <ErrorState message={error} />;
  if (!data?.length) return <EmptyState />;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          dataKey={dataKey}
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={100}
          label
        >
          {data.map((_entry, index) => (
            <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
          labelStyle={{ color: '#f1f5f9' }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function RealtimeMetricsChart({ businessId, dataKey, name, color, type = 'area', height }: MetricChartProps) {
  const { metrics, loading, error } = useRealtimeMetrics({
    businessId: businessId || '',
    enabled: !!businessId,
    refreshInterval: 5000,
  });

  const chartData = metrics?.trends?.[dataKey]
    ? Object.entries(metrics.trends[dataKey]).map(([key, value]) => ({
        name: key,
        [dataKey]: value,
      }))
    : undefined;

  const props = { data: chartData, dataKey, name, color, height, loading, error };

  switch (type) {
    case 'bar':
      return <MetricsBarChart {...props} />;
    case 'line':
      return <MetricsLineChart {...props} />;
    case 'area':
      return <MetricsAreaChart {...props} />;
    case 'pie':
      return <MetricsPieChart {...props} />;
    default:
      return <MetricsAreaChart {...props} />;
  }
}
