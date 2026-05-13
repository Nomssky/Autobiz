'use client';

interface MetricCardProps {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  icon: React.ReactNode;
  color?: string;
}

export function MetricCard({ title, value, change, trend, icon, color = 'text-blue-400' }: MetricCardProps) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-400">{title}</span>
        <span className={color}>{icon}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className={`text-sm mt-1 ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
        {trend === 'up' ? '↑' : '↓'} {change} vs last period
      </p>
    </div>
  );
}