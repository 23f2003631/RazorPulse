import React from "react";
import {
  AlertTriangle,
  Database,
  FileSearch,
  HelpCircle,
  LayoutDashboard,
  Plus,
  Radio,
  Shield,
  Zap,
} from "lucide-react";

export type ConsoleTab = "dashboard" | "investigations" | "dossier" | "demos" | "vault";

export interface SidebarProps {
  currentTab: ConsoleTab;
  onTabChange: (tab: ConsoleTab) => void;
  activeMode: "live" | "demo";
  onModeChange: (mode: "live" | "demo") => void;
  onOpenSimulateModal: () => void;
  onOpenHelpDocs: () => void;
  onFilterAnomaliesQueue?: (filter: "all" | "needs_investigation" | "investigated" | "contradictions") => void;
  needsInvestigationCount: number;
  investigationsCount: number;
  contradictionsCount: number;
  evidenceVaultCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  activeMode,
  onModeChange,
  onOpenSimulateModal,
  onOpenHelpDocs,
  onFilterAnomaliesQueue,
  needsInvestigationCount,
  investigationsCount,
  contradictionsCount,
  evidenceVaultCount,
}) => {
  const handleNavDashboard = () => {
    onModeChange("live");
    if (onFilterAnomaliesQueue) onFilterAnomaliesQueue("all");
    onTabChange("dashboard");
  };

  const handleNavRiskAnomalies = () => {
    onModeChange("live");
    if (onFilterAnomaliesQueue) onFilterAnomaliesQueue("needs_investigation");
    onTabChange("dashboard");
  };

  const handleNavInvestigations = () => {
    onTabChange("investigations");
  };

  const handleNavDemoScenarios = () => {
    onModeChange("demo");
    onTabChange("demos");
  };

  const handleNavEvidenceVault = () => {
    onTabChange("vault");
  };

  const handleNavContradictionRadar = () => {
    onModeChange("live");
    if (onFilterAnomaliesQueue) onFilterAnomaliesQueue("contradictions");
    onTabChange("dashboard");
  };

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div>
        <div className="sidebar-header">
          <div className="sidebar-brand" onClick={handleNavDashboard} title="RazorPulse Console Overview">
            <div className="brand-icon">
              <Zap size={17} fill="#FFFFFF" color="#FFFFFF" />
            </div>
            <div className="brand-info">
              <span className="brand-title">RazorPulse</span>
              <span className="brand-subtitle">External Corroboration</span>
            </div>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="sidebar-nav">
          {/* Dashboard */}
          <button
            className={`sidebar-nav-item ${currentTab === "dashboard" && activeMode === "live" ? "active" : ""}`}
            onClick={handleNavDashboard}
            title="Overview dashboard and active anomaly queue"
          >
            <div className="sidebar-nav-left">
              <LayoutDashboard size={18} />
              <span>Dashboard</span>
            </div>
          </button>

          {/* Risk Anomalies */}
          <button
            className="sidebar-nav-item"
            onClick={handleNavRiskAnomalies}
            title="Filter queue to uninvestigated payment anomalies"
          >
            <div className="sidebar-nav-left">
              <AlertTriangle size={18} />
              <span>Risk Anomalies</span>
            </div>
            <span className="sidebar-badge sidebar-badge-blue">{needsInvestigationCount}</span>
          </button>

          {/* Investigations */}
          <button
            className={`sidebar-nav-item ${currentTab === "investigations" ? "active" : ""}`}
            onClick={handleNavInvestigations}
            title="View all completed and in-flight investigations"
          >
            <div className="sidebar-nav-left">
              <FileSearch size={18} />
              <span>Investigations</span>
            </div>
            <span className="sidebar-badge sidebar-badge-blue">{investigationsCount}</span>
          </button>

          {/* Demo Scenarios */}
          <button
            className={`sidebar-nav-item ${currentTab === "demos" && activeMode === "demo" ? "active" : ""}`}
            onClick={handleNavDemoScenarios}
            title="Offline deterministic demonstration scenarios"
          >
            <div className="sidebar-nav-left">
              <Shield size={18} />
              <span>Demo Scenarios</span>
            </div>
            <span className="sidebar-badge sidebar-badge-emerald">3</span>
          </button>

          {/* Evidence Vault */}
          <button
            className={`sidebar-nav-item ${currentTab === "vault" ? "active" : ""}`}
            onClick={handleNavEvidenceVault}
            title="Searchable repository of external web citations"
          >
            <div className="sidebar-nav-left">
              <Database size={18} />
              <span>Evidence Vault</span>
            </div>
            {evidenceVaultCount > 0 && (
              <span className="sidebar-badge sidebar-badge-blue">{evidenceVaultCount}</span>
            )}
          </button>

          {/* Contradiction Radar */}
          <button
            className="sidebar-nav-item"
            onClick={handleNavContradictionRadar}
            title="Filter queue to anomalies with identified external refutations"
          >
            <div className="sidebar-nav-left">
              <Radio size={18} />
              <span>Contradiction Radar</span>
            </div>
            {contradictionsCount > 0 && (
              <span className="sidebar-badge sidebar-badge-rose">{contradictionsCount}</span>
            )}
          </button>

          {/* Help & Docs Reference */}
          <button
            className="sidebar-nav-item"
            onClick={onOpenHelpDocs}
            title="Open ECI v1.1 methodology and decision boundary guide"
          >
            <div className="sidebar-nav-left">
              <HelpCircle size={18} />
              <span>Help & Docs</span>
            </div>
          </button>
        </nav>
      </div>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        {/* Status Module */}
        <div className="sidebar-status-card">
          <div className="status-card-header">
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--band-very-strong)", display: "inline-block" }} />
            <span>ECI v1.1 Engine Active</span>
          </div>
          <p className="status-card-desc">
            Deterministic eligibility gating & cross-source corroboration.
          </p>
          <button
            className="status-card-btn"
            onClick={onOpenSimulateModal}
            title="Ingest a simulated payment risk anomaly"
          >
            <Plus size={13} />
            <span>Simulate Anomaly</span>
          </button>
        </div>

        {/* Buildathon attribution */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 0.25rem", fontSize: "0.72rem", color: "var(--text-muted)" }}>
          <span>Razorpay Buildathon</span>
          <span style={{ fontWeight: 600, fontFamily: "var(--font-mono)" }}>v1.0.0</span>
        </div>
      </div>
    </aside>
  );
};
