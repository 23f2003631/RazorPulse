/**
 * RazorPulse Centralized API Client.
 * 
 * Interacts with FastAPI backend routes.
 * Robust error handling, typed responses, and clean abstraction.
 */

import {
  DemoScenarioListResponse,
  InvestigationDetailResponse,
  InvestigationListResponse,
  RiskEvent,
  RiskEventCreate,
  RiskEventListResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...options.headers,
  };

  try {
    const res = await fetch(url, { ...options, headers });

    if (!res.ok) {
      let errorMessage = `HTTP Error ${res.status}`;
      let errorData: any = null;
      try {
        errorData = await res.json();
        if (errorData?.detail) {
          errorMessage = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
        } else if (errorData?.message) {
          errorMessage = errorData.message;
        }
      } catch {
        // Fallback to text status
      }
      throw new ApiError(errorMessage, res.status, errorData);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network or parse error
    throw new ApiError(
      err?.message?.includes("Failed to fetch")
        ? "Unable to connect to the RazorPulse backend server. Please verify it is running."
        : err?.message || "An unexpected network error occurred",
      0
    );
  }
}

export const api = {
  // Health
  checkHealth: async () => {
    return request<{ status: string; app: string; version: string; environment: string }>("/health");
  },

  // Risk Events
  getRiskEvents: async (limit = 50, offset = 0, status?: string) => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (status) params.set("status", status);
    return request<RiskEventListResponse>(`/api/v1/risk-events?${params.toString()}`);
  },

  getRiskEvent: async (id: string) => {
    return request<RiskEvent>(`/api/v1/risk-events/${id}`);
  },

  createRiskEvent: async (payload: RiskEventCreate) => {
    return request<RiskEvent>("/api/v1/risk-events", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Investigations
  triggerInvestigation: async (riskEventId: string) => {
    return request<InvestigationDetailResponse>("/api/v1/investigations", {
      method: "POST",
      body: JSON.stringify({ risk_event_id: riskEventId }),
    });
  },

  getInvestigation: async (investigationId: string) => {
    return request<InvestigationDetailResponse>(`/api/v1/investigations/${investigationId}`);
  },

  listInvestigations: async (limit = 50, offset = 0, status?: string, riskEventId?: string) => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (status) params.set("status", status);
    if (riskEventId) params.set("risk_event_id", riskEventId);
    return request<InvestigationListResponse>(`/api/v1/investigations?${params.toString()}`);
  },

  // Deterministic Demo Scenarios (Single source of truth from backend)
  getDemoScenarios: async () => {
    return request<DemoScenarioListResponse>("/api/v1/investigations/demo-scenarios");
  },
};
