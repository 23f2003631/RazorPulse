import React from "react";
import {
  BookOpen,
  ExternalLink,
  Layers,
  Scale,
  X,
} from "lucide-react";

export interface HelpDocsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HelpDocsModal: React.FC<HelpDocsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-box"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 680, width: "100%", maxHeight: "88vh", overflowY: "auto", padding: "2rem" }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            <BookOpen size={22} color="var(--accent-primary)" />
            <div>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-primary)" }}>
                RazorPulse Analyst Reference Guide
              </h2>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                External Evidence Corroboration & ECI v1.1 Methodology
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--text-muted)" }}
          >
            <X size={20} />
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {/* Card 1: Strategic Product Boundary */}
          <div
            style={{
              padding: "1rem 1.25rem",
              backgroundColor: "rgba(37, 99, 235, 0.06)",
              border: "1px solid var(--accent-primary-border)",
              borderRadius: "var(--radius-md)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--accent-primary)", fontWeight: 700, fontSize: "0.9rem", marginBottom: "0.35rem" }}>
              <Scale size={18} />
              <span>Decision-Support Boundary (Human-in-the-Loop)</span>
            </div>
            <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
              RazorPulse is an <strong>external evidence corroboration engine</strong>, NOT a fraud scoring engine.
              Its sole objective is to determine whether discoverable public external evidence (news, merchant releases, social announcements) corroborates a commercial explanation for a payment anomaly.
            </p>
            <ul style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.5rem", paddingLeft: "1.25rem", display: "flex", flexDirection: "column", gap: "0.2rem" }}>
              <li>RazorPulse never makes autonomous freeze, decline, or fund-hold decisions.</li>
              <li>A high ECI score indicates strong external corroboration, NOT low merchant risk.</li>
              <li>The human risk analyst retains final authority over all account actions.</li>
            </ul>
          </div>

          {/* Card 2: ECI v1.1 Heuristic Engine */}
          <div
            style={{
              padding: "1.25rem",
              backgroundColor: "var(--bg-surface-elevated)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-primary)", fontWeight: 700, fontSize: "0.92rem", marginBottom: "0.5rem" }}>
              <Layers size={17} color="var(--accent-primary)" />
              <span>ECI v1.1 Scoring Engine Architecture</span>
            </div>
            <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.75rem", lineHeight: 1.45 }}>
              The Event Corroboration Index (ECI) is calculated using a deterministic, explainable heuristic bounded strictly between <strong>0 and 100</strong>:
            </p>

            {/* Positive Dimensions Table */}
            <div style={{ fontSize: "0.78rem", marginBottom: "0.85rem" }}>
              <div style={{ fontWeight: 600, color: "#065F46", marginBottom: "0.35rem" }}>
                Positive Corroboration Dimensions (Max 100 pts)
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.4rem" }}>
                <div style={{ padding: "0.4rem 0.6rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
                  <strong>Merchant Entity Match:</strong> Max 25 pts
                </div>
                <div style={{ padding: "0.4rem 0.6rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
                  <strong>Temporal Alignment:</strong> Max 25 pts
                </div>
                <div style={{ padding: "0.4rem 0.6rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
                  <strong>Explanation Support:</strong> Max 20 pts
                </div>
                <div style={{ padding: "0.4rem 0.6rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)" }}>
                  <strong>Source Credibility:</strong> Max 20 pts
                </div>
                <div style={{ padding: "0.4rem 0.6rem", backgroundColor: "var(--bg-app)", borderRadius: "var(--radius-sm)", gridColumn: "1 / -1" }}>
                  <strong>Independence Bonus:</strong> Max 10 pts (&ge;3 claim groups: 10 pts; 2 groups: 5 pts)
                </div>
              </div>
            </div>

            {/* Deductions & Gating */}
            <div style={{ fontSize: "0.78rem", borderTop: "1px solid var(--border-subtle)", paddingTop: "0.75rem" }}>
              <div style={{ fontWeight: 600, color: "#991B1B", marginBottom: "0.35rem" }}>
                Per-Item Eligibility Gates & Penalty Deductions
              </div>
              <ul style={{ paddingLeft: "1.25rem", color: "var(--text-secondary)", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                <li><strong>Entity Gate:</strong> Unrelated evidence items receive 0 pts and are logged in the excluded-items audit trail.</li>
                <li><strong>Temporal Causality Gate:</strong> Items with post-anomaly timing cannot contribute causal explanation support.</li>
                <li><strong>Authority Ceiling:</strong> Low-credibility sources cap positive contributions per-item (e.g. at 29 pts).</li>
                <li><strong>Contradiction Deduction:</strong> -25 pts for severe discrepancies (e.g. official merchant refutations or multiple contradictions); -10 pts for a single discrepancy.</li>
                <li><strong>Uncertainty Deduction:</strong> -12 pts for high ambiguity; -6 pts for moderate gaps.</li>
              </ul>
            </div>
          </div>

          {/* Card 3: Qualitative Corroboration Bands */}
          <div
            style={{
              padding: "1rem 1.25rem",
              backgroundColor: "var(--bg-surface-elevated)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
            }}
          >
            <div style={{ fontWeight: 700, fontSize: "0.85rem", color: "var(--text-primary)", marginBottom: "0.5rem" }}>
              Qualitative ECI Corroboration Bands
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.5rem", fontSize: "0.75rem", textAlign: "center" }}>
              <div style={{ padding: "0.5rem", backgroundColor: "#ECFDF5", color: "#065F46", borderRadius: "var(--radius-sm)", border: "1px solid #A7F3D0" }}>
                <div style={{ fontWeight: 700 }}>VERY STRONG</div>
                <div style={{ fontWeight: 600 }}>80 – 100</div>
              </div>
              <div style={{ padding: "0.5rem", backgroundColor: "#EFF6FF", color: "#1E40AF", borderRadius: "var(--radius-sm)", border: "1px solid #BFDBFE" }}>
                <div style={{ fontWeight: 700 }}>STRONG</div>
                <div style={{ fontWeight: 600 }}>60 – 79</div>
              </div>
              <div style={{ padding: "0.5rem", backgroundColor: "#FFFBEB", color: "#92400E", borderRadius: "var(--radius-sm)", border: "1px solid #FDE68A" }}>
                <div style={{ fontWeight: 700 }}>MODERATE</div>
                <div style={{ fontWeight: 600 }}>30 – 59</div>
              </div>
              <div style={{ padding: "0.5rem", backgroundColor: "#F1F5F9", color: "#334155", borderRadius: "var(--radius-sm)", border: "1px solid #CBD5E1" }}>
                <div style={{ fontWeight: 700 }}>LOW</div>
                <div style={{ fontWeight: 600 }}>0 – 29</div>
              </div>
            </div>
          </div>

          {/* External Backend API Docs Links */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "0.5rem" }}>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              FastAPI Interactive Documentation:
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary btn-sm"
                style={{ fontSize: "0.72rem" }}
              >
                <ExternalLink size={12} />
                OpenAPI Swagger
              </a>
              <a
                href="http://localhost:8000/redoc"
                target="_blank"
                rel="noreferrer"
                className="btn btn-secondary btn-sm"
                style={{ fontSize: "0.72rem" }}
              >
                <ExternalLink size={12} />
                ReDoc
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
