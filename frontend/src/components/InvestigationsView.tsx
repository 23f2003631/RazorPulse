import React, { useState } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  Clock,
  FileCheck2,
  FileSearch,
  FileText,
  Search,
} from "lucide-react";
import { InvestigationResponse } from "../types";
import { BandBadge, EmptyState, StatusBadge } from "./Common";

export interface InvestigationsViewProps {
  investigations: InvestigationResponse[];
  investigationsDetailsMap?: Record<string, any>; // investigationId -> full details (for contradictions / merchants)
  merchantNamesMap?: Record<string, string>; // riskEventId -> merchant name
  merchantDomainsMap?: Record<string, string>; // riskEventId -> domain
  onViewDossier: (investigationId: string) => void;
  onBackToDashboard: () => void;
  contradictionsMap?: Record<string, boolean>; // investigationId -> hasContradiction
}

export const InvestigationsView: React.FC<InvestigationsViewProps> = ({
  investigations,
  merchantNamesMap = {},
  merchantDomainsMap = {},
  onViewDossier,
  onBackToDashboard,
  contradictionsMap = {},
}) => {
  const [filter, setFilter] = useState<"all" | "completed" | "in_flight" | "contradictions">("all");
  const [searchQuery, setSearchQuery] = useState("");

  const completedInvs = investigations.filter((i) => i.status === "completed");
  const inFlightInvs = investigations.filter((i) =>
    ["pending", "searching", "verifying", "scoring"].includes(i.status)
  );
  const contradictionInvs = investigations.filter(
    (i) => contradictionsMap[i.id] || (i.eci_score !== null && i.eci_score !== undefined && i.eci_score <= 10 && i.eci_band === "low")
  );

  const strongOrAboveCount = completedInvs.filter(
    (i) => i.eci_band === "strong" || i.eci_band === "very_strong"
  ).length;
  const strongOrAboveRate = completedInvs.length > 0
    ? `${((strongOrAboveCount / completedInvs.length) * 100).toFixed(0)}%`
    : "—";

  // Filter investigations
  const filtered = investigations.filter((inv) => {
    // Tab filter
    if (filter === "completed" && inv.status !== "completed") return false;
    if (filter === "in_flight" && !["pending", "searching", "verifying", "scoring"].includes(inv.status)) return false;
    if (filter === "contradictions" && !contradictionsMap[inv.id]) return false;

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const merchant = (merchantNamesMap[inv.risk_event_id] || "").toLowerCase();
      const domain = (merchantDomainsMap[inv.risk_event_id] || "").toLowerCase();
      const id = inv.id.toLowerCase();
      return merchant.includes(q) || domain.includes(q) || id.includes(q);
    }
    return true;
  });

  return (
    <div className="page-container">
      {/* Header bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "1.5rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <FileSearch size={22} color="var(--accent-primary)" />
            <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--text-primary)" }}>
              External Corroboration Investigations
            </h1>
          </div>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            Synthesized evidence dossiers, deterministic ECI v1.1 evaluations, and external citation records.
          </p>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={onBackToDashboard}>
          Return to Dashboard
        </button>
      </div>

      {/* Summary Stat Cards */}
      <div className="metrics-row" style={{ marginBottom: "1.5rem" }}>
        <div className="metric-card" style={{ cursor: "pointer" }} onClick={() => setFilter("all")}>
          <div className="metric-header">
            <span className="metric-title">Total Investigations</span>
            <div className="metric-icon-circle" style={{ backgroundColor: "#EFF6FF", color: "#2563EB" }}>
              <FileText size={16} />
            </div>
          </div>
          <div className="metric-body">
            <span className="metric-value">{investigations.length}</span>
          </div>
          <div className="metric-subtitle">Across all anomaly events</div>
        </div>

        <div className="metric-card" style={{ cursor: "pointer" }} onClick={() => setFilter("completed")}>
          <div className="metric-header">
            <span className="metric-title">Completed Dossiers</span>
            <div className="metric-icon-circle" style={{ backgroundColor: "#ECFDF5", color: "#059669" }}>
              <FileCheck2 size={16} />
            </div>
          </div>
          <div className="metric-body">
            <span className="metric-value">{completedInvs.length}</span>
          </div>
          <div className="metric-subtitle">Ready for human analyst review</div>
        </div>

        <div className="metric-card" style={{ cursor: "pointer" }} onClick={() => setFilter("contradictions")}>
          <div className="metric-header">
            <span className="metric-title">Contradictions Flagged</span>
            <div className="metric-icon-circle" style={{ backgroundColor: "#FEF2F2", color: "#DC2626" }}>
              <AlertTriangle size={16} />
            </div>
          </div>
          <div className="metric-body">
            <span className="metric-value">{contradictionInvs.length}</span>
          </div>
          <div className="metric-subtitle">Public refutations or dispute signals</div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">Strong-or-Above Rate</span>
            <div className="metric-icon-circle" style={{ backgroundColor: "#EFF6FF", color: "#1D4ED8" }}>
              <ArrowUpRight size={16} />
            </div>
          </div>
          <div className="metric-body">
            <span className="metric-value">{strongOrAboveRate}</span>
          </div>
          <div className="metric-subtitle">Completed cases with ECI Strong or Very Strong</div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="card" style={{ padding: "1.25rem 1.5rem" }}>
        {/* Filter bar & live search */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1rem" }}>
          {/* Tabs */}
          <div style={{ display: "flex", gap: "0.25rem", backgroundColor: "var(--bg-app)", padding: "0.2rem", borderRadius: "var(--radius-pill)" }}>
            <button
              onClick={() => setFilter("all")}
              style={{
                padding: "0.3rem 0.75rem",
                borderRadius: "var(--radius-pill)",
                fontSize: "0.75rem",
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                backgroundColor: filter === "all" ? "#FFFFFF" : "transparent",
                color: filter === "all" ? "var(--accent-primary)" : "var(--text-muted)",
                boxShadow: filter === "all" ? "var(--shadow-sm)" : "none",
              }}
            >
              All ({investigations.length})
            </button>
            <button
              onClick={() => setFilter("completed")}
              style={{
                padding: "0.3rem 0.75rem",
                borderRadius: "var(--radius-pill)",
                fontSize: "0.75rem",
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                backgroundColor: filter === "completed" ? "#FFFFFF" : "transparent",
                color: filter === "completed" ? "var(--accent-primary)" : "var(--text-muted)",
                boxShadow: filter === "completed" ? "var(--shadow-sm)" : "none",
              }}
            >
              Completed ({completedInvs.length})
            </button>
            <button
              onClick={() => setFilter("in_flight")}
              style={{
                padding: "0.3rem 0.75rem",
                borderRadius: "var(--radius-pill)",
                fontSize: "0.75rem",
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                backgroundColor: filter === "in_flight" ? "#FFFFFF" : "transparent",
                color: filter === "in_flight" ? "#2563EB" : "var(--text-muted)",
                boxShadow: filter === "in_flight" ? "var(--shadow-sm)" : "none",
              }}
            >
              In-Flight ({inFlightInvs.length})
            </button>
            <button
              onClick={() => setFilter("contradictions")}
              style={{
                padding: "0.3rem 0.75rem",
                borderRadius: "var(--radius-pill)",
                fontSize: "0.75rem",
                fontWeight: 600,
                border: "none",
                cursor: "pointer",
                backgroundColor: filter === "contradictions" ? "#FFFFFF" : "transparent",
                color: filter === "contradictions" ? "#DC2626" : "var(--text-muted)",
                boxShadow: filter === "contradictions" ? "var(--shadow-sm)" : "none",
              }}
            >
              Contradictions ({contradictionInvs.length})
            </button>
          </div>

          {/* Search box */}
          <div style={{ position: "relative", width: 260 }}>
            <Search size={14} style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Filter by merchant or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: "100%",
                padding: "0.4rem 0.75rem 0.4rem 2.25rem",
                fontSize: "0.78rem",
                borderRadius: "var(--radius-pill)",
                border: "1px solid var(--border-subtle)",
                backgroundColor: "var(--bg-app)",
                outline: "none",
              }}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                style={{
                  position: "absolute",
                  right: "0.6rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "transparent",
                  border: "none",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  color: "var(--text-muted)",
                }}
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Table / Empty State */}
        {filtered.length === 0 ? (
          <EmptyState
            title="No investigations match your filter"
            description="Adjust your search criteria or filter tab to view other recorded investigations."
            action={
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  setFilter("all");
                  setSearchQuery("");
                }}
              >
                Reset Filters
              </button>
            }
          />
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Investigation ID</th>
                  <th>Merchant Subject</th>
                  <th>Status</th>
                  <th>ECI Corroboration</th>
                  <th>Evidence Items</th>
                  <th>Created At</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((inv) => {
                  const merchantName = merchantNamesMap[inv.risk_event_id] || "Investigated Merchant";
                  const domain = merchantDomainsMap[inv.risk_event_id] || "direct-gateway.in";
                  const hasContra = contradictionsMap[inv.id];

                  return (
                    <tr key={inv.id}>
                      {/* ID */}
                      <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", color: "var(--accent-primary)", fontWeight: 600 }}>
                        #INV-{inv.id.slice(0, 8).toUpperCase()}
                      </td>

                      {/* Merchant */}
                      <td>
                        <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                          {merchantName}
                        </div>
                        <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                          {domain}
                        </div>
                      </td>

                      {/* Status */}
                      <td>
                        <StatusBadge status={inv.status} />
                      </td>

                      {/* ECI */}
                      <td>
                        {inv.status === "completed" && inv.eci_score !== null && inv.eci_score !== undefined ? (
                          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                            <span
                              style={{
                                fontFamily: "var(--font-mono)",
                                fontWeight: 700,
                                fontSize: "0.9rem",
                                color:
                                  inv.eci_band === "very_strong"
                                    ? "#059669"
                                    : inv.eci_band === "strong"
                                    ? "#2563EB"
                                    : inv.eci_band === "moderate"
                                    ? "#D97706"
                                    : "#64748B",
                              }}
                            >
                              ECI {inv.eci_score}/100
                            </span>
                            <BandBadge band={inv.eci_band} />
                            {hasContra && (
                              <span
                                style={{
                                  fontSize: "0.68rem",
                                  padding: "0.15rem 0.4rem",
                                  backgroundColor: "var(--contradiction-bg)",
                                  color: "var(--contradiction-text)",
                                  border: "1px solid var(--contradiction-border)",
                                  borderRadius: "var(--radius-pill)",
                                  fontWeight: 600,
                                }}
                              >
                                Discrepancy Flagged
                              </span>
                            )}
                          </div>
                        ) : (
                          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            Pipeline in progress
                          </span>
                        )}
                      </td>

                      {/* Evidence Count */}
                      <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                        {inv.evidence_count} source{inv.evidence_count === 1 ? "" : "s"}
                      </td>

                      {/* Timestamp */}
                      <td style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                        {new Date(inv.created_at).toLocaleString("en-IN", {
                          dateStyle: "short",
                          timeStyle: "short",
                        })}
                      </td>

                      {/* Actions */}
                      <td style={{ textAlign: "right" }}>
                        {inv.status === "completed" ? (
                          <button
                            className="btn btn-secondary btn-sm"
                            style={{ borderRadius: "var(--radius-pill)", fontSize: "0.75rem", padding: "0.3rem 0.75rem" }}
                            onClick={() => onViewDossier(inv.id)}
                          >
                            <FileText size={12} />
                            View Dossier
                          </button>
                        ) : (
                          <button
                            className="btn btn-secondary btn-sm"
                            style={{ borderRadius: "var(--radius-pill)", fontSize: "0.75rem", padding: "0.3rem 0.75rem" }}
                            disabled
                          >
                            <Clock size={12} />
                            In Progress
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
