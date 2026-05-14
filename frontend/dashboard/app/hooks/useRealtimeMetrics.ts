'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { RealtimeMetricsResponse, MetricSnapshot } from '@/types';

interface UseRealtimeMetricsOptions {
  businessId: string;
  refreshInterval?: number;
  enabled?: boolean;
}

export function useRealtimeMetrics({
  businessId,
  refreshInterval = 30000, // 30 seconds
  enabled = true,
}: UseRealtimeMetricsOptions) {
  const [metrics, setMetrics] = useState<RealtimeMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout>();

  const fetchMetrics = useCallback(async () => {
    if (!enabled || !businessId) return;

    try {
      const data = await api.getRealtimeMetrics(businessId);
      setMetrics(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  }, [businessId, enabled]);

  useEffect(() => {
    fetchMetrics();

    if (enabled) {
      intervalRef.current = setInterval(fetchMetrics, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchMetrics, refreshInterval, enabled]);

  return { metrics, loading, error, refetch: fetchMetrics };
}

interface UseMetricHistoryOptions {
  businessId: string;
  days?: number;
  enabled?: boolean;
}

export function useMetricHistory({
  businessId,
  days = 7,
  enabled = true,
}: UseMetricHistoryOptions) {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(async () => {
    if (!enabled || !businessId) return;

    try {
      const data = await api.getMetricSummary(businessId, days);
      if (data.message) {
        setHistory([]);
      } else {
        // Transform summary into chart-ready format
        setHistory([
          { name: 'M', value: data.avg_daily_revenue || 0, label: 'Avg Daily Revenue' },
          { name: 'Users', value: data.avg_users || 0, label: 'Avg Users' },
          { name: 'Active', value: data.avg_active_users || 0, label: 'Avg Active Users' },
          { name: 'Bugs', value: data.avg_bugs || 0, label: 'Avg Bugs' },
          { name: 'Churn %', value: (data.avg_churn_rate || 0) * 100, label: 'Avg Churn Rate' },
        ]);
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch metric history');
    } finally {
      setLoading(false);
    }
  }, [businessId, days, enabled]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return { history, loading, error, refetch: fetchHistory };
}

interface UseSnapshotsOptions {
  businessId: string;
  skip?: number;
  limit?: number;
  enabled?: boolean;
}

export function useSnapshots({
  businessId,
  skip = 0,
  limit = 50,
  enabled = true,
}: UseSnapshotsOptions) {
  const [snapshots, setSnapshots] = useState<MetricSnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSnapshots = useCallback(async () => {
    if (!enabled || !businessId) return;

    try {
      const data = await api.getMetrics({ business_id: businessId, skip, limit });
      setSnapshots(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch snapshots');
    } finally {
      setLoading(false);
    }
  }, [businessId, skip, limit, enabled]);

  useEffect(() => {
    fetchSnapshots();
  }, [fetchSnapshots]);

  const addSnapshot = useCallback((snapshot: MetricSnapshot) => {
    setSnapshots((prev) => [snapshot, ...prev].slice(0, limit));
  }, [limit]);

  const removeSnapshot = useCallback((id: string) => {
    setSnapshots((prev) => prev.filter((s) => s.id !== id));
  }, []);

  return {
    snapshots,
    loading,
    error,
    refetch: fetchSnapshots,
    addSnapshot,
    removeSnapshot,
  };
}