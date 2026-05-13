'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { ApprovalRequest, ApprovalDecisionRequest } from '@/types';

interface UseApprovalsOptions {
  businessId?: string;
  statusFilter?: string;
  skip?: number;
  limit?: number;
}

export function useApprovals({
  businessId,
  statusFilter,
  skip = 0,
  limit = 50,
}: UseApprovalsOptions = {}) {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pendingCount, setPendingCount] = useState(0);

  const fetchApprovals = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      if (businessId) params.business_id = businessId;

      const data = await api.getApprovals(params);
      setApprovals(data);
      setPendingCount(data.filter((a: any) => a.status === 'pending').length);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch approvals');
    } finally {
      setLoading(false);
    }
  }, [businessId, statusFilter]);

  const fetchPending = useCallback(async () => {
    try {
      const data = await api.getPendingApprovals(
        businessId ? { business_id: businessId } : undefined
      );
      setApprovals(data);
      setPendingCount(data.length);
    } catch (err: any) {
      setError(err.message);
    }
  }, [businessId]);

  const approve = useCallback(async (id: string, body: ApprovalDecisionRequest) => {
    try {
      await api.decideApproval(id, body);
      setApprovals((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, status: body.decision } : a
        )
      );
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message };
    }
  }, []);

  useEffect(() => {
    fetchApprovals();
  }, [fetchApprovals]);

  return {
    approvals,
    loading,
    error,
    pendingCount,
    refetch: fetchApprovals,
    fetchPending,
    approve,
  };
}

interface UseFeedbackOptions {
  businessId: string;
  enabled?: boolean;
}

export function useFeedback({ businessId, enabled = true }: UseFeedbackOptions) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const submitFeedback = useCallback(
    async (content: string, feedbackType?: string, sentimentScore?: number) => {
      setSubmitting(true);
      setError(null);
      setSuccess(false);

      try {
        await api.submitFeedback({
          business_id: businessId,
          content,
          feedback_type: feedbackType,
          sentiment_score: sentimentScore,
        });
        setSuccess(true);
      } catch (err: any) {
        setError(err.message || 'Failed to submit feedback');
      } finally {
        setSubmitting(false);
      }
    },
    [businessId]
  );

  return { submitFeedback, submitting, error, success };
}

interface UseVectorSearchOptions {
  businessId: string;
  enabled?: boolean;
}

export function useVectorSearch({ businessId, enabled = true }: UseVectorSearchOptions) {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(
    async (query: string) => {
      if (!enabled || !businessId) return;

      setLoading(true);
      try {
        const data = await api.searchVectors({ business_id: businessId, query });
        setResults(data.results || []);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Search failed');
      } finally {
        setLoading(false);
      }
    },
    [businessId, enabled]
  );

  return { results, loading, error, search };
}

interface UseAgentEvaluationOptions {
  businessId: string;
  role?: string;
  enabled?: boolean;
}

export function useAgentEvaluation({
  businessId,
  role,
  enabled = true,
}: UseAgentEvaluationOptions) {
  const [evaluation, setEvaluation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEvaluation = useCallback(async () => {
    if (!enabled || !businessId) return;

    try {
      const data = role
        ? await api.getEvaluation(businessId, role)
        : await api.getEvaluation(businessId);
      setEvaluation(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to evaluate agent');
    } finally {
      setLoading(false);
    }
  }, [businessId, role, enabled]);

  useEffect(() => {
    fetchEvaluation();
  }, [fetchEvaluation]);

  return { evaluation, loading, error, refetch: fetchEvaluation };
}