import React from "react";
import { AlertTriangle, CheckCircle2, Clock, Info, Loader2, XCircle } from "lucide-react";
import { ECIBand, InvestigationStatus } from "../types";

export interface BandBadgeProps {
  band?: ECIBand | string | null;
  label?: string | null;
}

export const BandBadge: React.FC<BandBadgeProps> = ({ band, label }) => {
  if (!band) return <span className="badge badge-neutral">No Score</span>;

  const bandKey = typeof band === "string" ? band.toLowerCase() : "";

  switch (bandKey) {
    case "very_strong":
      return (
        <span className="badge badge-very-strong">
          <CheckCircle2 size={12} />
          {label || "Very Strong Corroboration"}
        </span>
      );
    case "strong":
      return (
        <span className="badge badge-strong">
          <CheckCircle2 size={12} />
          {label || "Strong Corroboration"}
        </span>
      );
    case "moderate":
      return (
        <span className="badge badge-moderate">
          <Clock size={12} />
          {label || "Moderate Corroboration"}
        </span>
      );
    case "low":
    default:
      return (
        <span className="badge badge-low">
          <AlertTriangle size={12} />
          {label || "Low Corroboration"}
        </span>
      );
  }
};

export interface StatusBadgeProps {
  status: InvestigationStatus | string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const s = status.toLowerCase();
  switch (s) {
    case "completed":
      return (
        <span className="badge badge-completed">
          <CheckCircle2 size={11} /> Completed
        </span>
      );
    case "searching":
      return (
        <span className="badge badge-pending">
          <Loader2 size={11} className="animate-spin" /> Searching
        </span>
      );
    case "verifying":
      return (
        <span className="badge badge-pending">
          <Loader2 size={11} className="animate-spin" /> Verifying
        </span>
      );
    case "scoring":
      return (
        <span className="badge badge-pending">
          <Loader2 size={11} className="animate-spin" /> Scoring
        </span>
      );
    case "pending":
      return (
        <span className="badge badge-pending">
          <Clock size={11} /> Needs Investigation
        </span>
      );
    case "failed":
      return (
        <span className="badge badge-failed">
          <XCircle size={11} /> Failed
        </span>
      );
    default:
      return <span className="badge badge-neutral">{status}</span>;
  }
};

export interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, onRetry }) => {
  return (
    <div
      style={{
        padding: "0.875rem 1.25rem",
        backgroundColor: "var(--contradiction-bg)",
        border: "1px solid var(--contradiction-border)",
        borderRadius: "var(--radius-md)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "1rem",
        margin: "1rem 0",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <AlertTriangle size={18} color="var(--contradiction-color)" />
        <span style={{ color: "var(--contradiction-text)", fontSize: "0.85rem", fontWeight: 500 }}>{message}</span>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-secondary btn-sm">
          Retry
        </button>
      )}
    </div>
  );
};

export const LoadingSpinner: React.FC<{ text?: string }> = ({ text = "Loading data..." }) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "3rem 1rem",
        gap: "0.75rem",
        color: "var(--text-secondary)",
      }}
    >
      <Loader2 size={28} className="animate-spin" color="var(--accent-primary)" />
      <span style={{ fontSize: "0.875rem" }}>{text}</span>
    </div>
  );
};

export const EmptyState: React.FC<{
  title: string;
  description: string;
  action?: React.ReactNode;
}> = ({ title, description, action }) => {
  return (
    <div
      style={{
        textAlign: "center",
        padding: "3.5rem 1.5rem",
        backgroundColor: "var(--bg-surface)",
        border: "1px dashed var(--border-medium)",
        borderRadius: "var(--radius-lg)",
      }}
    >
      <Info size={36} color="var(--text-muted)" style={{ margin: "0 auto 1rem auto" }} />
      <h3 style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.35rem" }}>
        {title}
      </h3>
      <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", maxWidth: "440px", margin: "0 auto 1.25rem auto" }}>
        {description}
      </p>
      {action}
    </div>
  );
};
