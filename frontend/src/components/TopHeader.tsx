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
      {/* Title & Universal Search */}
      <div className="header-title-wrap">
        <h1 className="header-title">Risk Investigation Console</h1>
        <div className="header-search">
          <Search size={14} className="search-icon-left" />
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Search merchants, anomalies, IDs..."
            value={searchVal}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          {searchVal ? (
            <button
              onClick={() => onSearchChange("")}
              style={{
                position: "absolute",
                right: "0.65rem",
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
              <X size={13} />
            </button>
          ) : (
            <span className="search-kbd">⌘K</span>
          )}
        </div>

        {isSearching && matchCount !== undefined && (
          <span
            style={{
              fontSize: "0.72rem",
              padding: "0.15rem 0.5rem",
              borderRadius: "var(--radius-pill)",
              backgroundColor: "var(--brand-primary-subtle)",
              color: "var(--brand-primary)",
              fontWeight: 600,
              border: "1px solid var(--brand-primary-border)",
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
          <Calendar size={13} color="var(--text-muted)" />
          <span>Queue Window: Latest Anomalies</span>
        </div>

        {/* Context-Aware Export Button */}
        {isDossierView ? (
          <button
            className="btn btn-secondary btn-sm"
            onClick={hasActiveDossier ? onExportDossier : undefined}
            title={hasActiveDossier ? "Export active evidence dossier JSON" : "No active dossier to export"}
            disabled={!hasActiveDossier}
          >
            <Download size={13} color="var(--text-secondary)" />
            <span>Export Dossier</span>
          </button>
        ) : (
          <button
            className="btn btn-secondary btn-sm"
            onClick={onExportQueue}
            title="Export active anomaly queue and investigation status summary JSON"
          >
            <Download size={13} color="var(--text-secondary)" />
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
              width: 6,
              height: 6,
              borderRadius: "50%",
              backgroundColor: isBackendConnected ? "var(--band-very-strong)" : "var(--contradiction-color)",
              display: "inline-block",
            }}
          />
          <span
            style={{
              fontSize: "0.72rem",
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
