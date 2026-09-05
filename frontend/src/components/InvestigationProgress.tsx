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
        padding: "1.75rem",
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-medium)",
        borderRadius: "var(--radius-lg)",
        margin: "1.5rem 0",
      }}
    >
      <div style={{ marginBottom: "1.25rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)" }}>
            Investigation In Progress
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
            Executing synchronous multi-source external verification pipeline
          </p>
        </div>
        {!isFailed && (
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--accent-primary)", fontSize: "0.8rem", fontWeight: 600 }}>
            <Loader2 size={16} className="animate-spin" />
            <span>Processing Live Stage</span>
          </div>
        )}
      </div>

      {/* Stepper track */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "1rem",
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
                padding: "1rem",
                borderRadius: "var(--radius-md)",
                backgroundColor: isCurrent
                  ? "var(--accent-primary-subtle)"
                  : isDone
                  ? "rgba(16, 185, 129, 0.06)"
                  : isErrorStage
                  ? "var(--contradiction-bg)"
                  : "var(--bg-surface-elevated)",
                border: "1px solid",
                borderColor: isCurrent
                  ? "var(--accent-primary-border)"
                  : isDone
                  ? "rgba(16, 185, 129, 0.3)"
                  : isErrorStage
                  ? "var(--contradiction-border)"
                  : "var(--border-subtle)",
                transition: "all var(--transition-normal)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: isCurrent
                      ? "var(--accent-primary)"
                      : isDone
                      ? "#10B981"
                      : isErrorStage
                      ? "var(--contradiction-color)"
                      : "rgba(255, 255, 255, 0.05)",
                    color: isDone || isCurrent || isErrorStage ? "#FFFFFF" : "var(--text-muted)",
                  }}
                >
                  {isCurrent ? (
                    <Loader2 size={14} className="animate-spin" />
                  ) : isDone ? (
                    <CheckCircle2 size={16} />
                  ) : isErrorStage ? (
                    <XCircle size={16} />
                  ) : (
                    <Icon size={14} />
                  )}
                </div>
                <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 600 }}>
                  0{idx + 1}
                </span>
              </div>

              <div style={{ fontSize: "0.85rem", fontWeight: 600, color: isErrorStage ? "#FCA5A5" : "var(--text-primary)" }}>
                {stage.label}
              </div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
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
