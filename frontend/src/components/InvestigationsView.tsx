import React, { useState } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  FileCheck2,
  FileSearch,
  FileText,
  Search,
} from "lucide-react";
import { InvestigationResponse } from "../types";
import { BandBadge, EmptyState, StatusBadge } from "./Common";

export interface InvestigationsViewProps {
  investigations: InvestigationResponse[];
  investigationsDetailsMap?: Record<string, any>;
  merchantNamesMap?: Record<string, string>;
  merchantDomainsMap?: Record<string, string>;
  onViewDossier: (investigationId: string) => void;
  onBackToDashboard: () => void;
  contradictionsMap?: Record<string, boolean>;
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
    (i) => Boolean(contradictionsMap[i.id])
  );

  const strongOrAboveCount = completedInvs.filter(
    (i) => i.eci_band === "strong" || i.eci_band === "very_strong"
  ).length;
  const strongOrAboveRate = completedInvs.length > 0
    ? `${((strongOrAboveCount / completedInvs.length) * 100).toFixed(0)}%`
    : "—";

  // Filter investigations
  const filtered = investigations.filter((inv) => {
    if (filter === "completed" && inv.status !== "completed") return false;
    if (filter === "in_flight" && !["pending", "searching", "verifying", "scoring"].includes(inv.status)) return false;
    if (filter === "contradictions" && !contradictionsMap[inv.id]) return false;

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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.75rem", marginBottom: "0.25rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
            <FileSearch size={20} color="var(--brand-primary)" />
            <h1 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>
              External Corroboration Investigations
            </h1>
          </div>
          <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: "0.15rem" }}>
            Synthesized evidence dossiers, deterministic ECI v1.1 evaluations, and external citation records.
          </p>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={onBackToDashboard}>
          Return to Dashboard
        </button>
      </div>

      {/* Summary Stat Cards */}
      <div className="metrics-row">
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
          <div className="metric-subtitle">
            {completedInvs.length > 0
              ? "Completed cases with ECI Strong or Very Strong"
              : "Awaiting completed investigations"}
          </div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="card" style={{ padding: "1.25rem" }}>
        {/* Filter bar & live search */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem", marginBottom: "0.85rem" }}>
          {/* Segmented filter */}
          <div className="segmented-control">
            <button
              className={`segmented-item ${filter === "all" ? "active" : ""}`}
              onClick={() => setFilter("all")}
            >
              All ({investigations.length})
            </button>
            <button
              className={`segmented-item ${filter === "completed" ? "active" : ""}`}
              onClick={() => setFilter("completed")}
            >
              Completed ({completedInvs.length})
            </button>
            <button
              className={`segmented-item ${filter === "in_flight" ? "active" : ""}`}
              onClick={() => setFilter("in_flight")}
            >
              In-Flight ({inFlightInvs.length})
            </button>
            <button
              className={`segmented-item ${filter === "contradictions" ? "active" : ""}`}
              onClick={() => setFilter("contradictions")}
            >
              Contradictions ({contradictionInvs.length})
            </button>
          </div>

          {/* Search bar */}
          <div style={{ position: "relative", width: 280 }}>
            <Search size={14} style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Search merchant, domain, ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: "100%",
                height: 32,
                padding: "0 0.75rem 0 2.25rem",
                fontSize: "0.78rem",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border-subtle)",
                backgroundColor: "var(--bg-input)",
                outline: "none",
              }}
            />
          </div>
        </div>

        {/* Table */}
        {filtered.length === 0 ? (
          <EmptyState
            title="No investigations match your criteria"
            description="Adjust your search query or tab filter to view other investigations in the queue."
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
                  <th>Discovered Evidence</th>
                  <th>Synthesized At</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((inv) => {
                  const merchant = merchantNamesMap[inv.risk_event_id] || "Unknown Merchant";
                  const domain = merchantDomainsMap[inv.risk_event_id] || "direct-gateway.in";
                  const hasContra = contradictionsMap[inv.id];

                  return (
                    <tr key={inv.id}>
                      <td style={{ fontFamily: "var(--font-mono)", fontWeight: 600, fontSize: "0.75rem", color: "var(--brand-primary)", fontVariantNumeric: "tabular-nums" }}>
                        #INV-{inv.id.slice(0, 8).toUpperCase()}
                      </td>
                      <td>
                        <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>{merchant}</div>
                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{domain}</div>
                      </td>
                      <td>
                        <StatusBadge status={inv.status} />
                      </td>
                      <td>
                        {inv.status === "completed" && inv.eci_score !== null && inv.eci_score !== undefined ? (
                          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                            <span
                              style={{
                                fontSize: "0.82rem",
                                fontWeight: 700,
                                fontFamily: "var(--font-mono)",
                                fontVariantNumeric: "tabular-nums",
                                color:
                                  inv.eci_band === "very_strong"
                                    ? "var(--band-very-strong)"
                                    : inv.eci_band === "strong"
                                    ? "var(--band-strong)"
                                    : inv.eci_band === "moderate"
                                    ? "var(--band-moderate)"
                                    : "var(--band-low)",
                              }}
                            >
                              ECI {inv.eci_score}
                            </span>
                            <BandBadge band={inv.eci_band} />
                            {hasContra && (
                              <span
                                style={{
                                  fontSize: "0.65rem",
                                  padding: "0.1rem 0.35rem",
                                  backgroundColor: "var(--contradiction-bg)",
                                  color: "var(--contradiction-text)",
                                  border: "1px solid var(--contradiction-border)",
                                  borderRadius: "var(--radius-pill)",
                                  fontWeight: 600,
                                }}
                              >
                                Discrepancy
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="badge badge-neutral" style={{ fontSize: "0.7rem" }}>
                            Awaiting Pipeline
                          </span>
                        )}
                      </td>
                      <td>
                        <span style={{ fontSize: "0.78rem", fontWeight: 600, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
                          {inv.evidence_count || 0} items
                        </span>
                      </td>
                      <td>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>
                          {inv.completed_at ? new Date(inv.completed_at).toLocaleDateString("en-IN") : "In Progress"}
                        </span>
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => onViewDossier(inv.id)}
                          title="View complete evidence dossier"
                        >
                          <FileText size={12} />
                          <span>View Dossier</span>
                        </button>
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
