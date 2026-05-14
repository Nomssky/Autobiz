import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Approvals | AutoBiz',
};

export default function ApprovalsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Approval Queue</h1>
          <p className="text-slate-400">Review and approve pending business decisions</p>
        </div>
        <div className="flex gap-2">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
            2 Pending
          </span>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
            12 Approved
          </span>
        </div>
      </div>

      {/* Approval Queue */}
      <div className="space-y-4">
        <ApprovalRequestCard
          id="req-1"
          title="Launch marketing campaign"
          description="Approve $2,000 budget for Q1 social media campaign on Instagram, TikTok, and Google Ads"
          business="Acme AI Solutions"
          urgency="high"
          status="pending"
          proposedChanges={{ budget: '$2,000', channel: 'social_media' }}
          impact="Expected 150% ROI within 3 months"
        />
        <ApprovalRequestCard
          id="req-2"
          title="Deploy v1.0.0 to production"
          description="Full production deployment with monitoring and rollback plan"
          business="Acme AI Solutions"
          urgency="normal"
          status="pending"
          proposedChanges={{ version: 'v1.0.0', environment: 'production' }}
          impact="Enables real customer access"
        />
      </div>

      {/* Approved History */}
      <div className="mt-10">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Decisions</h3>
        <div className="space-y-3">
          <DecisionCard
            title="Approve pricing tiers"
            decision="approved"
            decisionBy="CEO"
            date="2026-05-10"
            comments="Good pricing structure. Proceed with launch."
          />
          <DecisionCard
            title="Budget allocation for development"
            decision="rejected"
            decisionBy="CEO"
            date="2026-05-08"
            comments="Budget too high. Need to reduce scope to MVP features only."
          />
        </div>
      </div>
    </div>
  );
}

function ApprovalRequestCard({
  id, title, description, business, urgency, status, proposedChanges, impact
}: {
  id: string; title: string; description: string; business: string;
  urgency: 'low' | 'normal' | 'high' | 'critical'; status: string;
  proposedChanges: Record<string, any>; impact: string;
}) {
  const urgencyColors: Record<string, string> = {
    low: 'bg-blue-500/20 text-blue-400',
    normal: 'bg-slate-500/20 text-slate-400',
    high: 'bg-orange-500/20 text-orange-400',
    critical: 'bg-red-500/20 text-red-400',
  };

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-slate-600 transition-colors">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-white font-semibold">{title}</h3>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${urgencyColors[urgency]}`}>
              {urgency}
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-400">
              {business}
            </span>
          </div>
          <p className="text-sm text-slate-400 mb-3">{description}</p>

          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <p className="text-slate-500">Proposed Changes:</p>
              <ul className="mt-1 space-y-1">
                {Object.entries(proposedChanges).map(([key, val]) => (
                  <li key={key} className="text-slate-300">• {key}: <span className="font-medium">{String(val)}</span></li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-slate-500">Impact Analysis:</p>
              <p className="text-slate-300 mt-1">{impact}</p>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <button className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium text-sm transition-colors">
            ✓ Approve
          </button>
          <button className="px-4 py-2 bg-red-600/80 hover:bg-red-700 text-white rounded-lg font-medium text-sm transition-colors">
            ✗ Reject
          </button>
        </div>
      </div>
    </div>
  );
}

function DecisionCard({ title, decision, decisionBy, date, comments }: {
  title: string; decision: 'approved' | 'rejected'; decisionBy: string; date: string; comments: string;
}) {
  const colors = decision === 'approved'
    ? 'bg-green-500/10 border-green-500/20'
    : 'bg-red-500/10 border-red-500/20';
  const textColor = decision === 'approved' ? 'text-green-400' : 'text-red-400';

  return (
    <div className={`border rounded-lg p-4 ${colors}`}>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-white font-medium">{title}</h4>
        <span className={`text-xs font-medium ${textColor}`}>{decision.toUpperCase()}</span>
      </div>
      <p className="text-sm text-slate-400 mb-2">{comments}</p>
      <div className="flex items-center gap-3 text-xs text-slate-500">
        <span>By: {decisionBy}</span>
        <span>•</span>
        <span>{date}</span>
      </div>
    </div>
  );
}