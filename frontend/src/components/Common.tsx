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
          <CheckCircle2 size={11} />
          <span>{label || "Very Strong Corroboration"}</span>
        </span>
      );
    case "strong":
      return (
        <span className="badge badge-strong">
          <CheckCircle2 size={11} />
          <span>{label || "Strong Corroboration"}</span>
        </span>
      );
    case "moderate":
      return (
        <span className="badge badge-moderate">
          <Clock size={11} />
          <span>{label || "Moderate Corroboration"}</span>
        </span>
      );
    case "low":
    default:
      return (
        <span className="badge badge-low">
          <AlertTriangle size={11} />
          <span>{label || "Low Corroboration"}</span>
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
          <Loader2 size={11} className="animate-spin" /> Discovery
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
        <span className="badge badge-neutral">
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
        padding: "0.75rem 1rem",
        backgroundColor: "var(--contradiction-bg)",
        border: "1px solid var(--contradiction-border)",
        borderRadius: "var(--radius-sm)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "1rem",
        margin: "0.75rem 0",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <AlertTriangle size={16} color="var(--contradiction-color)" style={{ flexShrink: 0 }} />
        <span style={{ color: "var(--contradiction-text)", fontSize: "0.82rem", fontWeight: 500 }}>
          {message}
        </span>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-secondary btn-sm" style={{ height: "26px", fontSize: "0.72rem" }}>
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
        padding: "2.5rem 1rem",
        gap: "0.5rem",
        color: "var(--text-secondary)",
      }}
    >
      <Loader2 size={24} className="animate-spin" color="var(--brand-primary)" />
      <span style={{ fontSize: "0.82rem", fontWeight: 500 }}>{text}</span>
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
        padding: "2.5rem 1.5rem",
        backgroundColor: "var(--bg-surface)",
        border: "1px dashed var(--border-medium)",
        borderRadius: "var(--radius-md)",
      }}
    >
      <Info size={28} color="var(--text-faint)" style={{ margin: "0 auto 0.75rem auto" }} />
      <h3 style={{ fontSize: "0.95rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
        {title}
      </h3>
      <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", maxWidth: "420px", margin: "0 auto 1rem auto", lineHeight: 1.45 }}>
        {description}
      </p>
      {action && <div style={{ display: "inline-flex", justifyContent: "center" }}>{action}</div>}
    </div>
  );
};

/**
 * Format currency in Indian numbering format (e.g. ₹7.25L, ₹32,000).
 */
export function formatIndianCurrency(amount?: number | null, currency: string = "INR"): string {
  if (amount == null || isNaN(amount)) return "N/A";
  const symbol = currency === "INR" ? "₹" : `${currency} `;
  if (amount >= 10000000) {
    const cr = (amount / 10000000).toFixed(2).replace(/\.00$/, "");
    return `${symbol}${cr} Cr`;
  }
  if (amount >= 100000) {
    const l = (amount / 100000).toFixed(2).replace(/\.00$/, "");
    return `${symbol}${l}L`;
  }
  return `${symbol}${amount.toLocaleString("en-IN")}`;
}

/**
 * Format velocity surge percentage cleanly with thousands grouping (e.g. +1,606%).
 */
export function formatVelocitySurge(pct?: number | null): string {
  if (pct == null || isNaN(pct)) return "+0%";
  const rounded = Math.round(pct);
  return `+${rounded.toLocaleString("en-IN")}%`;
}

/**
 * Format baseline multiplier with distinct baseline label (e.g. 17.1× baseline).
 */
export function formatMultiplier(multiplier: string | number): string {
  return `${multiplier}× baseline`;
}
