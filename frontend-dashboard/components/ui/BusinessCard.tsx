'use client';

interface BusinessCardProps {
  business: {
    id: string;
    name: string;
    description: string | null;
    status: string;
    current_phase: string;
    created_at: string;
    metrics?: {
      revenue?: number;
      users?: number;
    };
  };
  onView?: (id: string) => void;
  onArchive?: (id: string) => void;
  loading?: boolean;
}

export function BusinessCard({ business, onView, onArchive, loading }: BusinessCardProps) {
  if (loading) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 animate-pulse">
        <div className="h-5 bg-slate-700 rounded w-3/4 mb-4" />
        <div className="h-4 bg-slate-700 rounded w-full mb-2" />
        <div className="h-4 bg-slate-700 rounded w-1/2 mb-4" />
        <div className="h-3 bg-slate-700 rounded w-1/3" />
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    building: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    operating: 'bg-green-500/20 text-green-400 border-green-500/30',
    archived: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-blue-500/50 transition-colors group">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
          {business.name}
        </h3>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium border ${
            statusColors[business.status] || 'bg-gray-500/20 text-gray-400'
          }`}
        >
          {business.status}
        </span>
      </div>

      <p className="text-gray-400 text-sm mb-4 line-clamp-2 min-h-[2.5rem]">
        {business.description || 'No description'}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
        <span>Phase: {business.current_phase}</span>
        <span>
          {business.metrics?.revenue != null
            ? `$${business.metrics.revenue.toLocaleString()}`
            : '—'}
        </span>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-600">
          Created: {new Date(business.created_at).toLocaleDateString()}
        </span>
        <div className="flex gap-2">
          <button
            onClick={(e) => { e.stopPropagation(); onView?.(business.id); }}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30 hover:bg-blue-500/30 transition-colors"
          >
            View
          </button>
          {business.status !== 'archived' && (
            <button
              onClick={(e) => { e.stopPropagation(); onArchive?.(business.id); }}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 transition-colors"
            >
              Archive
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
