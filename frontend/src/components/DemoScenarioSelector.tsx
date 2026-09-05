import React, { useState } from "react";
import { AlertTriangle, Sparkles } from "lucide-react";
import { DemoScenarioResponse, InvestigationDetailResponse } from "../types";
import { BandBadge, LoadingSpinner } from "./Common";
import { DossierView } from "./DossierView";

export interface DemoScenarioSelectorProps {
  scenarios: DemoScenarioResponse[];
  isLoading: boolean;
  onBackToQueue: () => void;
}

export const DemoScenarioSelector: React.FC<DemoScenarioSelectorProps> = ({
  scenarios,
  isLoading,
  onBackToQueue,
}) => {
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  if (isLoading) {
    return <LoadingSpinner text="Loading deterministic demo scenarios from backend..." />;
  }

  if (!scenarios || scenarios.length === 0) {
    return (
      <div className="panel" style={{ padding: "2.5rem", textAlign: "center" }}>
        <AlertTriangle size={32} color="#F59E0B" style={{ margin: "0 auto 1rem auto" }} />
        <h3 style={{ fontSize: "1.1rem", fontWeight: 600 }}>Demo Scenarios Unavailable</h3>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "0.5rem" }}>
          The backend did not return any demo scenarios. Please ensure the server is running.
        </p>
      </div>
    );
  }

  const selectedScenario = scenarios[selectedIndex] || scenarios[0];

  // Adapt the demo scenario to an InvestigationDetailResponse for DossierView
  const adaptedInvestigation: InvestigationDetailResponse = {
    id: selectedScenario.dossier.investigation_id,
    risk_event_id: selectedScenario.dossier.anomaly_context.risk_event_id,
    status: "completed",
    eci_score: selectedScenario.eci_score,
    eci_band: selectedScenario.dossier.eci_result.band,
    eci_version: selectedScenario.dossier.eci_version,
    evidence_count: selectedScenario.evidence_count,
    created_at: selectedScenario.dossier.generated_at,
    dossier: selectedScenario.dossier,
    evidence_items: selectedScenario.evidence_items || [],
    verification_items: selectedScenario.verification_items || [],
    pipeline_metadata: selectedScenario.dossier.pipeline_metadata,
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.75rem" }}>
      {/* Demo Mode Notice Banner */}
      <div
        style={{
          padding: "1rem 1.25rem",
          backgroundColor: "rgba(245, 158, 11, 0.08)",
          border: "1px solid rgba(245, 158, 11, 0.25)",
          borderRadius: "var(--radius-lg)",
          display: "flex",
          alignItems: "flex-start",
          gap: "0.875rem",
        }}
      >
        <Sparkles size={20} color="#F59E0B" style={{ flexShrink: 0, marginTop: "2px" }} />
        <div>
          <div style={{ fontWeight: 600, color: "#F59E0B", fontSize: "0.9rem" }}>
            Deterministic Demonstration Mode (Offline Evaluation)
          </div>
          <p style={{ fontSize: "0.8rem", color: "#FDE68A", marginTop: "0.2rem", lineHeight: 1.45 }}>
            Deterministic demo mode provides a network-independent demonstration path for the external discovery and verification pipeline. These 3 canonical scenarios demonstrate strong external corroboration, clean zero-evidence discovery, and discrepancy handling without calling external search or LLM APIs.
          </p>
        </div>
      </div>

      {/* Scenario Cards Selector */}
      <div>
        <div style={{ fontSize: "0.75rem", textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--text-muted)", fontWeight: 600, marginBottom: "0.75rem" }}>
          Select Canonical Scenario Archetype ({scenarios.length})
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
            gap: "1rem",
          }}
        >
          {scenarios.map((scenario, idx) => {
            const isSelected = selectedIndex === idx;

            return (
              <div
                key={scenario.scenario_name}
                onClick={() => setSelectedIndex(idx)}
                style={{
                  padding: "1.25rem",
                  backgroundColor: isSelected ? "var(--bg-surface-elevated)" : "var(--bg-surface)",
                  border: "1px solid",
                  borderColor: isSelected ? "var(--accent-primary)" : "var(--border-subtle)",
                  borderRadius: "var(--radius-lg)",
                  cursor: "pointer",
                  boxShadow: isSelected ? "0 0 0 1px var(--accent-primary)" : "var(--shadow-sm)",
                  transition: "all var(--transition-fast)",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "0.75rem",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      SCENARIO 0{idx + 1}
                    </span>
                    <BandBadge band={scenario.eci_band} />
                  </div>

                  <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-primary)" }}>
                    {scenario.merchant_name}
                  </h3>

                  <div style={{ fontSize: "0.8rem", color: "#F87171", fontWeight: 600, marginTop: "0.2rem" }}>
                    {scenario.anomaly_summary}
                  </div>

                  <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.5rem", lineHeight: 1.4 }}>
                    {scenario.semantic_expectation}
                  </p>
                </div>

                <div
                  style={{
                    paddingTop: "0.75rem",
                    borderTop: "1px solid var(--border-subtle)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    fontSize: "0.75rem",
                  }}
                >
                  <span style={{ color: "var(--text-muted)" }}>
                    Discovered Evidence: <strong style={{ color: "var(--text-primary)" }}>{scenario.evidence_count} items</strong>
                  </span>
                  <span style={{ fontWeight: 700, color: isSelected ? "var(--accent-primary)" : "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
                    ECI: {scenario.eci_score}/100
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Render Selected Scenario Dossier */}
      <div style={{ marginTop: "1rem" }}>
        <DossierView
          investigation={adaptedInvestigation}
          onBackToQueue={onBackToQueue}
          isDemo={true}
        />
      </div>
    </div>
  );
};
