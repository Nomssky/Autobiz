'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

const STEPS = ['Idea', 'Details', 'Confirm'] as const;
type Step = typeof STEPS[number];

export default function NewBusinessWizard() {
  const router = useRouter();
  const [step, setStep] = useState<Step>('Idea');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    idea: '',
    ceo_id: '',
  });

  const stepIndex = STEPS.indexOf(step);

  const nextStep = () => {
    if (stepIndex < STEPS.length - 1) {
      setStep(STEPS[stepIndex + 1]);
    }
  };

  const prevStep = () => {
    if (stepIndex > 0) {
      setStep(STEPS[stepIndex - 1]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Auto-generate CEO ID for demo
      const ceoId = crypto.randomUUID();
      await api.createBusiness({ ...form, ceo_id: ceoId });
      router.push('/businesses');
    } catch (err: any) {
      setError(err.message || 'Failed to create business');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-2xl font-bold text-white mb-2">Create New Business</h1>
      <p className="text-slate-400 mb-8">Launch your AI-powered autonomous business</p>

      {/* Progress Steps */}
      <div className="flex items-center mb-8">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                step === s
                  ? 'bg-blue-600 text-white'
                  : i < stepIndex
                  ? 'bg-green-500 text-white'
                  : 'bg-slate-700 text-slate-400'
              }`}
            >
              {i < stepIndex ? '✓' : s[0]}
            </div>
            <span
              className={`ml-3 text-sm font-medium ${
                step === s ? 'text-white' : 'text-slate-500'
              }`}
              style={{ display: i < STEPS.length - 1 ? 'none' : 'inline' }}
            >
              {s}
            </span>
            {i < STEPS.length - 1 && (
              <div
                className={`w-16 h-1 mx-2 rounded ${
                  i < stepIndex ? 'bg-green-500' : 'bg-slate-700'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Idea */}
        {step === 'Idea' && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white">Describe Your Business Idea</h3>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Business Idea <span className="text-red-400">*</span>
              </label>
              <textarea
                value={form.idea}
                onChange={(e) => setForm({ ...form, idea: e.target.value })}
                className="w-full p-3 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-[120px]"
                placeholder="Describe your business idea in detail. The AI agents will use this to build your business."
                required
              />
            </div>
            <button
              type="button"
              onClick={nextStep}
              disabled={!form.idea.trim()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white rounded-lg font-medium transition-colors"
            >
              Next →
            </button>
          </div>
        )}

        {/* Step 2: Details */}
        {step === 'Details' && (
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white">Business Details</h3>
            <p className="text-sm text-slate-400">
              A CEO ID will be auto-generated for you. The AI agents will use this to coordinate and build your business.
            </p>
            <button
              type="button"
              onClick={() => setForm((f) => ({ ...f, ceo_id: crypto.randomUUID() }))}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg font-medium text-sm transition-colors border border-slate-600"
            >
              🔄 Generate CEO ID
            </button>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                CEO ID {form.ceo_id ? '' : <span className="text-red-400">*</span>}
              </label>
              <input
                type="text"
                value={form.ceo_id}
                onChange={(e) => setForm({ ...form, ceo_id: e.target.value })}
                className="w-full p-3 bg-slate-900 border border-slate-600 rounded-lg text-white placeholder-slate-500 font-mono text-sm"
                placeholder="Auto-generated on submit"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={prevStep}
                className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg font-medium transition-colors"
              >
                ← Back
              </button>
              <button
                type="submit"
                disabled={loading || !form.ceo_id}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                    Launching...
                  </>
                ) : (
                  '🚀 Launch Business'
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}