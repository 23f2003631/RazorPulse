import React, { useState } from "react";
import {
  AlertOctagon,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileCheck,
  FileText,
  Filter,
  Globe,
  Info,
  Layers,
  Sparkles,
  Zap,
} from "lucide-react";
import {
  EvidenceDossier,
  EvidenceVerificationItem,
  InvestigationDetailResponse,
} from "../types";
import { BandBadge, StatusBadge } from "./Common";

export interface DossierViewProps {
  investigation: InvestigationDetailResponse;
  onBackToQueue: () => void;
  isDemo?: boolean;
}

export const DossierView: React.FC<DossierViewProps> = ({
  investigation,
  onBackToQueue,
  isDemo = false,
}) => {
  const [methodologyOpen, setMethodologyOpen] = useState(false);

  const dossier: EvidenceDossier | undefined | null = investigation.dossier;
  const eci = dossier?.eci_result;
  const anomaly = dossier?.anomaly_context;
  const citations = dossier?.evidence_citations || [];
  const contradictions = dossier?.contradictions || [];
  const checklist = dossier?.analyst_review_checklist || [];
  const metadata = dossier?.pipeline_metadata || investigation.pipeline_metadata;

  // Map verification items by evidence_id for quick lookup
  const verificationsMap = new Map<string, EvidenceVerificationItem>();
  (investigation.verification_items || []).forEach((v) => {
    verificationsMap.set(v.evidence_id, v);
  });

  if (!dossier || !eci) {
    return (
      <div className="panel" style={{ padding: "2.5rem", textAlign: "center" }}>
        <AlertTriangle size={32} color="#F59E0B" style={{ margin: "0 auto 1rem auto" }} />
        <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>Dossier Not Available</h3>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "0.5rem" }}>
          This investigation has not synthesized a completed dossier yet. Status: {investigation.status}
        </p>
        <button className="btn btn-secondary" onClick={onBackToQueue} style={{ marginTop: "1.25rem" }}>
          <ArrowLeft size={14} /> Back to Anomaly Queue
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Top action navigation */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <button className="btn btn-secondary btn-sm" onClick={onBackToQueue}>
          <ArrowLeft size={14} />
          Back to Anomaly Queue
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {isDemo && (
            <span
              style={{
                fontSize: "0.72rem",
                padding: "0.2rem 0.5rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: "rgba(245, 158, 11, 0.15)",
                color: "#F59E0B",
                fontWeight: 600,
                border: "1px solid rgba(245, 158, 11, 0.3)",
              }}
            >
              DEMO SCENARIO (OFFLINE EVALUATION)
            </span>
          )}
          <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
            Investigation ID: {investigation.id.slice(0, 8)}...
          </span>
        </div>
      </div>

      {/* Section 1: Anomaly Context Header */}
      <div
        className="panel"
        style={{
          padding: "1.5rem",
          background: "linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(11, 15, 25, 0.95) 100%)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <h1 style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {anomaly?.merchant_name || "Unknown Merchant"}
              </h1>
              {anomaly?.merchant_domain && (
                <a
                  href={`https://${anomaly.merchant_domain}`}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.25rem",
                    fontSize: "0.8rem",
                    color: "var(--text-secondary)",
                  }}
                >
                  <Globe size={13} />
                  {anomaly.merchant_domain}
                  <ExternalLink size={11} />
                </a>
              )}
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.35rem", maxWidth: "600px" }}>
              {anomaly?.risk_reason || "Unusual transaction velocity anomaly flagged for external corroboration review."}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <StatusBadge status={investigation.status} />
            <BandBadge band={eci.band} label={eci.band_label} />
          </div>
        </div>

        {/* Anomaly parameters grid */}
        <div
          className="kv-grid"
          style={{
            marginTop: "1.5rem",
            paddingTop: "1.25rem",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          <div className="kv-item">
            <span className="kv-label">Observed Velocity Surge</span>
            <span className="kv-value" style={{ color: "#F87171", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.3rem" }}>
              <Zap size={14} />
              +{anomaly?.percentage_change ? anomaly.percentage_change.toFixed(0) : "0"}%
            </span>
          </div>
          <div className="kv-item">
            <span className="kv-label">Observed vs Baseline Txns</span>
            <span className="kv-value">
              {anomaly?.observed_transaction_count?.toLocaleString()} txns <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>(baseline {anomaly?.baseline_transaction_count?.toLocaleString()})</span>
            </span>
          </div>
          <div className="kv-item">
            <span className="kv-label">Reported Volume</span>
            <span className="kv-value">
              {anomaly?.currency || "INR"} {anomaly?.transaction_amount?.toLocaleString() || "N/A"}
            </span>
          </div>
          <div className="kv-item">
            <span className="kv-label">Event Timestamp & Geo</span>
            <span className="kv-value" style={{ fontSize: "0.8rem" }}>
              {anomaly?.occurred_at ? new Date(anomaly.occurred_at).toLocaleString("en-IN") : "N/A"}
              {anomaly?.geographic_info && (
                <span style={{ color: "var(--text-muted)", display: "block", fontSize: "0.72rem" }}>
                  {anomaly.geographic_info}
                </span>
              )}
            </span>
          </div>
        </div>
      </div>

      {/* Section 2: Primary ECI Corroboration Score Hero Card */}
      <div
        className="panel"
        style={{
          padding: "1.75rem",
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-medium)",
          display: "grid",
          gridTemplateColumns: "240px 1fr",
          gap: "2rem",
          alignItems: "center",
        }}
      >
        {/* Score gauge / block */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "1.5rem 1rem",
            backgroundColor: "var(--bg-surface-elevated)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--border-medium)",
            textAlign: "center",
          }}
        >
          <span style={{ fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", fontWeight: 600 }}>
            Event Corroboration Index
          </span>
          <div
            style={{
              fontSize: "3.25rem",
              fontWeight: 800,
              lineHeight: 1.1,
              marginTop: "0.5rem",
              color:
                eci.band === "very_strong"
                  ? "var(--band-very-strong)"
                  : eci.band === "strong"
                  ? "var(--band-strong)"
                  : eci.band === "moderate"
                  ? "var(--band-moderate)"
                  : "var(--band-low)",
            }}
          >
            {eci.eci_score}
            <span style={{ fontSize: "1.125rem", fontWeight: 500, color: "var(--text-muted)" }}>/100</span>
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <BandBadge band={eci.band} label={eci.band_label} />
          </div>
          <div
            style={{
              fontSize: "0.72rem",
              color: "var(--text-muted)",
              marginTop: "0.75rem",
              padding: "0.2rem 0.5rem",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              borderRadius: "var(--radius-sm)",
            }}
          >
            {eci.confidence_level} EVALUATION CONFIDENCE
          </div>
        </div>

        {/* Narrative & Non-Fraud Disclaimer */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div>
            <h3 style={{ fontSize: "1.0625rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.5rem" }}>
              External Evidence Synthesis
            </h3>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
              {dossier.executive_summary}
            </p>
          </div>

          {/* Mandatory product disclaimer */}
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: "0.625rem",
              padding: "0.75rem 1rem",
              backgroundColor: "rgba(59, 130, 246, 0.06)",
              border: "1px solid var(--accent-primary-border)",
              borderRadius: "var(--radius-md)",
              fontSize: "0.78rem",
              color: "#93C5FD",
              lineHeight: 1.45,
            }}
          >
            <Info size={16} style={{ flexShrink: 0, marginTop: "2px" }} />
            <span>
              <strong>Decision-Support Boundary:</strong> {eci.disclaimer}
            </span>
          </div>
        </div>
      </div>

      {/* Section 3: Factor Contribution Breakdown */}
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">
            <Layers size={16} color="var(--accent-primary)" />
            <span>ECI v1.1 Itemized Factor Breakdown</span>
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Positive Points: <strong style={{ color: "#10B981" }}>+{eci.positive_points}</strong> | Penalties:{" "}
            <strong style={{ color: "#EF4444" }}>-{eci.penalty_points}</strong>
          </div>
        </div>
        <div className="panel-body" style={{ padding: "0" }}>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Scoring Dimension</th>
                  <th>Evaluated Attribute</th>
                  <th>Points Awarded</th>
                  <th>Max</th>
                  <th>Deterministic Explanation</th>
                </tr>
              </thead>
              <tbody>
                {eci.factors.map((factor, idx) => {
                  const isPenalty = factor.points_awarded < 0;
                  const isZero = factor.points_awarded === 0;

                  return (
                    <tr key={`${factor.factor_id}-${idx}`}>
                      <td>
                        <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                          {factor.name}
                        </div>
                        <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                          {factor.category}
                        </div>
                      </td>
                      <td>
                        <code style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                          {factor.raw_value}
                        </code>
                      </td>
                      <td>
                        <span
                          style={{
                            fontWeight: 700,
                            fontFamily: "var(--font-mono)",
                            color: isPenalty ? "#EF4444" : isZero ? "var(--text-muted)" : "#10B981",
                          }}
                        >
                          {factor.points_awarded > 0 ? `+${factor.points_awarded}` : factor.points_awarded} pts
                        </span>
                      </td>
                      <td style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>
                        {factor.max_possible_points > 0 ? `${factor.max_possible_points} pts` : "—"}
                      </td>
                      <td style={{ fontSize: "0.8rem", color: "var(--text-secondary)", maxWidth: "420px" }}>
                        {factor.explanation}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Section 4: Contradictions & Discrepancies Alert */}
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">
            <AlertOctagon size={16} color={contradictions.length > 0 ? "#EF4444" : "#10B981"} />
            <span>Contradiction & Discrepancy Assessment</span>
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Cross-source conflict detection
          </span>
        </div>
        <div className="panel-body">
          {contradictions.length > 0 ? (
            <div
              style={{
                padding: "1rem 1.25rem",
                backgroundColor: "var(--contradiction-bg)",
                border: "1px solid var(--contradiction-border)",
                borderRadius: "var(--radius-md)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "#EF4444", fontWeight: 600, marginBottom: "0.5rem" }}>
                <AlertTriangle size={18} />
                <span>Contradictory Evidence Identified Across Sources</span>
              </div>
              <p style={{ fontSize: "0.82rem", color: "#FCA5A5", marginBottom: "0.75rem" }}>
                The external public record contains claims that conflict with or refute the proposed commercial explanation.
              </p>
              <ul style={{ paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                {contradictions.map((contra, idx) => (
                  <li key={idx} style={{ color: "#FEE2E2", fontSize: "0.82rem" }}>
                    {contra}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.75rem",
                padding: "1rem 1.25rem",
                backgroundColor: "rgba(16, 185, 129, 0.06)",
                border: "1px solid rgba(16, 185, 129, 0.25)",
                borderRadius: "var(--radius-md)",
              }}
            >
              <CheckCircle2 size={18} color="#10B981" style={{ flexShrink: 0 }} />
              <div>
                <div style={{ fontWeight: 600, color: "#10B981", fontSize: "0.85rem" }}>
                  No Contradictory Evidence Identified
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: "0.15rem" }}>
                  Discovered sources contain no conflicting factual assertions regarding the merchant's commercial activity. Note: Absence of contradiction does not imply absence of risk.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Section 5: Discovered Evidence Timeline & Source Cards */}
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">
            <FileText size={16} color="var(--accent-primary)" />
            <span>Discovered Evidence & Source Citations ({citations.length} cited / {investigation.evidence_items?.length || 0} processed)</span>
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Traceable external web sources
          </span>
        </div>
        <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          {investigation.evidence_items && investigation.evidence_items.length > 0 ? (
            investigation.evidence_items.map((item, idx) => {
              const citation = citations.find((c) => c.evidence_id === item.evidence_id);
              const verification = verificationsMap.get(item.evidence_id);
              const citationTag = citation ? citation.citation_id : `[E${idx + 1}]`;

              return (
                <div
                  key={item.evidence_id}
                  style={{
                    padding: "1.25rem",
                    backgroundColor: "var(--bg-surface-elevated)",
                    border: "1px solid var(--border-medium)",
                    borderRadius: "var(--radius-md)",
                    transition: "border-color var(--transition-fast)",
                  }}
                >
                  {/* Card top: Citation tag, title, domain, external link */}
                  <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem" }}>
                        <span
                          style={{
                            padding: "0.15rem 0.45rem",
                            borderRadius: "var(--radius-sm)",
                            backgroundColor: "rgba(59, 130, 246, 0.2)",
                            color: "var(--accent-primary)",
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.72rem",
                            fontWeight: 700,
                          }}
                        >
                          {citationTag}
                        </span>
                        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                          {item.source_type}
                        </span>
                        {item.published_at && (
                          <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                            <Calendar size={11} />
                            {item.published_at.slice(0, 10)}
                          </span>
                        )}
                      </div>
                      <h4 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}>
                        {item.title || "External Source Document"}
                      </h4>
                    </div>

                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary btn-sm"
                      style={{ flexShrink: 0 }}
                    >
                      <ExternalLink size={12} />
                      Visit Source
                    </a>
                  </div>

                  {/* Verification badges */}
                  {verification && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", margin: "0.75rem 0" }}>
                      <span className="badge badge-neutral">
                        Entity: {verification.merchant_match}
                      </span>
                      <span className="badge badge-neutral">
                        Timing: {verification.temporal_match}
                      </span>
                      <span className="badge badge-neutral">
                        Support: {verification.explanation_support}
                      </span>
                      <span className="badge badge-neutral">
                        Strength: {verification.evidence_strength}
                      </span>
                      <span className="badge badge-neutral">
                        Credibility: {verification.source_credibility}
                      </span>
                    </div>
                  )}

                  {/* Content snippet */}
                  {item.content_snippet && (
                    <div
                      style={{
                        fontSize: "0.82rem",
                        color: "var(--text-secondary)",
                        padding: "0.75rem",
                        backgroundColor: "var(--bg-app)",
                        borderLeft: "3px solid var(--accent-primary)",
                        borderRadius: "var(--radius-sm)",
                        margin: "0.5rem 0",
                        fontStyle: "italic",
                      }}
                    >
                      "{item.content_snippet}"
                    </div>
                  )}

                  {/* Highlights / Key facts */}
                  {item.highlights && item.highlights.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginTop: "0.5rem" }}>
                      {item.highlights.map((h, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: "0.72rem",
                            padding: "0.15rem 0.4rem",
                            backgroundColor: "rgba(255, 255, 255, 0.05)",
                            borderRadius: "var(--radius-sm)",
                            color: "var(--text-secondary)",
                          }}
                        >
                          • {h}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Query intent origin */}
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "0.75rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span>Discovered via query: <code>{item.discovery_query}</code></span>
                    <span>({item.discovery_query_intent})</span>
                  </div>
                </div>
              );
            })
          ) : (
            <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              Zero external web evidence was discovered for this merchant and timeframe.
            </div>
          )}
        </div>
      </div>

      {/* Section 6: Excluded Evidence Transparency Audit */}
      {eci.excluded_items && eci.excluded_items.length > 0 && (
        <div className="panel">
          <div className="panel-header">
            <div className="panel-title">
              <Filter size={16} color="var(--exclusion-color)" />
              <span>Evidence Excluded from Corroboration by ECI v1.1 Gating ({eci.excluded_items.length})</span>
            </div>
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Transparent audit trail of non-contributing evidence
            </span>
          </div>
          <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
              ECI v1.1 implements strict per-item eligibility gates. Evidence items that fail entity alignment, temporal causality, or source authority rules are excluded from positive score contribution:
            </p>
            {eci.excluded_items.map((ex, idx) => (
              <div
                key={idx}
                style={{
                  padding: "0.875rem 1rem",
                  backgroundColor: "var(--exclusion-bg)",
                  border: "1px solid var(--exclusion-border)",
                  borderRadius: "var(--radius-md)",
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  gap: "1rem",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span
                      style={{
                        fontSize: "0.72rem",
                        padding: "0.15rem 0.4rem",
                        borderRadius: "var(--radius-sm)",
                        backgroundColor: "rgba(249, 115, 22, 0.2)",
                        color: "#F97316",
                        fontWeight: 700,
                        fontFamily: "var(--font-mono)",
                      }}
                    >
                      EXCLUDED: {ex.exclusion_reason}
                    </span>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      Evidence ID: {ex.evidence_id.slice(0, 8)}...
                    </span>
                  </div>
                  <div style={{ fontSize: "0.82rem", color: "#FED7AA", marginTop: "0.35rem" }}>
                    {ex.explanation}
                  </div>
                </div>
                <div style={{ textAlign: "right", flexShrink: 0 }}>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Awarded</div>
                  <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#94A3B8" }}>0 pts</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section 7: Analyst Review Guidance Checklist */}
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">
            <FileCheck size={16} color="#10B981" />
            <span>Recommended Human Analyst Review Actions</span>
          </div>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
            Preserving human risk decision authority
          </span>
        </div>
        <div className="panel-body">
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
            The following verification checklist is generated based on discovered evidence density, cited sources, and identified discrepancies:
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
            {checklist.map((check, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "0.75rem",
                  padding: "0.75rem 1rem",
                  backgroundColor: "var(--bg-surface-elevated)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                <input
                  type="checkbox"
                  id={`check-${idx}`}
                  style={{ marginTop: "0.2rem", cursor: "pointer", accentColor: "var(--accent-primary)" }}
                />
                <label
                  htmlFor={`check-${idx}`}
                  style={{ fontSize: "0.82rem", color: "var(--text-primary)", cursor: "pointer", lineHeight: 1.4 }}
                >
                  {check}
                </label>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Section 8: Methodology & Reproducibility Accordion */}
      <div className="panel">
        <div
          className="panel-header"
          onClick={() => setMethodologyOpen(!methodologyOpen)}
          style={{ cursor: "pointer" }}
        >
          <div className="panel-title">
            <Sparkles size={16} color="var(--accent-primary)" />
            <span>Engineering Methodology & Reproducibility Metadata</span>
          </div>
          <button style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}>
            {methodologyOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>

        {methodologyOpen && (
          <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            <div className="kv-grid">
              <div className="kv-item">
                <span className="kv-label">ECI Engine Formula</span>
                <span className="kv-value">v1.1 (Per-Item Eligibility & Claim Groups)</span>
              </div>
              <div className="kv-item">
                <span className="kv-label">Pipeline Version</span>
                <span className="kv-value">{metadata?.pipeline_version || "0.3.0"}</span>
              </div>
              <div className="kv-item">
                <span className="kv-label">Gemini Verifier Model</span>
                <span className="kv-value">{metadata?.gemini_model || "gemini-3.5-flash-lite"}</span>
              </div>
              <div className="kv-item">
                <span className="kv-label">Prompt Version</span>
                <span className="kv-value">{metadata?.verification_prompt_version || "v1"}</span>
              </div>
            </div>

            {/* Stage durations */}
            {metadata?.stage_durations && (
              <div>
                <span className="kv-label" style={{ display: "block", marginBottom: "0.5rem" }}>
                  Execution Latency Breakdown
                </span>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {Object.entries(metadata.stage_durations).map(([stage, dur]) => (
                    <div
                      key={stage}
                      style={{
                        padding: "0.35rem 0.65rem",
                        backgroundColor: "var(--bg-app)",
                        borderRadius: "var(--radius-sm)",
                        border: "1px solid var(--border-subtle)",
                        fontSize: "0.75rem",
                      }}
                    >
                      <span style={{ color: "var(--text-muted)", textTransform: "capitalize" }}>{stage}: </span>
                      <strong style={{ color: "var(--accent-primary)" }}>{dur}s</strong>
                    </div>
                  ))}
                  {metadata.total_duration_seconds && (
                    <div
                      style={{
                        padding: "0.35rem 0.65rem",
                        backgroundColor: "rgba(59, 130, 246, 0.1)",
                        borderRadius: "var(--radius-sm)",
                        border: "1px solid var(--accent-primary-border)",
                        fontSize: "0.75rem",
                      }}
                    >
                      <span style={{ color: "var(--accent-primary)" }}>Total Pipeline: </span>
                      <strong style={{ color: "#93C5FD" }}>{metadata.total_duration_seconds}s</strong>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
