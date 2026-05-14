'use client';

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { api } from './api';

interface BusinessState {
  businesses: any[];
  loading: boolean;
  error: string | null;
  setBusinesses: (businesses: any[]) => void;
  addBusiness: (business: any) => void;
  updateBusiness: (id: string, updates: Partial<any>) => void;
  removeBusiness: (id: string) => void;
  fetchBusinesses: () => Promise<void>;
}

interface ApprovalState {
  approvals: any[];
  loading: boolean;
  fetchApprovals: () => Promise<void>;
  fetchPendingApprovals: () => Promise<void>;
}

interface MetricState {
  metrics: any[];
  metricsLoading: boolean;
  fetchMetrics: () => Promise<void>;
}

interface UIState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useStore = create<
  BusinessState & ApprovalState & MetricState & UIState
>()(
  devtools((set, get) => ({
    // Business State
    businesses: [],
    loading: false,
    error: null,
    setBusinesses: (businesses) => set({ businesses }),
    addBusiness: (business) =>
      set((state) => ({ businesses: [business, ...state.businesses] })),
    updateBusiness: (id, updates) =>
      set((state) => ({
        businesses: state.businesses.map((b: any) =>
          b.id === id ? { ...b, ...updates } : b
        ),
      })),
    removeBusiness: (id) =>
      set((state) => ({
        businesses: state.businesses.filter((b: any) => b.id !== id),
      })),
    fetchBusinesses: async () => {
      set({ loading: true, error: null });
      try {
        const data = await api.getBusinesses();
        set({ businesses: data, loading: false });
      } catch (error: any) {
        set({ error: error.message, loading: false });
      }
    },

    // Approval State
    approvals: [],
    fetchApprovals: async () => {
      set({ loading: true });
      try {
        const data = await api.getApprovals();
        set({ approvals: data, loading: false });
      } catch {
        set({ loading: false });
      }
    },
    fetchPendingApprovals: async () => {
      set({ loading: true });
      try {
        const data = await api.getPendingApprovals();
        set({ approvals: data, loading: false });
      } catch {
        set({ loading: false });
      }
    },

    // Metric State
    metrics: [],
    metricsLoading: false,
    fetchMetrics: async () => {
      set({ metricsLoading: true });
      try {
        const data = await api.getMetrics();
        set({ metrics: data, metricsLoading: false });
      } catch {
        set({ metricsLoading: false });
      }
    },

    // UI State
    sidebarOpen: true,
    toggleSidebar: () =>
      set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  }))
);