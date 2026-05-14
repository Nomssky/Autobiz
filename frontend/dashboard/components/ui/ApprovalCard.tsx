'use client';

// ApprovalCard — Menampilkan approval request dengan aksi approve/reject
interface ApprovalCardProps {
  id: string;
  title: string;
  description: string;
  business: string;
  urgency: 'low' | 'normal' | 'high' | 'critical';
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  proposedChanges: Record<string, any>;
  impact: string;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
}

const urgencyColors: Record<string, string> = {
  low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  normal: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
};

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  approved: 'bg-green-500/20 text-green-400 border-green-500/30',
  rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
  cancelled: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

export function ApprovalCard({
  id, title, description, business, urgency, status,
  proposedChanges, impact, onApprove, onReject
}: ApprovalCardProps) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-slate-600 transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-white font-semibold">{title}</h3>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${urgencyColors[urgency]}`}>
              {urgency}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[status]}`}>
              {status}
            </span>
          </div>
          <p className="text-sm text-slate-400 mb-2">{description}</p>
          <span className="text-xs text-slate-500 bg-slate-700/50 px-2 py-0.5 rounded">
            {business}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
        <div>
          <p className="text-slate-500 mb-1">Proposed Changes:</p>
          <ul className="space-y-0.5">
            {Object.entries(proposedChanges).map(([k, v]) => (
              <li key={k} className="text-slate-300">• {k}: <span className="font-medium">{String(v)}</span></li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-slate-500 mb-1">Impact:</p>
          <p className="text-slate-300">{impact}</p>
        </div>
      </div>

      {status === 'pending' && (onApprove || onReject) && (
        <div className="flex gap-2 mt-4 pt-4 border-t border-slate-700">
          <button
            onClick={() => onApprove?.(id)}
            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium text-sm transition-colors"
          >
            ✓ Approve
          </button>
          <button
            onClick={() => onReject?.(id)}
            className="flex-1 px-4 py-2 bg-red-600/80 hover:bg-red-700 text-white rounded-lg font-medium text-sm transition-colors"
          >
            ✗ Reject
          </button>
        </div>
      )}
    </div>
  );
}