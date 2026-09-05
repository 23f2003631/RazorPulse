import React from "react";
import { Activity, Play, ShieldAlert, Sparkles } from "lucide-react";

export interface NavbarProps {
  currentTab: "dashboard" | "dossier" | "demos";
  onTabChange: (tab: "dashboard" | "dossier" | "demos") => void;
  isBackendConnected: boolean;
  activeMode: "live" | "demo";
  onModeChange: (mode: "live" | "demo") => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onTabChange,
  isBackendConnected,
  activeMode,
  onModeChange,
}) => {
  return (
    <header
      style={{
        backgroundColor: "var(--bg-surface)",
        borderBottom: "1px solid var(--border-subtle)",
        position: "sticky",
        top: 0,
        zIndex: 40,
      }}
    >
      <div
        className="container"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "64px",
        }}
      >
        {/* Brand identity */}
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
          <div
            onClick={() => onTabChange("dashboard")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.625rem",
              cursor: "pointer",
            }}
          >
            <div
              style={{
                width: "34px",
                height: "34px",
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--accent-primary-subtle)",
                border: "1px solid var(--accent-primary-border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--accent-primary)",
              }}
            >
              <ShieldAlert size={20} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <span style={{ fontSize: "1.0625rem", fontWeight: 700, letterSpacing: "-0.01em", color: "var(--text-primary)" }}>
                  RazorPulse
                </span>
                <span
                  style={{
                    fontSize: "0.6875rem",
                    padding: "0.15rem 0.4rem",
                    borderRadius: "var(--radius-sm)",
                    backgroundColor: "rgba(59, 130, 246, 0.15)",
                    color: "var(--accent-primary)",
                    fontWeight: 600,
                  }}
                >
                  AI Risk Manager
                </span>
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", lineHeight: 1 }}>
                External-Context Verification Console
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav style={{ display: "flex", alignItems: "center", gap: "0.25rem", marginLeft: "1rem" }}>
            <button
              onClick={() => {
                onModeChange("live");
                onTabChange("dashboard");
              }}
              style={{
                background: "transparent",
                border: "none",
                padding: "0.4rem 0.75rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.8125rem",
                fontWeight: currentTab === "dashboard" ? 600 : 500,
                color: currentTab === "dashboard" ? "var(--text-primary)" : "var(--text-secondary)",
                backgroundColor: currentTab === "dashboard" ? "var(--bg-surface-elevated)" : "transparent",
                cursor: "pointer",
              }}
            >
              Anomalies Queue
            </button>
            <button
              onClick={() => {
                onModeChange("demo");
                onTabChange("demos");
              }}
              style={{
                background: "transparent",
                border: "none",
                padding: "0.4rem 0.75rem",
                borderRadius: "var(--radius-md)",
                fontSize: "0.8125rem",
                fontWeight: currentTab === "demos" ? 600 : 500,
                color: currentTab === "demos" ? "var(--text-primary)" : "var(--text-secondary)",
                backgroundColor: currentTab === "demos" ? "var(--bg-surface-elevated)" : "transparent",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.35rem",
              }}
            >
              <Sparkles size={14} color="#F59E0B" />
              Demo Scenarios
            </button>
          </nav>
        </div>

        {/* Right side controls: Mode Toggle & Health Indicator */}
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {/* Mode Pill Switcher */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              backgroundColor: "var(--bg-input)",
              border: "1px solid var(--border-medium)",
              borderRadius: "var(--radius-lg)",
              padding: "0.2rem",
            }}
          >
            <button
              onClick={() => onModeChange("live")}
              style={{
                padding: "0.3rem 0.75rem",
                borderRadius: "var(--radius-md)",
                border: "none",
                fontSize: "0.75rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.35rem",
                backgroundColor: activeMode === "live" ? "var(--accent-primary)" : "transparent",
                color: activeMode === "live" ? "#FFFFFF" : "var(--text-secondary)",
                transition: "all var(--transition-fast)",
              }}
            >
              <Activity size={12} />
              LIVE
            </button>
            <button
              onClick={() => {
                onModeChange("demo");
                onTabChange("demos");
              }}
              style={{
                padding: "0.3rem 0.75rem",
                borderRadius: "var(--radius-md)",
                border: "none",
                fontSize: "0.75rem",
                fontWeight: 600,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "0.35rem",
                backgroundColor: activeMode === "demo" ? "#D97706" : "transparent",
                color: activeMode === "demo" ? "#FFFFFF" : "var(--text-secondary)",
                transition: "all var(--transition-fast)",
              }}
            >
              <Play size={12} />
              DEMO (OFFLINE)
            </button>
          </div>

          {/* Backend Health Dot */}
          <div
            title={isBackendConnected ? "Backend API online (FastAPI :8000)" : "Backend disconnected"}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.72rem",
              color: "var(--text-muted)",
              padding: "0.25rem 0.5rem",
              backgroundColor: "rgba(255, 255, 255, 0.03)",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: isBackendConnected ? "#10B981" : "#EF4444",
                boxShadow: isBackendConnected ? "0 0 6px #10B981" : "none",
              }}
            />
            {isBackendConnected ? "API Connected" : "API Offline"}
          </div>
        </div>
      </div>
    </header>
  );
};
