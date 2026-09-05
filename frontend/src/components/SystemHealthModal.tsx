import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  Database,
  Key,
  RefreshCw,
  Server,
  Sparkles,
  X,
  XCircle,
} from "lucide-react";
import { HealthResponse, IntegrationStatusResponse } from "../types";
import { api } from "../services/api";

export interface SystemHealthModalProps {
  isOpen: boolean;
  onClose: () => void;
  isBackendConnected: boolean;
  onRefreshHealth: () => Promise<void>;
}

export const SystemHealthModal: React.FC<SystemHealthModalProps> = ({
  isOpen,
  onClose,
  isBackendConnected,
  onRefreshHealth,
}) => {
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [integrationsData, setIntegrationsData] = useState<IntegrationStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastCheckedAt, setLastCheckedAt] = useState<Date>(new Date());

  const fetchHealthDetails = async () => {
    setIsLoading(true);
    try {
      const [h, i] = await Promise.allSettled([
        api.checkHealth(),
        api.getIntegrationsStatus(),
      ]);

      if (h.status === "fulfilled") {
        setHealthData(h.value);
      }
      if (i.status === "fulfilled") {
        setIntegrationsData(i.value);
      }
      setLastCheckedAt(new Date());
    } catch {
      // Handled gracefully
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchHealthDetails();
    }
  }, [isOpen]);

  const handleManualCheck = async () => {
    await onRefreshHealth();
    await fetchHealthDetails();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-box"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 540, width: "100%", padding: "1.75rem" }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Server size={20} color="var(--accent-primary)" />
            <h2 style={{ fontSize: "1.15rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Backend Health & Integrations
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)" }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Server Status Hero */}
        <div
          style={{
            padding: "1rem 1.25rem",
            backgroundColor: isBackendConnected ? "rgba(16, 185, 129, 0.08)" : "rgba(239, 68, 68, 0.08)",
            border: "1px solid",
            borderColor: isBackendConnected ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)",
            borderRadius: "var(--radius-md)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "1.25rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            {isBackendConnected ? (
              <CheckCircle2 size={22} color="#10B981" />
            ) : (
              <XCircle size={22} color="#EF4444" />
            )}
            <div>
              <div style={{ fontWeight: 700, fontSize: "0.95rem", color: isBackendConnected ? "#065F46" : "#991B1B" }}>
                {isBackendConnected ? "FastAPI Backend Connected" : "Backend Offline"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.15rem" }}>
                {isBackendConnected
                  ? `Running ${healthData?.app || "RazorPulse"} v${healthData?.version || "0.1.0"} (${healthData?.environment || "development"})`
                  : "Unable to reach http://localhost:8000. Start the server with uvicorn."}
              </div>
            </div>
          </div>

          <button
            className="btn btn-secondary btn-sm"
            onClick={handleManualCheck}
            disabled={isLoading}
            style={{ fontSize: "0.75rem" }}
          >
            <RefreshCw size={12} className={isLoading ? "animate-spin" : ""} />
            Check Now
          </button>
        </div>

        {/* Credential Status Section */}
        <div style={{ marginBottom: "1.25rem" }}>
          <div style={{ fontSize: "0.78rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
            Credential Configuration Status
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
            Reports whether credentials are configured in the backend environment. Never exposes secret keys or tokens.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {/* Supabase */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.6rem 0.85rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Database size={15} color="var(--text-secondary)" />
                <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>Supabase (PostgreSQL Persistence)</span>
              </div>
              <span
                style={{
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  padding: "0.15rem 0.5rem",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor: integrationsData?.supabase?.configured ? "#ECFDF5" : "#F1F5F9",
                  color: integrationsData?.supabase?.configured ? "#065F46" : "#64748B",
                }}
              >
                {integrationsData?.supabase?.configured ? "Configured" : "Not Configured (SQLite Fallback)"}
              </span>
            </div>

            {/* Exa AI */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.6rem 0.85rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Sparkles size={15} color="#2563EB" />
                <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>Exa AI (External Web Discovery)</span>
              </div>
              <span
                style={{
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  padding: "0.15rem 0.5rem",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor: integrationsData?.exa?.configured ? "#ECFDF5" : "#F1F5F9",
                  color: integrationsData?.exa?.configured ? "#065F46" : "#64748B",
                }}
              >
                {integrationsData?.exa?.configured ? "Configured" : "Not Configured"}
              </span>
            </div>

            {/* Google Gemini */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.6rem 0.85rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Sparkles size={15} color="#8B5CF6" />
                <div>
                  <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>Google Gemini (Evidence Verifier)</span>
                  {integrationsData?.gemini?.model && (
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginLeft: "0.4rem" }}>
                      ({integrationsData.gemini.model})
                    </span>
                  )}
                </div>
              </div>
              <span
                style={{
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  padding: "0.15rem 0.5rem",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor: integrationsData?.gemini?.configured ? "#ECFDF5" : "#F1F5F9",
                  color: integrationsData?.gemini?.configured ? "#065F46" : "#64748B",
                }}
              >
                {integrationsData?.gemini?.configured ? "Configured" : "Not Configured"}
              </span>
            </div>

            {/* Razorpay */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.6rem 0.85rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <Key size={15} color="var(--text-secondary)" />
                <span style={{ fontSize: "0.82rem", fontWeight: 600 }}>Razorpay API (Test Mode Ingestion)</span>
              </div>
              <span
                style={{
                  fontSize: "0.72rem",
                  fontWeight: 600,
                  padding: "0.15rem 0.5rem",
                  borderRadius: "var(--radius-pill)",
                  backgroundColor: integrationsData?.razorpay?.configured ? "#ECFDF5" : "#F1F5F9",
                  color: integrationsData?.razorpay?.configured ? "#065F46" : "#64748B",
                }}
              >
                {integrationsData?.razorpay?.configured ? "Configured" : "Not Configured"}
              </span>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.72rem", color: "var(--text-muted)", borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem" }}>
          <span>Last checked: {lastCheckedAt.toLocaleTimeString()}</span>
          <button className="btn btn-primary btn-sm" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
