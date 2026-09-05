import React, { useEffect, useRef } from "react";
import { Calendar, Download, Search, X } from "lucide-react";

export interface TopHeaderProps {
  isBackendConnected: boolean;
  searchVal: string;
  onSearchChange: (query: string) => void;
  matchCount?: number;
  isSearching: boolean;
  currentTab: string;
  hasActiveDossier: boolean;
  onExportDossier: () => void;
  onExportQueue: () => void;
  onOpenHealthModal: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  isBackendConnected,
  searchVal,
  onSearchChange,
  matchCount,
  isSearching,
  currentTab,
  hasActiveDossier,
  onExportDossier,
  onExportQueue,
  onOpenHealthModal,
}) => {
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Global shortcut ⌘K / Ctrl+K to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const isDossierView = currentTab === "dossier";

  return (
    <header className="top-header">
      {/* Title & Universal Live-as-You-Type Search */}
      <div className="header-title-wrap">
        <h1 className="header-title">Risk Investigation Console</h1>
        <div className="header-search">
          <Search size={15} className="search-icon-left" />
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Search loaded merchants, anomaly types, IDs..."
            value={searchVal}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          {searchVal ? (
            <button
              onClick={() => onSearchChange("")}
              style={{
                position: "absolute",
                right: "0.75rem",
                top: "50%",
                transform: "translateY(-50%)",
                background: "transparent",
                border: "none",
                cursor: "pointer",
                color: "var(--text-muted)",
                padding: "2px",
                display: "flex",
                alignItems: "center",
              }}
              title="Clear search"
            >
              <X size={14} />
            </button>
          ) : (
            <span className="search-kbd">⌘K</span>
          )}
        </div>

        {isSearching && matchCount !== undefined && (
          <span
            style={{
              fontSize: "0.72rem",
              padding: "0.2rem 0.5rem",
              borderRadius: "var(--radius-pill)",
              backgroundColor: "rgba(37, 99, 235, 0.1)",
              color: "var(--accent-primary)",
              fontWeight: 600,
            }}
          >
            {matchCount} match{matchCount === 1 ? "" : "es"}
          </span>
        )}
      </div>

      {/* Right Controls */}
      <div className="header-actions">
        {/* Dynamic Queue Window Indicator */}
        <div className="header-badge-pill" title="Current risk anomaly ingestion window">
          <Calendar size={14} color="var(--text-muted)" />
          <span>Queue Window: Latest Recorded Anomalies</span>
        </div>

        {/* Context-Aware Export Button */}
        {isDossierView ? (
          <button
            className="header-btn-primary"
            style={{
              backgroundColor: "#FFFFFF",
              color: "var(--text-primary)",
              border: "1px solid var(--border-subtle)",
              boxShadow: "var(--shadow-sm)",
              opacity: hasActiveDossier ? 1 : 0.6,
              cursor: hasActiveDossier ? "pointer" : "not-allowed",
            }}
            onClick={hasActiveDossier ? onExportDossier : undefined}
            title={hasActiveDossier ? "Export active evidence dossier JSON & printable report" : "No active dossier to export"}
            disabled={!hasActiveDossier}
          >
            <Download size={14} color="var(--text-secondary)" />
            <span>Export Dossier</span>
          </button>
        ) : (
          <button
            className="header-btn-primary"
            style={{
              backgroundColor: "#FFFFFF",
              color: "var(--text-primary)",
              border: "1px solid var(--border-subtle)",
              boxShadow: "var(--shadow-sm)",
              cursor: "pointer",
            }}
            onClick={onExportQueue}
            title="Export active anomaly queue and investigation status summary JSON"
          >
            <Download size={14} color="var(--text-secondary)" />
            <span>Export Queue Summary</span>
          </button>
        )}

        {/* Clickable Backend Connection Status */}
        <button
          className="header-badge-pill"
          onClick={onOpenHealthModal}
          style={{
            borderColor: isBackendConnected ? "var(--band-very-strong-border)" : "var(--contradiction-border)",
            backgroundColor: isBackendConnected ? "var(--band-very-strong-bg)" : "var(--contradiction-bg)",
            cursor: "pointer",
            transition: "all var(--transition-fast)",
            outline: "none",
          }}
          title="Click to view Backend Health & Credential Readiness"
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: isBackendConnected ? "#10B981" : "#EF4444",
              display: "inline-block",
              boxShadow: isBackendConnected ? "0 0 6px rgba(16, 185, 129, 0.6)" : "none",
            }}
          />
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: 600,
              color: isBackendConnected ? "var(--band-very-strong-text)" : "var(--contradiction-text)",
            }}
          >
            {isBackendConnected ? "Backend Connected" : "Backend Offline"}
          </span>
        </button>

        {/* Analyst Profile Avatar */}
        <div
          className="avatar-circle"
          title="Risk Analyst Console • Decision Support Mode (Human-in-the-Loop)"
          style={{ cursor: "default" }}
        >
          RP
        </div>
      </div>
    </header>
  );
};
