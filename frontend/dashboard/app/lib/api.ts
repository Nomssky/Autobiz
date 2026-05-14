import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { BusinessResponse, ApprovalRequestResponse, MetricSnapshotResponse, RealtimeMetricsResponse } from '@/types';

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') + '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // Auth
  // Generic HTTP methods
  async get<T = any>(url: string, params?: Record<string, any>) {
    const { data } = await this.client.get<T>(url, { params });
    return data;
  }

  async post<T = any>(url: string, body?: any) {
    const { data } = await this.client.post<T>(url, body);
    return data;
  }

  // Auth
  async login(credentials: { username: string; password: string }) {
    const { data } = await this.client.post('/auth/login', credentials);
    return data;
  }

  // Billing
  async getBillingUsage() {
    return this.get('/billing/usage');
  }

  async upgradeBilling(tier: string) {
    return this.post(`/billing/upgrade?tier=${tier}`);
  }

  // Businesses
  async getBusinesses(params?: { status?: string; skip?: number; limit?: number }) {
    const { data } = await this.client.get<BusinessResponse[]>('/businesses', { params });
    return data;
  }

  async getBusiness(id: string) {
    const { data } = await this.client.get<BusinessResponse>(`/businesses/${id}`);
    return data;
  }

  async createBusiness(body: { idea: string; ceo_id: string }) {
    const { data } = await this.client.post<BusinessResponse>('/businesses/create', body);
    return data;
  }

  async updateBusiness(id: string, body: Record<string, any>) {
    const { data } = await this.client.patch<BusinessResponse>(`/businesses/${id}`, body);
    return data;
  }

  async archiveBusiness(id: string) {
    await this.client.delete(`/businesses/${id}`);
  }

  async launchBusiness(id: string) {
    const { data } = await this.client.post<BusinessResponse>(`/businesses/${id}/launch`);
    return data;
  }

  async getBusinessTimeline(id: string) {
    const { data } = await this.client.get(`/businesses/${id}/timeline`);
    return data;
  }

  // Approvals
  async getApprovals(params?: { status?: string; business_id?: string }) {
    const { data } = await this.client.get<ApprovalRequestResponse[]>('/approvals', { params });
    return data;
  }

  async getPendingApprovals(params?: { business_id?: string }) {
    const { data } = await this.client.get<ApprovalRequestResponse[]>('/approvals/pending', { params });
    return data;
  }

  async getApproval(id: string) {
    const { data } = await this.client.get<ApprovalRequestResponse>(`/approvals/${id}`);
    return data;
  }

  async createApproval(body: {
    business_id: string;
    title: string;
    description?: string;
    proposed_changes: Record<string, any>;
    impact_analysis?: Record<string, any>;
    urgency: string;
  }) {
    const { data } = await this.client.post<ApprovalRequestResponse>('/approvals', {
      ...body,
      proposed_changes: body.proposed_changes || {},
    });
    return data;
  }

  async decideApproval(id: string, body: { decision: 'approve' | 'reject'; ceo_id: string; comments?: string }) {
    const { data } = await this.client.post(`/approvals/${id}/decide`, body);
    return data;
  }

  async updateApproval(id: string, body: Record<string, any>) {
    const { data } = await this.client.patch<ApprovalRequestResponse>(`/approvals/${id}`, body);
    return data;
  }

  async cancelApproval(id: string) {
    await this.client.delete(`/approvals/${id}`);
  }

  // Metrics
  async getMetrics(params?: { business_id?: string; skip?: number; limit?: number }) {
    const { data } = await this.client.get<MetricSnapshotResponse[]>('/metrics', { params });
    return data;
  }

  async getMetric(id: string) {
    const { data } = await this.client.get<MetricSnapshotResponse>(`/metrics/${id}`);
    return data;
  }

  async getRealtimeMetrics(businessId: string) {
    const { data } = await this.client.get<RealtimeMetricsResponse>(`/metrics/${businessId}/realtime`);
    return data;
  }

  async getMetricSummary(businessId: string, days?: number) {
    const { data } = await this.client.get(`/metrics/${businessId}/summary`, { params: { days } });
    return data;
  }

  async createMetric(body: {
    business_id: string;
    recorded_by_role: string;
    daily_revenue?: number;
    weekly_revenue?: number;
    monthly_revenue?: number;
    users_count?: number;
    active_users_count?: number;
    churn_rate?: number;
    bug_count?: number;
    support_tickets_count?: number;
    open_support_tickets?: number;
    conversion_rate?: number;
    customer_acquisition_cost?: number;
    lifetime_value?: number;
    custom_metrics?: Record<string, any>;
  }) {
    const { data } = await this.client.post<MetricSnapshotResponse>('/metrics', body);
    return data;
  }

  async deleteMetric(id: string) {
    await this.client.delete(`/metrics/${id}`);
  }

  // Vectors
  async searchVectors(body: { business_id: string; query: string; top_k?: number }) {
    const { data } = await this.client.post('/vectors/search', body);
    return data;
  }

  async getKnowledge(businessId: string) {
    const { data } = await this.client.get(`/vectors/${businessId}/knowledge`);
    return data;
  }

  // Learning
  async submitFeedback(body: {
    business_id: string;
    user_id?: string;
    feedback_type?: string;
    content: string;
    sentiment_score?: number;
  }) {
    const { data } = await this.client.post('/learning/feedback', body);
    return data;
  }

  async getEvaluation(businessId: string, role?: string, days?: number) {
    const { data } = await this.client.get(`/learning/evaluation/${businessId}`, { params: { role, days } });
    return data;
  }

  async optimizePrompt(businessId: string, roleName: string, prompt: string) {
    const { data } = await this.client.post(`/learning/optimize-prompt`, {
      business_id: businessId,
      role_name: roleName,
      original_prompt: prompt,
    });
    return data;
  }
}

export const api = new ApiClient();