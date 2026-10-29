import React from "react";
import { CheckCircle2, Loader2, Search, ShieldCheck, Sparkles, XCircle } from "lucide-react";
import { InvestigationStatus } from "../types";

export interface InvestigationProgressProps {
  status: InvestigationStatus;
  errorStage?: string | null;
  errorMessage?: string | null;
}

const STAGES = [
  { id: "searching", label: "External Discovery", desc: "Exa multi-intent web query", icon: Search },
  { id: "verifying", label: "Evidence Verification", desc: "Gemini structured assessment", icon: Sparkles },
  { id: "scoring", label: "ECI v1.1 Calculation", desc: "Deterministic eligibility gates", icon: ShieldCheck },
  { id: "completed", label: "Dossier Synthesis", desc: "Audit trail & human checklist", icon: CheckCircle2 },
];

export const InvestigationProgress: React.FC<InvestigationProgressProps> = ({
  status,
  errorStage,
  errorMessage,
}) => {
  const getStageIndex = (s: InvestigationStatus) => {
    switch (s) {
      case "searching":
        return 0;
      case "verifying":
        return 1;
      case "scoring":
        return 2;
      case "completed":
        return 3;
      default:
        return -1;
    }
  };

  const currentIndex = getStageIndex(status);
  const isFailed = status === "failed";

  return (
    <div
      style={{
        padding: "1.25rem",
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-card)",
        boxShadow: "var(--shadow-card)",
        margin: "1rem 0",
      }}
    >
      <div style={{ marginBottom: "1rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}>
            Investigation In Progress
          </h3>
          <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: "0.15rem" }}>
            Executing synchronous multi-source external verification pipeline
          </p>
        </div>
        {!isFailed && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", color: "var(--brand-primary)", fontSize: "0.78rem", fontWeight: 600 }}>
            <Loader2 size={15} className="animate-spin" />
            <span>Processing Live Stage</span>
          </div>
        )}
      </div>

      {/* Stepper track */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "0.75rem",
          position: "relative",
        }}
      >
        {STAGES.map((stage, idx) => {
          const Icon = stage.icon;
          const isDone = currentIndex > idx || (status === "completed" && idx === 3);
          const isCurrent = currentIndex === idx && !isFailed;
          const isErrorStage = isFailed && (errorStage?.toLowerCase().includes(stage.id) || idx === currentIndex);

          return (
            <div
              key={stage.id}
              style={{
                padding: "0.85rem 1rem",
                borderRadius: "var(--radius-sm)",
                backgroundColor: isCurrent
                  ? "var(--brand-primary-subtle)"
                  : isDone
                  ? "var(--band-very-strong-bg)"
                  : isErrorStage
                  ? "var(--contradiction-bg)"
                  : "var(--bg-app)",
                border: "1px solid",
                borderColor: isCurrent
                  ? "var(--brand-primary-border)"
                  : isDone
                  ? "var(--band-very-strong-border)"
                  : isErrorStage
                  ? "var(--contradiction-border)"
                  : "var(--border-subtle)",
                transition: "all var(--transition-normal)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.4rem" }}>
                <div
                  style={{
                    width: "26px",
                    height: "26px",
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: isCurrent
                      ? "var(--brand-primary)"
                      : isDone
                      ? "var(--band-very-strong)"
                      : isErrorStage
                      ? "var(--contradiction-color)"
                      : "#E2E8F0",
                    color: isDone || isCurrent || isErrorStage ? "#FFFFFF" : "var(--text-muted)",
                  }}
                >
                  {isCurrent ? (
                    <Loader2 size={13} className="animate-spin" />
                  ) : isDone ? (
                    <CheckCircle2 size={14} />
                  ) : isErrorStage ? (
                    <XCircle size={14} />
                  ) : (
                    <Icon size={13} />
                  )}
                </div>
                <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", fontWeight: 600 }}>
                  0{idx + 1}
                </span>
              </div>

              <div style={{ fontSize: "0.82rem", fontWeight: 600, color: isErrorStage ? "var(--contradiction-text)" : "var(--text-primary)" }}>
                {stage.label}
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>
                {stage.desc}
              </div>
            </div>
          );
        })}
      </div>

      {isFailed && (
        <div
          style={{
            marginTop: "1.25rem",
            padding: "0.875rem 1rem",
            backgroundColor: "var(--contradiction-bg)",
            border: "1px solid var(--contradiction-border)",
            borderRadius: "var(--radius-md)",
            fontSize: "0.82rem",
            color: "#FCA5A5",
          }}
        >
          <strong>Investigation failed at stage:</strong> {errorStage || "Unknown"}
          <br />
          <span>{errorMessage || "Pipeline execution encountered an unexpected error."}</span>
        </div>
      )}
    </div>
  );
};
