'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { MetricsPieChart } from '@/components/ui/MetricsChart';

interface UsageData {
  tier: string;
  subscription_status: string;
  usage: {
    tokens_used: number;
    total_cost: number;
    total_executions: number;
    monthly_budget: number;
    budget_used_percent: number;
  };
  limits: {
    businesses_limit: number;
    ai_budget_monthly: number;
  };
  needs_upgrade: boolean;
}

const TIER_INFO: Record<string, { label: string; price: string; businesses: string; budget: string }> = {
  starter: { label: 'Starter', price: '$29/mo', businesses: '1 business', budget: '$50 AI budget' },
  growth: { label: 'Growth', price: '$99/mo', businesses: '5 businesses', budget: '$200 AI budget' },
  enterprise: { label: 'Enterprise', price: 'Custom', businesses: 'Unlimited', budget: 'Custom' },
};

function getStatusColor(percent: number): string {
  if (percent > 80) return 'bg-red-500';
  if (percent > 50) return 'bg-yellow-500';
  return 'bg-blue-500';
}

export default function BillingPage() {
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    fetchUsage();
  }, []);

  async function fetchUsage() {
    try {
      const data = await api.get('/billing/usage');
      setUsage(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load billing data');
    } finally {
      setLoading(false);
    }
  }

  async function handleUpgrade(tier: string) {
    setUpgrading(true);
    try {
      const data = await api.post(`/billing/upgrade?tier=${tier}`);
      if (data.url) {
        window.location.href = data.url;
      } else if (data.type === 'contact_sales') {
        window.open('mailto:sales@autobiz.ai', '_blank');
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUpgrading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 p-8">
        <div className="max-w-4xl mx-auto space-y-6 animate-pulse">
          <div className="h-8 bg-slate-800 rounded w-48" />
          <div className="h-4 bg-slate-800 rounded w-96" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-slate-800 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-2">Failed to load billing data</p>
          <p className="text-slate-500 text-sm mb-4">{error}</p>
          <button onClick={fetchUsage} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const currentTier = usage?.tier || 'starter';
  const budgetPct = usage?.usage?.budget_used_percent || 0;
  const tierInfo = TIER_INFO[currentTier] || TIER_INFO.starter;

  const pieData = [
    { name: 'Used', value: usage?.usage?.total_cost || 0 },
    { name: 'Remaining', value: Math.max(0, (usage?.usage?.monthly_budget || 50) - (usage?.usage?.total_cost || 0)) },
  ];

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Billing</h1>
          <p className="text-slate-400 mt-1">Manage your subscription and usage</p>
        </div>

        {/* Current Plan */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-white">Current Plan</h2>
              <p className="text-sm text-slate-400 capitalize">{currentTier}</p>
            </div>
            <span className="text-2xl font-bold text-white">{tierInfo.price}</span>
          </div>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="bg-slate-700/50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-400">Businesses</p>
              <p className="text-lg font-semibold text-white">{tierInfo.businesses}</p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-400">AI Budget</p>
              <p className="text-lg font-semibold text-white">{tierInfo.budget}</p>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-3 text-center">
              <p className="text-xs text-slate-400">Executions</p>
              <p className="text-lg font-semibold text-white">{usage?.usage?.total_executions || 0}</p>
            </div>
          </div>
        </div>

        {/* Usage Bar */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-white">AI Budget Usage</h3>
            <span className="text-sm font-medium text-slate-300">
              ${usage?.usage?.total_cost?.toFixed(2) || '0.00'} / ${usage?.usage?.monthly_budget || 50}
            </span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${getStatusColor(budgetPct)}`}
              style={{ width: `${Math.min(budgetPct, 100)}%` }}
            />
          </div>
          <div className="flex items-center justify-between mt-1">
            <span className="text-xs text-slate-500">{budgetPct}% used</span>
            {usage?.needs_upgrade && (
              <span className="text-xs text-yellow-400 font-medium">Approaching limit</span>
            )}
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-sm font-medium text-white mb-4">Budget Breakdown</h3>
            <MetricsPieChart
              data={pieData}
              dataKey="value"
              name="Budget"
              height={250}
            />
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h3 className="text-sm font-medium text-white mb-4">Usage Details</h3>
            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b border-slate-700">
                <span className="text-sm text-slate-400">Tokens Used</span>
                <span className="text-sm text-white font-medium">
                  {(usage?.usage?.tokens_used || 0).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-700">
                <span className="text-sm text-slate-400">Total Cost</span>
                <span className="text-sm text-white font-medium">
                  ${usage?.usage?.total_cost?.toFixed(4) || '0.0000'}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-700">
                <span className="text-sm text-slate-400">AI Executions</span>
                <span className="text-sm text-white font-medium">
                  {usage?.usage?.total_executions || 0}
                </span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-sm text-slate-400">Status</span>
                <span className={`text-sm font-medium capitalize ${
                  usage?.subscription_status === 'active' ? 'text-green-400' : 'text-yellow-400'
                }`}>
                  {usage?.subscription_status || 'No subscription'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Upgrade CTA */}
        {usage?.needs_upgrade && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-400">Approaching AI budget limit</p>
                <p className="text-xs text-slate-400 mt-1">
                  You&apos;ve used {budgetPct}% of your monthly AI budget. Upgrade to continue without interruption.
                </p>
              </div>
              <button
                onClick={() => handleUpgrade('growth')}
                disabled={upgrading}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 text-sm font-medium"
              >
                {upgrading ? 'Processing...' : 'Upgrade to Growth'}
              </button>
            </div>
          </div>
        )}

        {/* Plan Comparison */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Compare Plans</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(TIER_INFO).map(([key, info]) => (
              <div
                key={key}
                className={`rounded-xl p-4 border ${
                  key === currentTier
                    ? 'bg-blue-500/10 border-blue-500/30'
                    : 'bg-slate-700/50 border-slate-600'
                }`}
              >
                <h4 className="text-lg font-semibold text-white capitalize">{info.label}</h4>
                <p className="text-2xl font-bold text-white mt-2">{info.price}</p>
                <ul className="mt-4 space-y-2">
                  <li className="text-sm text-slate-400">{info.businesses}</li>
                  <li className="text-sm text-slate-400">{info.budget}</li>
                </ul>
                {key !== currentTier && key !== 'enterprise' && (
                  <button
                    onClick={() => handleUpgrade(key)}
                    disabled={upgrading}
                    className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
                  >
                    {upgrading ? 'Processing...' : `Upgrade to ${info.label}`}
                  </button>
                )}
                {key === 'enterprise' && (
                  <button
                    onClick={() => handleUpgrade(key)}
                    className="mt-4 w-full px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-500 text-sm font-medium"
                  >
                    Contact Sales
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
