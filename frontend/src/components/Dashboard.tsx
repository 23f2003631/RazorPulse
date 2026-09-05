import React from "react";
import { FileText, Plus, RefreshCw, Search, ShieldAlert, Zap } from "lucide-react";
import { RiskEvent } from "../types";
import { EmptyState, StatusBadge } from "./Common";

export interface DashboardProps {
  events: RiskEvent[];
  investigationsMap: Record<string, string>; // risk_event_id -> investigation_id
  onInvestigate: (event: RiskEvent) => void;
  onViewDossier: (investigationId: string) => void;
  onOpenSimulateModal: () => void;
  onRefresh: () => void;
  isLoading: boolean;
  activeInvestigatingId?: string | null;
}

export const Dashboard: React.FC<DashboardProps> = ({
  events,
  investigationsMap,
  onInvestigate,
  onViewDossier,
  onOpenSimulateModal,
  onRefresh,
  isLoading,
  activeInvestigatingId,
}) => {
  const pendingCount = events.filter((e) => e.status === "pending").length;
  const completedCount = events.filter((e) => e.status === "completed").length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Header bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontSize: "1.375rem", fontWeight: 700, color: "var(--text-primary)" }}>
            Anomalies Requiring External Corroboration
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            Payment velocity anomalies detected by payment-risk systems awaiting external context discovery.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <button className="btn btn-secondary" onClick={onRefresh} disabled={isLoading} title="Refresh Anomaly Queue">
            <RefreshCw size={14} className={isLoading ? "animate-spin" : ""} />
            Refresh
          </button>
          <button className="btn btn-primary" onClick={onOpenSimulateModal}>
            <Plus size={14} />
            Simulate Risk Anomaly
          </button>
        </div>
      </div>

      {/* Metric Cards Bar */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1rem",
        }}
      >
        <div className="panel" style={{ padding: "1rem 1.25rem" }}>
          <div className="kv-label">Total Ingested Anomalies</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)", marginTop: "0.25rem" }}>
            {events.length}
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Tracked in Supabase <code>risk_events</code>
          </div>
        </div>

        <div className="panel" style={{ padding: "1rem 1.25rem" }}>
          <div className="kv-label">Pending External Review</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#F59E0B", marginTop: "0.25rem" }}>
            {pendingCount}
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Awaiting external web corroboration
          </div>
        </div>

        <div className="panel" style={{ padding: "1rem 1.25rem" }}>
          <div className="kv-label">Investigations Completed</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#10B981", marginTop: "0.25rem" }}>
            {completedCount}
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Dossier & ECI synthesized
          </div>
        </div>

        <div className="panel" style={{ padding: "1rem 1.25rem" }}>
          <div className="kv-label">Decision Support Model</div>
          <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--accent-primary)", marginTop: "0.5rem" }}>
            Human-in-the-Loop
          </div>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
            Zero automated fund freezing or approvals
          </div>
        </div>
      </div>

      {/* Anomaly Table Panel */}
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">
            <ShieldAlert size={16} color="var(--accent-primary)" />
            <span>Risk Anomaly Queue ({events.length})</span>
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Sorted by most recent detection
          </span>
        </div>

        {events.length === 0 ? (
          <div style={{ padding: "2rem" }}>
            <EmptyState
              title="No Risk Anomalies in Queue"
              description="The database currently contains no simulated risk anomaly events. Click below to ingest standard test fixtures."
              action={
                <button className="btn btn-primary" onClick={onOpenSimulateModal}>
                  <Plus size={14} />
                  Simulate Risk Anomaly
                </button>
              }
            />
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Merchant</th>
                  <th>Anomaly Type</th>
                  <th>Velocity Spike</th>
                  <th>Txn Volume</th>
                  <th>Occurred</th>
                  <th>Status</th>
                  <th style={{ textAlign: "right" }}>Analyst Action</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => {
                  const hasInvestigation = investigationsMap[ev.id];
                  const isCurrentlyInvestigating = activeInvestigatingId === ev.id;
                  const pct = ev.percentage_change ?? (
                    ev.observed_transaction_count && ev.baseline_transaction_count
                      ? ((ev.observed_transaction_count - ev.baseline_transaction_count) / ev.baseline_transaction_count) * 100
                      : 0
                  );

                  return (
                    <tr key={ev.id}>
                      <td>
                        <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                          {ev.merchant_name}
                        </div>
                        {ev.merchant_domain && (
                          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                            {ev.merchant_domain}
                          </div>
                        )}
                      </td>
                      <td>
                        <span
                          style={{
                            fontSize: "0.75rem",
                            fontFamily: "var(--font-mono)",
                            color: "var(--text-secondary)",
                          }}
                        >
                          {ev.anomaly_type}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.25rem", color: "#F87171", fontWeight: 600 }}>
                          <Zap size={13} />
                          <span>+{pct.toFixed(0)}%</span>
                        </div>
                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                          {ev.observed_transaction_count} vs {ev.baseline_transaction_count} baseline
                        </div>
                      </td>
                      <td>
                        <div style={{ fontWeight: 500 }}>
                          {ev.currency} {ev.transaction_amount?.toLocaleString() || "N/A"}
                        </div>
                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                          {ev.geographic_info || "India"}
                        </div>
                      </td>
                      <td>
                        <div style={{ fontSize: "0.78rem" }}>
                          {new Date(ev.occurred_at).toLocaleDateString("en-IN", {
                            month: "short",
                            day: "numeric",
                          })}
                        </div>
                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                          {new Date(ev.occurred_at).toLocaleTimeString("en-IN", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                      </td>
                      <td>
                        <StatusBadge status={ev.status} />
                      </td>
                      <td style={{ textAlign: "right" }}>
                        {hasInvestigation ? (
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => onViewDossier(hasInvestigation)}
                          >
                            <FileText size={13} />
                            View Dossier
                          </button>
                        ) : (
                          <button
                            className="btn btn-primary btn-sm"
                            disabled={isCurrentlyInvestigating}
                            onClick={() => onInvestigate(ev)}
                          >
                            <Search size={13} />
                            {isCurrentlyInvestigating ? "Investigating..." : "Investigate"}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
