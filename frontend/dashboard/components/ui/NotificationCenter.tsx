'use client';

import { useEffect, useState, useCallback } from 'react';
import { Bell, CheckCircle2, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';
import { createWebSocketConnection } from '@/lib/websocket';
import { api } from '@/lib/api';
import { ApprovalRequest } from '@/types';

interface Notification {
  id: string;
  type: 'approval' | 'alert' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action?: string;
  data?: any;
}

interface NotificationCenterProps {
  maxNotifications?: number;
}

export function NotificationCenter({ maxNotifications = 5 }: NotificationCenterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // Fetch notifications from API
  const fetchNotifications = useCallback(async () => {
    try {
      setIsLoading(true);
      const pending = await api.getPendingApprovals();
      const approvalNotifs: Notification[] = pending.map((a: any) => ({
        id: a.id,
        type: 'approval' as const,
        title: a.title || 'New Approval Required',
        message: a.description || 'A decision is required on this item',
        timestamp: a.created_at ? new Date(a.created_at).toLocaleString() : 'Just now',
        read: false,
        action: `/approvals`,
        data: a,
      }));

      const recent = await api.getApprovals({ statusFilter: 'approved', skip: 0, limit: 3 });
      const successNotifs: Notification[] = recent.map((a: any) => ({
        id: `approved-${a.id}`,
        type: 'success' as const,
        title: `${a.title} — Approved`,
        message: `Approved by decision maker`,
        timestamp: a.decided_at ? new Date(a.decided_at).toLocaleString() : 'Recently',
        read: true,
        action: `/approvals`,
      }));

      const rejected = await api.getApprovals({ statusFilter: 'rejected', skip: 0, limit: 3 });
      const rejectNotifs: Notification[] = rejected.map((a: any) => ({
        id: `rejected-${a.id}`,
        type: 'alert' as const,
        title: `${a.title} — Rejected`,
        message: a.ceo_decision || 'Request was rejected',
        timestamp: a.decided_at ? new Date(a.decided_at).toLocaleString() : 'Recently',
        read: true,
        action: `/approvals`,
      }));

      const allNotifications = [...approvalNotifs, ...successNotifs, ...rejectNotifs];
      setNotifications(allNotifications);
      setUnreadCount(approvalNotifs.length);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // WebSocket for real-time approval notifications
  useEffect(() => {
    const ws = createWebSocketConnection({
      url: `${typeof window !== 'undefined'
        ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/approvals`
        : 'ws://localhost:8000/api/v1/ws/approvals'}`,
      reconnect: true,
      maxReconnectAttempts: 5,
      reconnectInterval: 3000,
      autoConnect: true,
    });

    ws.onConnected(() => {
      setWsConnected(true);
      console.log('[NotificationCenter] WebSocket connected');
    });

    ws.onDisconnected(() => {
      setWsConnected(false);
    });

    ws.on('approval_update', (data: any) => {
      const approval = data.payload || data;
      if (!approval) return;

      const notifType = approval.status === 'approved' ? 'success' :
                        approval.status === 'rejected' ? 'alert' : 'approval';

      const newNotif: Notification = {
        id: `ws-${approval.id}-${Date.now()}`,
        type: notifType as any,
        title: approval.title || `${approval.status === 'approved' ? 'Approved' : 'Rejected'}: ${approval.task_type || 'Task'}`,
        message: approval.description || `Status changed to ${approval.status}`,
        timestamp: new Date().toLocaleString(),
        read: false,
        action: '/approvals',
        data: approval,
      };

      setNotifications((prev) => {
        // Deduplicate by approval ID
        const filtered = prev.filter((n) => n.data?.id !== approval.id);
        return [newNotif, ...filtered];
      });

      if (notifType === 'approval') {
        setUnreadCount((c) => c + 1);
      }
    });

    ws.on('metrics_update', () => {
      // Refresh notifications when metrics update
      fetchNotifications();
    });

    ws.on('error', (err: any) => {
      console.error('[NotificationCenter] WebSocket error:', err);
    });

    return () => {
      ws.disconnect();
    };
  }, [fetchNotifications]);

  // Initial fetch
  useEffect(() => {
    fetchNotifications();

    // Refresh interval as fallback
    const interval = setInterval(fetchNotifications, 60000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const typeIcons: Record<Notification['type'], JSX.Element> = {
    approval: <AlertTriangle size={16} className="text-orange-400" />,
    alert: <XCircle size={16} className="text-red-400" />,
    info: <Bell size={16} className="text-blue-400" />,
    success: <CheckCircle2 size={16} className="text-green-400" />,
  };

  const typeBg: Record<Notification['type'], string> = {
    approval: 'bg-orange-500/10',
    alert: 'bg-red-500/10',
    info: 'bg-blue-500/10',
    success: 'bg-green-500/10',
  };

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
    setUnreadCount((c) => Math.max(0, c - 1));
  };

  return (
    <div className="relative">
      <button
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) {
            setUnreadCount(0);
            setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
          }
        }}
        className="relative p-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors"
        title="Notifications"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 w-5 h-5 bg-red-500 rounded-full ring-2 ring-slate-900 text-xs text-white flex items-center justify-center font-bold">
            {unreadCount}
          </span>
        )}
        {wsConnected && (
          <span className="absolute bottom-0 right-0 w-1.5 h-1.5 bg-green-500 rounded-full ring-2 ring-slate-900" />
        )}
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-30"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-96 bg-slate-900 border border-slate-700 rounded-xl shadow-xl z-40 overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
              <h4 className="text-sm font-semibold text-white">Notifications</h4>
              <div className="flex items-center gap-2">
                {isLoading && <RefreshCw size={14} className="text-slate-500 animate-spin" />}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    fetchNotifications();
                  }}
                  className="text-slate-400 hover:text-white text-xs"
                  title="Refresh"
                >
                  <RefreshCw size={14} />
                </button>
              </div>
            </div>

            {/* Status indicator */}
            <div className="px-4 py-1.5 bg-slate-800/50 text-xs text-slate-500 flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}
              />
              <span>{wsConnected ? 'Live updates' : 'Reconnecting...'}</span>
            </div>

            {/* Notification list */}
            <div className="max-h-96 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-6 text-center text-slate-500 text-sm">
                  <Bell size={24} className="mx-auto mb-2 opacity-50" />
                  No notifications
                </div>
              ) : (
                notifications.slice(0, maxNotifications).map((notification) => (
                  <div
                    key={notification.id}
                    onClick={() => markAsRead(notification.id)}
                    className={`p-3 border-b border-slate-700 last:border-0 cursor-pointer hover:bg-slate-800/50 transition-colors ${
                      !notification.read ? typeBg[notification.type] : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {typeIcons[notification.type]}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">
                          {notification.title}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5 truncate">
                          {notification.message}
                        </p>
                        <p className="text-xs text-slate-600 mt-1">
                          {notification.timestamp}
                        </p>
                      </div>
                      {!notification.read && (
                        <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1" />
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-slate-700 text-center">
              <button
                onClick={() => {
                  setNotifications([]);
                  setUnreadCount(0);
                }}
                className="text-xs text-slate-500 hover:text-white transition-colors"
              >
                Clear all
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}