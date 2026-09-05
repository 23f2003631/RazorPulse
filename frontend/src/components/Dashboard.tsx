import React, { useState } from "react";
import {
  AlertTriangle,
  BarChart2,
  FileSearch,
  FileText,
  Flame,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { InvestigationResponse, RiskEvent } from "../types";
import { BandBadge, EmptyState, StatusBadge } from "./Common";

export interface DashboardProps {
  events: RiskEvent[];
  investigationsMap: Record<string, string>; // risk_event_id -> investigation_id
  investigationsList: InvestigationResponse[]; // loaded investigations
  contradictionsMap: Record<string, boolean>; // investigation_id -> hasContradiction
  onInvestigate: (event: RiskEvent) => void;
  onViewDossier: (investigationId: string) => void;
  onOpenSimulateModal: () => void;
  onRefresh: () => void;
  isLoading: boolean;
  activeInvestigatingId?: string | null;
  searchFilterQuery?: string;
  activeQueueFilter?: "all" | "needs_investigation" | "investigated" | "contradictions";
  onQueueFilterChange?: (filter: "all" | "needs_investigation" | "investigated" | "contradictions") => void;
  onNavigateToDemoMode?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  events,
  investigationsMap,
  investigationsList,
  contradictionsMap,
  onInvestigate,
  onViewDossier,
  onOpenSimulateModal,
  onRefresh,
  isLoading,
  activeInvestigatingId,
  searchFilterQuery = "",
  activeQueueFilter = "all",
  onQueueFilterChange,
  onNavigateToDemoMode,
}) => {
  const [internalTableFilter, setInternalTableFilter] = useState<
    "all" | "needs_investigation" | "investigated" | "contradictions"
  >("all");
  const [tableSearchVal, setTableSearchVal] = useState("");

  const effectiveFilter = onQueueFilterChange ? activeQueueFilter : internalTableFilter;
  const setEffectiveFilter = (f: "all" | "needs_investigation" | "investigated" | "contradictions") => {
    if (onQueueFilterChange) {
      onQueueFilterChange(f);
    } else {
      setInternalTableFilter(f);
    }
  };

  // Map of investigation by ID
  const invById = new Map<string, InvestigationResponse>();
  investigationsList.forEach((inv) => invById.set(inv.id, inv));

  // --- Grounded Aggregate Calculations ---
  // Needs investigation: event with no investigation record
  const needsInvestigationEvents = events.filter((e) => !investigationsMap[e.id]);
  const completedInvs = investigationsList.filter((i) => i.status === "completed");
  const inFlightInvs = investigationsList.filter((i) =>
    ["searching", "verifying", "scoring", "pending"].includes(i.status)
  );

  // Contradictions count: completed investigations with verified contradictions
  const contradictionInvs = investigationsList.filter(
    (i) => contradictionsMap[i.id] || (i.eci_score !== null && i.eci_score !== undefined && i.eci_score <= 10 && i.eci_band === "low")
  );

  // Strong-or-Above Corroboration Rate:
  // Derived strictly from backend eci_band in ["strong", "very_strong"]
  const strongOrAboveCount = completedInvs.filter(
    (i) => i.eci_band === "strong" || i.eci_band === "very_strong"
  ).length;
  const strongOrAboveRate = completedInvs.length > 0
    ? `${((strongOrAboveCount / completedInvs.length) * 100).toFixed(0)}%`
    : "—";

  // ECI Band distribution across all completed investigations
  const bandCounts = {
    very_strong: completedInvs.filter((i) => i.eci_band === "very_strong").length,
    strong: completedInvs.filter((i) => i.eci_band === "strong").length,
    moderate: completedInvs.filter((i) => i.eci_band === "moderate").length,
    low: completedInvs.filter((i) => i.eci_band === "low").length,
  };

  // Total evidence items discovered across completed investigations
  const totalEvidenceCount = completedInvs.reduce((acc, curr) => acc + (curr.evidence_count || 0), 0);

  // Velocity comparison eligible events (events with valid observed and baseline counts)
  const velocityEvents = events.filter(
    (e) =>
      e.observed_transaction_count &&
      e.baseline_transaction_count &&
      e.baseline_transaction_count > 0
  );

  // Filter events for the table
  const filteredEvents = events.filter((ev) => {
    const invId = investigationsMap[ev.id];
    const hasContra = invId ? contradictionsMap[invId] : false;

    // Queue tab filter
    if (effectiveFilter === "needs_investigation" && invId) return false;
    if (effectiveFilter === "investigated" && !invId) return false;
    if (effectiveFilter === "contradictions" && !hasContra) return false;

    // Combined search (from top header search or local table search)
    const activeSearch = (searchFilterQuery || tableSearchVal).trim().toLowerCase();
    if (activeSearch) {
      const merchant = ev.merchant_name.toLowerCase();
      const domain = (ev.merchant_domain || "").toLowerCase();
      const anomalyType = ev.anomaly_type.toLowerCase();
      const riskReason = (ev.risk_reason || "").toLowerCase();
      const id = ev.id.toLowerCase();
      return (
        merchant.includes(activeSearch) ||
        domain.includes(activeSearch) ||
        anomalyType.includes(activeSearch) ||
        riskReason.includes(activeSearch) ||
        id.includes(activeSearch)
      );
    }

    return true;
  });

  return (
    <div className="page-container">
      {/* ROW 1: TOP 4 GROUNDED METRIC CARDS */}
      <section className="metrics-row">
        {/* Metric 1: Needs Investigation */}
        <div
          className="metric-card"
          onClick={() => setEffectiveFilter("needs_investigation")}
          style={{ cursor: "pointer" }}
          title="Filter to payment anomalies awaiting external discovery"
        >
          <div className="metric-header">
            <span className="metric-title">Needs Investigation</span>
            <div className="metric-icon-circle" style={{ backgroundColor: "#FEE2E2", color: "#EF4444" }}>
              <Flame size={18} />
            </div>
          </div>
          <div className="metric-body">
            <span className="metric-value">{needsInvestigationEvents.length}</span>
            <span className="metric-tag" style={{ backgroundColor: "#FEE2E2", color: "#991B1B" }}>
              Awaiting Review
            </span>
          </div>
          <div className="metric-subtitle">
            {events.length} total anomalies in ingestion queue
          </div>
        </div>

        {/* Metric 2: Completed Investigations */}
        <div
          className="metric-card"
          onClick={() => setEffectiveFilter("investigated")}
          style={{ cursor: "pointer" }}
          title="Filter to completed investigations with synthesized dossiers"
        >
          <div className="metric-header">
            <span className="metric-title">Completed Investigations</span>
            <div className="metric-icon-circle" style={{ backgroundColor: "#EFF6FF", color: "#2563EB" }}>
              <FileSearch size={18} />
            </div>
          </div>
          <div className="metric-body">
            <span className="metric-value">{completedInvs.length}</span>
            {inFlightInvs.length > 0 && (
              <span className="metric-tag" style={{ backgroundColor: "#EFF6FF", color: "#1D4ED8" }}>
                {inFlightInvs.length} In-Flight
              </span>
            )}
          </div>
          <div className="metric-subtitle">
            Synthesized dossiers ready for analyst sign-off
          </div>
        </div>

        {/* Metric 3: Contradictions Flagged */}
        <div
          className="metric-card"
          onClick={() => setEffectiveFilter("contradictions")}
          style={{ cursor: "pointer" }}
          title="Filter to investigations where external refutations or disputes were flagged"
        >
          <div className="metric-header">
            <span className="metric-title">Contradictions Flagged</span>
            <div className="metric-icon-circle" style={{ backgroundColor: "#FEF2F2", color: "#DC2626" }}>
              <AlertTriangle size={18} />
            </div>
          </div>
          <div className="metric-body">
            <span className="metric-value">{contradictionInvs.length}</span>
            {contradictionInvs.length > 0 && (
              <span className="metric-tag" style={{ backgroundColor: "#FEF2F2", color: "#991B1B" }}>
                Severe Penalty
              </span>
            )}
          </div>
          <div className="metric-subtitle">
            Public refutations or customer dispute waves
          </div>
        </div>

        {/* Metric 4: Strong-or-Above Corroboration Rate */}
        <div
          className="metric-card"
          onClick={() => setEffectiveFilter("investigated")}
          style={{ cursor: "pointer" }}
          title="Percentage of completed investigations scoring Strong or Very Strong ECI"
        >
          <div className="metric-header">
            <span className="metric-title">Strong-or-Above Rate</span>
            <div className="metric-icon-circle" style={{ backgroundColor: "#ECFDF5", color: "#059669" }}>
              <ShieldCheck size={18} />
            </div>
          </div>
          <div className="metric-body">
            <span className="metric-value">{strongOrAboveRate}</span>
            {completedInvs.length > 0 && (
              <span className="metric-tag" style={{ backgroundColor: "#ECFDF5", color: "#065F46" }}>
                {strongOrAboveCount}/{completedInvs.length} cases
              </span>
            )}
          </div>
          <div className="metric-subtitle">
            Completed investigations with ECI Strong or Very Strong
          </div>
        </div>
      </section>

      {/* ROW 2: DISCRETE VELOCITY PROFILE & ECI BANDS (2fr 1fr) */}
      <section className="analytics-row">
        {/* Left: Truthful Observed vs Baseline Velocity Profile */}
        <div className="card correlation-card">
          <div className="card-header-bar">
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <BarChart2 size={18} color="var(--accent-primary)" />
                <h2 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  Observed vs Baseline Velocity Profile
                </h2>
              </div>
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                Discrete comparison of observed transaction volume vs historical baseline per merchant.
              </p>
            </div>

            <span
              style={{
                fontSize: "0.72rem",
                padding: "0.2rem 0.6rem",
                backgroundColor: "var(--bg-app)",
                borderRadius: "var(--radius-pill)",
                color: "var(--text-secondary)",
                fontWeight: 600,
                border: "1px solid var(--border-subtle)",
              }}
            >
              {velocityEvents.length} Profiled Incident{velocityEvents.length === 1 ? "" : "s"}
            </span>
          </div>

          {/* Velocity Profile Bars */}
          {velocityEvents.length === 0 ? (
            <div style={{ padding: "2.5rem 1rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              No anomaly events with observed vs baseline counts currently loaded. Use "Simulate Anomaly" to ingest events.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "0.5rem" }}>
              {velocityEvents.slice(0, 4).map((ev) => {
                const observed = ev.observed_transaction_count || 1;
                const baseline = ev.baseline_transaction_count || 1;
                const multiplier = (observed / baseline).toFixed(1);
                const pct = ev.percentage_change ?? ((observed - baseline) / baseline) * 100;
                const maxVal = Math.max(observed, baseline);
                const observedWidth = Math.min(100, Math.max(12, (observed / maxVal) * 100));
                const baselineWidth = Math.min(100, Math.max(6, (baseline / maxVal) * 100));

                return (
                  <div key={ev.id} style={{ padding: "0.75rem 0.85rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-md)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
                      <div>
                        <span style={{ fontWeight: 700, color: "var(--text-primary)", fontSize: "0.85rem" }}>
                          {ev.merchant_name}
                        </span>
                        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginLeft: "0.5rem" }}>
                          {ev.currency} {ev.transaction_amount?.toLocaleString() || "N/A"}
                        </span>
                      </div>
                      <span
                        style={{
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          color: "#B91C1C",
                          backgroundColor: "#FEF2F2",
                          padding: "0.15rem 0.45rem",
                          borderRadius: "var(--radius-pill)",
                        }}
                      >
                        +{pct.toFixed(0)}% ({multiplier}x surge)
                      </span>
                    </div>

                    {/* Comparative Track */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                      {/* Observed */}
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", width: "52px" }}>Observed:</span>
                        <div style={{ flex: 1, height: 7, backgroundColor: "#E2E8F0", borderRadius: 4, overflow: "hidden" }}>
                          <div style={{ width: `${observedWidth}%`, height: "100%", backgroundColor: "#2563EB", borderRadius: 4 }} />
                        </div>
                        <span style={{ fontSize: "0.72rem", fontWeight: 700, color: "var(--text-primary)", width: "60px", textAlign: "right" }}>
                          {observed.toLocaleString()}
                        </span>
                      </div>

                      {/* Baseline */}
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                        <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", width: "52px" }}>Baseline:</span>
                        <div style={{ flex: 1, height: 7, backgroundColor: "#E2E8F0", borderRadius: 4, overflow: "hidden" }}>
                          <div style={{ width: `${baselineWidth}%`, height: "100%", backgroundColor: "#94A3B8", borderRadius: 4 }} />
                        </div>
                        <span style={{ fontSize: "0.72rem", fontWeight: 500, color: "var(--text-muted)", width: "60px", textAlign: "right" }}>
                          {baseline.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Stack: ECI Bands + Decision-Support Pipeline Summary */}
        <div className="right-analytics-stack">
          {/* ECI Corroboration Bands */}
          <div className="card" style={{ padding: "1.25rem" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.75rem" }}>
              <h3 style={{ fontSize: "0.92rem", fontWeight: 700, color: "var(--text-primary)" }}>
                ECI Corroboration Bands
              </h3>
              <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                {completedInvs.length} Evaluated
              </span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
              {/* Very Strong */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: "0.2rem" }}>
                  <span style={{ fontWeight: 600, color: "#065F46" }}>Very Strong (80–100)</span>
                  <span style={{ fontWeight: 700 }}>{bandCounts.very_strong}</span>
                </div>
                <div style={{ height: 6, backgroundColor: "#E2E8F0", borderRadius: 3, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${completedInvs.length > 0 ? (bandCounts.very_strong / completedInvs.length) * 100 : 0}%`,
                      height: "100%",
                      backgroundColor: "#10B981",
                      borderRadius: 3,
                    }}
                  />
                </div>
              </div>

              {/* Strong */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: "0.2rem" }}>
                  <span style={{ fontWeight: 600, color: "#1D4ED8" }}>Strong (60–79)</span>
                  <span style={{ fontWeight: 700 }}>{bandCounts.strong}</span>
                </div>
                <div style={{ height: 6, backgroundColor: "#E2E8F0", borderRadius: 3, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${completedInvs.length > 0 ? (bandCounts.strong / completedInvs.length) * 100 : 0}%`,
                      height: "100%",
                      backgroundColor: "#2563EB",
                      borderRadius: 3,
                    }}
                  />
                </div>
              </div>

              {/* Moderate */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: "0.2rem" }}>
                  <span style={{ fontWeight: 600, color: "#92400E" }}>Moderate (30–59)</span>
                  <span style={{ fontWeight: 700 }}>{bandCounts.moderate}</span>
                </div>
                <div style={{ height: 6, backgroundColor: "#E2E8F0", borderRadius: 3, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${completedInvs.length > 0 ? (bandCounts.moderate / completedInvs.length) * 100 : 0}%`,
                      height: "100%",
                      backgroundColor: "#F59E0B",
                      borderRadius: 3,
                    }}
                  />
                </div>
              </div>

              {/* Low */}
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: "0.2rem" }}>
                  <span style={{ fontWeight: 600, color: "#475569" }}>Low (0–29)</span>
                  <span style={{ fontWeight: 700 }}>{bandCounts.low}</span>
                </div>
                <div style={{ height: 6, backgroundColor: "#E2E8F0", borderRadius: 3, overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${completedInvs.length > 0 ? (bandCounts.low / completedInvs.length) * 100 : 0}%`,
                      height: "100%",
                      backgroundColor: "#64748B",
                      borderRadius: 3,
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Separate Contradiction Indicator */}
            <div
              style={{
                marginTop: "0.85rem",
                paddingTop: "0.75rem",
                borderTop: "1px solid var(--border-subtle)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", fontSize: "0.75rem", color: "var(--contradiction-text)", fontWeight: 600 }}>
                <AlertTriangle size={13} color="#EF4444" />
                <span>Contradictions Detected:</span>
              </div>
              <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#DC2626" }}>
                {contradictionInvs.length}
              </span>
            </div>
          </div>

          {/* Decision-Support Evidence Discovery Summary */}
          <div className="card" style={{ padding: "1.25rem" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>
                External Evidence Footprint
              </span>
              <span className="sidebar-badge sidebar-badge-blue">EXA + GEMINI</span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginTop: "0.75rem" }}>
              <div style={{ padding: "0.6rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Total Evidence Items</div>
                <div style={{ fontSize: "1.2rem", fontWeight: 800, color: "var(--text-primary)", marginTop: "0.15rem" }}>
                  {totalEvidenceCount}
                </div>
              </div>
              <div style={{ padding: "0.6rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Active Queue Items</div>
                <div style={{ fontSize: "1.2rem", fontWeight: 800, color: "var(--accent-primary)", marginTop: "0.15rem" }}>
                  {events.length}
                </div>
              </div>
            </div>

            <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.75rem", lineHeight: 1.45 }}>
              Evidence corroboration strength is evaluated per investigation; RazorPulse maintains strict non-fraud decision-support boundaries.
            </p>
          </div>
        </div>
      </section>

      {/* ROW 3: ACTIVE RISK ANOMALIES TABLE */}
      <section style={{ width: "100%" }}>
        <div className="card" style={{ padding: "1.25rem 1.5rem" }}>
          {/* Table Header Bar & Filter Tabs */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1rem" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <ShieldAlert size={18} color="var(--accent-primary)" />
                <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  Payment Risk Anomalies Queue
                </h3>
              </div>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                Transaction velocity spikes awaiting or equipped with external evidence verification.
              </p>
            </div>

            {/* Actions & Filters */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              {/* Filter Tabs */}
              <div style={{ display: "flex", gap: "0.25rem", backgroundColor: "var(--bg-app)", padding: "0.2rem", borderRadius: "var(--radius-pill)" }}>
                <button
                  onClick={() => setEffectiveFilter("all")}
                  style={{
                    padding: "0.25rem 0.65rem",
                    borderRadius: "var(--radius-pill)",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    border: "none",
                    cursor: "pointer",
                    backgroundColor: effectiveFilter === "all" ? "#FFFFFF" : "transparent",
                    color: effectiveFilter === "all" ? "var(--accent-primary)" : "var(--text-muted)",
                    boxShadow: effectiveFilter === "all" ? "var(--shadow-sm)" : "none",
                  }}
                >
                  All ({events.length})
                </button>
                <button
                  onClick={() => setEffectiveFilter("needs_investigation")}
                  style={{
                    padding: "0.25rem 0.65rem",
                    borderRadius: "var(--radius-pill)",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    border: "none",
                    cursor: "pointer",
                    backgroundColor: effectiveFilter === "needs_investigation" ? "#FFFFFF" : "transparent",
                    color: effectiveFilter === "needs_investigation" ? "#D97706" : "var(--text-muted)",
                    boxShadow: effectiveFilter === "needs_investigation" ? "var(--shadow-sm)" : "none",
                  }}
                >
                  Needs Investigation ({needsInvestigationEvents.length})
                </button>
                <button
                  onClick={() => setEffectiveFilter("investigated")}
                  style={{
                    padding: "0.25rem 0.65rem",
                    borderRadius: "var(--radius-pill)",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    border: "none",
                    cursor: "pointer",
                    backgroundColor: effectiveFilter === "investigated" ? "#FFFFFF" : "transparent",
                    color: effectiveFilter === "investigated" ? "var(--accent-primary)" : "var(--text-muted)",
                    boxShadow: effectiveFilter === "investigated" ? "var(--shadow-sm)" : "none",
                  }}
                >
                  Investigated ({investigationsList.length})
                </button>
                <button
                  onClick={() => setEffectiveFilter("contradictions")}
                  style={{
                    padding: "0.25rem 0.65rem",
                    borderRadius: "var(--radius-pill)",
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    border: "none",
                    cursor: "pointer",
                    backgroundColor: effectiveFilter === "contradictions" ? "#FFFFFF" : "transparent",
                    color: effectiveFilter === "contradictions" ? "#DC2626" : "var(--text-muted)",
                    boxShadow: effectiveFilter === "contradictions" ? "var(--shadow-sm)" : "none",
                  }}
                >
                  Contradictions ({contradictionInvs.length})
                </button>
              </div>

              {/* Refresh Button */}
              <button
                className="btn btn-secondary btn-sm"
                onClick={onRefresh}
                disabled={isLoading}
                title="Refresh Queue from backend"
              >
                <RefreshCw size={13} className={isLoading ? "animate-spin" : ""} />
              </button>

              {/* Simulate Anomaly Button */}
              <button
                className="btn btn-primary btn-sm"
                onClick={onOpenSimulateModal}
                style={{ borderRadius: "var(--radius-pill)", padding: "0.35rem 0.75rem", fontSize: "0.75rem" }}
                title="Ingest test anomaly event"
              >
                <Plus size={13} />
                Simulate Anomaly
              </button>
            </div>
          </div>

          {/* Table Container */}
          {filteredEvents.length === 0 ? (
            <EmptyState
              title={events.length === 0 ? "No risk anomalies in current queue" : "No risk anomalies match your criteria"}
              description={
                events.length === 0
                  ? "Ingest a simulated anomaly using the button above, or explore the deterministic evaluation scenarios."
                  : "Adjust your search query or tab filter to view other anomaly events in the queue."
              }
              action={
                events.length === 0 && onNavigateToDemoMode ? (
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <button className="btn btn-primary btn-sm" onClick={onOpenSimulateModal}>
                      <Plus size={13} />
                      Simulate Anomaly
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={onNavigateToDemoMode}>
                      View Demo Scenarios
                    </button>
                  </div>
                ) : (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      setEffectiveFilter("all");
                      setTableSearchVal("");
                    }}
                  >
                    Reset Filters
                  </button>
                )
              }
            />
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Incident ID</th>
                    <th>Merchant Subject</th>
                    <th>Spike Volume & Velocity</th>
                    <th>Status</th>
                    <th>ECI Corroboration</th>
                    <th style={{ textAlign: "right" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvents.map((ev) => {
                    const invId = investigationsMap[ev.id];
                    const inv = invId ? invById.get(invId) : null;
                    const isInvestigating = activeInvestigatingId === ev.id;
                    const pct = ev.percentage_change ?? (
                      ev.observed_transaction_count && ev.baseline_transaction_count
                        ? ((ev.observed_transaction_count - ev.baseline_transaction_count) / ev.baseline_transaction_count) * 100
                        : 0
                    );
                    const hasContra = invId ? contradictionsMap[invId] : false;

                    // Exact status determination
                    let displayStatus = "pending";
                    if (isInvestigating) {
                      displayStatus = "searching";
                    } else if (inv) {
                      displayStatus = inv.status;
                    }

                    return (
                      <tr key={ev.id}>
                        {/* Incident ID */}
                        <td style={{ fontFamily: "var(--font-mono)", fontWeight: 600, fontSize: "0.8rem", color: "var(--accent-primary)" }}>
                          #EVT-{ev.id.slice(0, 8).toUpperCase()}
                        </td>

                        {/* Merchant */}
                        <td>
                          <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                            {ev.merchant_name}
                          </div>
                          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                            {ev.merchant_domain || "direct-gateway.in"}
                          </div>
                        </td>

                        {/* Spike Vol & Velocity */}
                        <td>
                          <div style={{ fontWeight: 700, color: "var(--text-primary)" }}>
                            {ev.currency} {ev.transaction_amount?.toLocaleString() || "N/A"}
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: "0.25rem", fontSize: "0.72rem", color: "#EF4444", fontWeight: 600 }}>
                            <Zap size={11} />
                            <span>+{pct.toFixed(0)}%</span>
                            {ev.observed_transaction_count && ev.baseline_transaction_count && (
                              <span style={{ color: "var(--text-muted)", fontWeight: 400, marginLeft: 2 }}>
                                ({ev.observed_transaction_count} vs {ev.baseline_transaction_count} txns)
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Status */}
                        <td>
                          <StatusBadge status={displayStatus} />
                        </td>

                        {/* ECI Corroboration */}
                        <td>
                          {inv && inv.status === "completed" && inv.eci_score !== null && inv.eci_score !== undefined ? (
                            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                              <span
                                style={{
                                  fontSize: "0.85rem",
                                  fontWeight: 700,
                                  fontFamily: "var(--font-mono)",
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
                                ECI {inv.eci_score}
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
                                  Discrepancy
                                </span>
                              )}
                            </div>
                          ) : (
                            <span className="badge badge-neutral" style={{ fontSize: "0.72rem" }}>
                              {isInvestigating ? "Evaluating..." : "Awaiting Discovery"}
                            </span>
                          )}
                        </td>

                        {/* Actions */}
                        <td style={{ textAlign: "right" }}>
                          {inv && inv.status === "completed" ? (
                            <button
                              className="btn btn-secondary btn-sm"
                              style={{ borderRadius: "var(--radius-pill)", fontSize: "0.75rem", padding: "0.3rem 0.75rem" }}
                              onClick={() => onViewDossier(inv.id)}
                              title="View synthesized external evidence dossier"
                            >
                              <FileText size={12} />
                              View Dossier
                            </button>
                          ) : (
                            <button
                              className="btn btn-primary btn-sm"
                              style={{ borderRadius: "var(--radius-pill)", fontSize: "0.75rem", padding: "0.3rem 0.75rem" }}
                              disabled={isInvestigating}
                              onClick={() => onInvestigate(ev)}
                              title="Trigger external evidence discovery & verification pipeline"
                            >
                              <Search size={12} />
                              {isInvestigating ? "Investigating..." : "Investigate"}
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
      </section>
    </div>
  );
};
