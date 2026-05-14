'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { RealtimeMetricsResponse } from '@/types';
import { api } from '@/lib/api';

interface UseRealtimeUpdatesOptions {
  businessId: string;
  onMetricsUpdate?: (metrics: RealtimeMetricsResponse) => void;
  onApprovalUpdate?: (approval: any) => void;
}

export function useRealtimeUpdates({
  businessId,
  onMetricsUpdate,
  onApprovalUpdate,
}: UseRealtimeUpdatesOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const retryCountRef = useRef(0);
  const maxRetries = 5;

  const connect = useCallback(() => {
    // Fallback: SSE (Server-Sent Events) for real-time metrics
    // WebSocket is preferred but SSE is more compatible
    try {
      // Try WebSocket first
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/v1/ws/metrics/${businessId}`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        retryCountRef.current = 0;
        console.log('[Realtime] WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'metrics_update') {
            onMetricsUpdate?.(data.payload as RealtimeMetricsResponse);
          } else if (data.type === 'approval_update') {
            onApprovalUpdate?.(data.payload);
          }
        } catch (e) {
          console.error('[Realtime] Parse error:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[Realtime] WebSocket error:', error);
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('[Realtime] WebSocket disconnected');

        // Auto-reconnect with exponential backoff
        if (retryCountRef.current < maxRetries) {
          const delay = Math.pow(2, retryCountRef.current) * 1000;
          retryCountRef.current += 1;

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`[Realtime] Reconnecting... (attempt ${retryCountRef.current})`);
            connect();
          }, delay);
        }
      };
    } catch (e) {
      console.warn('[Realtime] WebSocket not supported, using fallback polling');
      startFallbackPolling();
    }
  }, [businessId, onMetricsUpdate, onApprovalUpdate]);

  const fallbackIntervalRef = useRef<NodeJS.Timeout>();

  const startFallbackPolling = useCallback(() => {
    if (fallbackIntervalRef.current) {
      clearInterval(fallbackIntervalRef.current);
    }

    // Fetch metrics every 30 seconds as fallback
    fallbackIntervalRef.current = setInterval(async () => {
      try {
        const data = await api.getRealtimeMetrics(businessId);
        onMetricsUpdate?.(data);
        setIsConnected(true);
      } catch {
        setIsConnected(false);
      }
    }, 30000);
  }, [businessId, onMetricsUpdate]);

  const disconnect = useCallback(() => {
    // Clean up WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Clean up fallback polling
    if (fallbackIntervalRef.current) {
      clearInterval(fallbackIntervalRef.current);
      fallbackIntervalRef.current = undefined;
    }

    // Clean up reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    setIsConnected(false);
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    reconnect: connect,
    disconnect,
    send: (message: any) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(message));
        return true;
      }
      return false;
    },
  };
}