import type { Metadata } from 'next';
import { useState } from 'react';
import { BarChart3, LineChart, TrendingUp, DollarSign, Users, Bug, AlertTriangle } from 'lucide-react';
import { MetricsBarChart, MetricsLineChart, MetricsAreaChart, MetricsPieChart } from '@/components/ui/MetricsChart';
import { MetricCard } from '@/components/ui/MetricCard';
import { Alert } from '@/components/ui/Alert';

export const metadata: Metadata = {
  title: 'Metrics | AutoBiz',
};

// Sample chart data
const revenueData = Array.from({ length: 7 }, (_, i) => ({
  name: `Day ${i + 1}`,
  revenue: Math.floor(1200 + Math.random() * 800),
  users: Math.floor(50 + Math.random() * 30),
}));

const growthData = Array.from({ length: 12 }, (_, i) => ({
  name: `M${i + 1}`,
  users: Math.floor(100 + i * 25 + Math.random() * 20),
  revenue: Math.floor(2000 + i * 500 + Math.random() * 300),
}));

const distributionData = [
  { name: 'Starter', value: 150 },
  { name: 'Pro', value: 142 },
  { name: 'Enterprise', value: 50 },
];

const COLORS = ['#3b82f6', '#10b981', '#f59e0b'];

export default function MetricsPage() {
  const [timeframe, setTimeframe] = useState('7d');

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Metrics & Analytics</h1>
          <p className="text-slate-400">Real-time business performance monitoring</p>
        </div>
        <select
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-slate-200 px-4 py-2 rounded-lg text-sm"
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="ytd">Year to date</option>
        </select>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard
          title="Daily Revenue"
          icon={<DollarSign size={20} />}
          value="$1,450.75"
          change="+8.5%"
          trend="up"
          color="text-green-400"
        />
        <MetricCard
          title="Total Users"
          icon={<Users size={20} />}
          value="342"
          change="+3.2%"
          trend="up"
          color="text-blue-400"
        />
        <MetricCard
          title="Bug Count"
          icon={<Bug size={20} />}
          value="3"
          change="-12%"
          trend="down"
          color="text-red-400"
        />
        <MetricCard
          title="Open Tickets"
          icon={<AlertTriangle size={20} />}
          value="12"
          change="-2.8%"
          trend="down"
          color="text-yellow-400"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Revenue Trend</h3>
            <BarChart3 className="text-slate-400" size={18} />
          </div>
          <MetricsBarChart data={revenueData} dataKey="revenue" name="Revenue" color="#3b82f6" />
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">User Growth</h3>
            <LineChart className="text-slate-400" size={18} />
          </div>
          <MetricsLineChart data={growthData} dataKey="users" name="Users" color="#10b981" />
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Revenue Forecast</h3>
            <TrendingUp className="text-slate-400" size={18} />
          </div>
          <MetricsAreaChart data={growthData} dataKey="revenue" name="Revenue" color="#8b5cf6" />
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Plan Distribution</h3>
          </div>
          <MetricsPieChart data={distributionData} dataKey="value" name="Plan" />
        </div>
      </div>

      {/* Alerts */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Alerts & Notifications</h3>
        <div className="space-y-2">
          <Alert type="warning" message="3 bugs reported in the last 24 hours — review backlog" />
          <Alert type="success" message="Conversion rate improved by 2.1% this week" />
          <Alert type="info" message="Weekly metric snapshot recorded successfully" />
        </div>
      </div>
    </div>
  );
}