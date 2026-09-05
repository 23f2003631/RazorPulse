import React, { useState } from "react";
import {
  Calendar,
  Database,
  ExternalLink,
  FileText,
  Globe,
  Search,
} from "lucide-react";
import { NormalizedEvidence } from "../types";
import { EmptyState } from "./Common";

export interface VaultEvidenceItem extends NormalizedEvidence {
  investigationId?: string;
  merchantName?: string;
  isDemo?: boolean;
}

export interface EvidenceVaultProps {
  items: VaultEvidenceItem[];
  isDemoMode: boolean;
  onViewDossier?: (investigationId: string) => void;
  onBackToDashboard: () => void;
}

export const EvidenceVault: React.FC<EvidenceVaultProps> = ({
  items,
  isDemoMode,
  onViewDossier,
  onBackToDashboard,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSourceType, setSelectedSourceType] = useState<string>("all");

  const sourceTypes: { id: string; label: string }[] = [
    { id: "all", label: `All Sources (${items.length})` },
    { id: "news_media", label: "News & Media" },
    { id: "merchant_official", label: "Merchant Official" },
    { id: "social_community", label: "Social & Community" },
    { id: "press_release", label: "Press Release" },
  ];

  // Filter items
  const filtered = items.filter((item) => {
    if (selectedSourceType !== "all" && item.source_type !== selectedSourceType) {
      return false;
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const title = (item.title || "").toLowerCase();
      const domain = (item.source_domain || "").toLowerCase();
      const snippet = (item.content_snippet || "").toLowerCase();
      const merchant = (item.merchantName || "").toLowerCase();
      const query = (item.discovery_query || "").toLowerCase();
      return (
        title.includes(q) ||
        domain.includes(q) ||
        snippet.includes(q) ||
        merchant.includes(q) ||
        query.includes(q)
      );
    }
    return true;
  });

  return (
    <div className="page-container">
      {/* Header bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem", marginBottom: "1.5rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Database size={22} color="var(--accent-primary)" />
            <h1 style={{ fontSize: "1.4rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Discovered Evidence Vault
            </h1>
          </div>
          <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.25rem" }}>
            Read-only repository of external evidence discovered across RazorPulse investigations.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span
            style={{
              fontSize: "0.75rem",
              padding: "0.25rem 0.65rem",
              borderRadius: "var(--radius-pill)",
              fontWeight: 600,
              backgroundColor: isDemoMode ? "rgba(245, 158, 11, 0.12)" : "rgba(37, 99, 235, 0.12)",
              color: isDemoMode ? "#D97706" : "var(--accent-primary)",
              border: isDemoMode ? "1px solid rgba(245, 158, 11, 0.3)" : "1px solid var(--accent-primary-border)",
            }}
          >
            {isDemoMode ? "Deterministic Demo Evidence" : "Live Investigation Evidence"}
          </span>

          <button className="btn btn-secondary btn-sm" onClick={onBackToDashboard}>
            Return to Dashboard
          </button>
        </div>
      </div>

      {/* Filter & Search Bar Card */}
      <div className="card" style={{ padding: "1.25rem 1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1.25rem" }}>
          {/* Source Type Pills */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
            {sourceTypes.map((st) => (
              <button
                key={st.id}
                onClick={() => setSelectedSourceType(st.id)}
                style={{
                  padding: "0.3rem 0.75rem",
                  borderRadius: "var(--radius-pill)",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  border: "1px solid",
                  borderColor: selectedSourceType === st.id ? "var(--accent-primary)" : "var(--border-subtle)",
                  backgroundColor: selectedSourceType === st.id ? "var(--accent-primary-subtle)" : "#FFFFFF",
                  color: selectedSourceType === st.id ? "var(--accent-primary)" : "var(--text-secondary)",
                  cursor: "pointer",
                  transition: "all var(--transition-fast)",
                }}
              >
                {st.label}
              </button>
            ))}
          </div>

          {/* Instant Search input */}
          <div style={{ position: "relative", width: 300 }}>
            <Search size={14} style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Search evidence title, domain, snippet..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: "100%",
                padding: "0.45rem 0.75rem 0.45rem 2.25rem",
                fontSize: "0.78rem",
                borderRadius: "var(--radius-pill)",
                border: "1px solid var(--border-subtle)",
                backgroundColor: "var(--bg-app)",
                outline: "none",
              }}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                style={{
                  position: "absolute",
                  right: "0.6rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "transparent",
                  border: "none",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  color: "var(--text-muted)",
                }}
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Evidence List */}
        {filtered.length === 0 ? (
          <EmptyState
            title="No evidence items found"
            description={
              items.length === 0
                ? "No investigations have been completed yet. Run an investigation to discover and verify external public evidence."
                : "No evidence items match your current search or source-type filter."
            }
            action={
              items.length > 0 ? (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setSelectedSourceType("all");
                    setSearchQuery("");
                  }}
                >
                  Reset Filters
                </button>
              ) : null
            }
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {filtered.map((item, idx) => (
              <div
                key={`${item.evidence_id}-${idx}`}
                style={{
                  padding: "1.25rem",
                  backgroundColor: "var(--bg-surface-elevated)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  transition: "border-color var(--transition-fast)",
                }}
              >
                {/* Top header row */}
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "1rem" }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem" }}>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          fontWeight: 700,
                          padding: "0.15rem 0.45rem",
                          borderRadius: "var(--radius-sm)",
                          backgroundColor: "rgba(37, 99, 235, 0.12)",
                          color: "var(--accent-primary)",
                          textTransform: "uppercase",
                        }}
                      >
                        {item.source_type.replace("_", " ")}
                      </span>

                      <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                        <Globe size={12} />
                        {item.source_domain}
                      </span>

                      {item.merchantName && (
                        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 600 }}>
                          • {item.merchantName}
                        </span>
                      )}

                      {item.published_at && (
                        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "0.25rem" }}>
                          <Calendar size={11} />
                          {item.published_at.slice(0, 10)}
                        </span>
                      )}
                    </div>

                    <h3 style={{ fontSize: "0.98rem", fontWeight: 600, color: "var(--text-primary)" }}>
                      {item.title || "External Source Document"}
                    </h3>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexShrink: 0 }}>
                    {item.investigationId && onViewDossier && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onViewDossier(item.investigationId!)}
                        style={{ fontSize: "0.75rem" }}
                      >
                        <FileText size={12} />
                        View Dossier
                      </button>
                    )}

                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="btn btn-secondary btn-sm"
                      style={{ fontSize: "0.75rem" }}
                    >
                      <ExternalLink size={12} />
                      Visit Source
                    </a>
                  </div>
                </div>

                {/* Content snippet */}
                {item.content_snippet && (
                  <div
                    style={{
                      fontSize: "0.82rem",
                      color: "var(--text-secondary)",
                      padding: "0.65rem 0.85rem",
                      backgroundColor: "var(--bg-app)",
                      borderLeft: "3px solid var(--accent-primary)",
                      borderRadius: "var(--radius-sm)",
                      margin: "0.65rem 0",
                      fontStyle: "italic",
                      lineHeight: 1.45,
                    }}
                  >
                    "{item.content_snippet}"
                  </div>
                )}

                {/* Highlights */}
                {item.highlights && item.highlights.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginTop: "0.4rem" }}>
                    {item.highlights.map((h, i) => (
                      <span
                        key={i}
                        style={{
                          fontSize: "0.72rem",
                          padding: "0.15rem 0.4rem",
                          backgroundColor: "rgba(0, 0, 0, 0.04)",
                          borderRadius: "var(--radius-sm)",
                          color: "var(--text-secondary)",
                        }}
                      >
                        • {h}
                      </span>
                    ))}
                  </div>
                )}

                {/* Query intent metadata */}
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "0.65rem" }}>
                  Discovered via Exa query: <code style={{ color: "var(--text-secondary)" }}>{item.discovery_query}</code> ({item.discovery_query_intent})
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
