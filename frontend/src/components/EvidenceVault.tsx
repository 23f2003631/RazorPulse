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
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.75rem", marginBottom: "0.25rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
            <Database size={20} color="var(--brand-primary)" />
            <h1 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)" }}>
              Discovered Evidence Vault
            </h1>
          </div>
          <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: "0.15rem" }}>
            Read-only repository of external evidence discovered across RazorPulse investigations.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
          <span
            style={{
              fontSize: "0.72rem",
              padding: "0.2rem 0.6rem",
              borderRadius: "var(--radius-pill)",
              fontWeight: 600,
              backgroundColor: isDemoMode ? "var(--band-moderate-bg)" : "var(--brand-primary-subtle)",
              color: isDemoMode ? "var(--band-moderate-text)" : "var(--brand-primary-text)",
              border: isDemoMode ? "1px solid var(--band-moderate-border)" : "1px solid var(--brand-primary-border)",
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
      <div className="card" style={{ padding: "1.15rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1rem" }}>
          {/* Source Type Pills */}
          <div className="segmented-control">
            {sourceTypes.map((st) => (
              <button
                key={st.id}
                onClick={() => setSelectedSourceType(st.id)}
                className={`segmented-item ${selectedSourceType === st.id ? "active" : ""}`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {/* Search input */}
          <div style={{ position: "relative", width: 280 }}>
            <Search size={14} style={{ position: "absolute", left: "0.75rem", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
            <input
              type="text"
              placeholder="Search title, domain, snippet..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: "100%",
                height: 32,
                padding: "0 0.75rem 0 2.25rem",
                fontSize: "0.78rem",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border-subtle)",
                backgroundColor: "var(--bg-input)",
                outline: "none",
              }}
            />
          </div>
        </div>

        {/* Evidence items list */}
        {filtered.length === 0 ? (
          <EmptyState
            title="No evidence items found"
            description={
              items.length === 0
                ? "No external evidence has been gathered yet. Trigger an investigation to begin discovery."
                : "Adjust your search query or source filter to locate matching evidence items."
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
              ) : undefined
            }
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {filtered.map((item, idx) => (
              <div
                key={`${item.url}-${idx}`}
                style={{
                  padding: "0.95rem 1.15rem",
                  backgroundColor: "var(--bg-surface)",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.45rem",
                  transition: "border-color var(--transition-fast)",
                }}
              >
                {/* Header row */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                    <span
                      style={{
                        fontSize: "0.68rem",
                        fontFamily: "var(--font-mono)",
                        fontWeight: 700,
                        backgroundColor: "var(--brand-primary-subtle)",
                        color: "var(--brand-primary-text)",
                        padding: "0.1rem 0.4rem",
                        borderRadius: "var(--radius-xs)",
                        border: "1px solid var(--brand-primary-border)",
                      }}
                    >
                      [E{idx + 1}]
                    </span>
                    <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>
                      {item.title || "External Evidence Publication"}
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span
                      style={{
                        fontSize: "0.68rem",
                        textTransform: "capitalize",
                        padding: "0.1rem 0.4rem",
                        borderRadius: "var(--radius-pill)",
                        backgroundColor: "var(--bg-app)",
                        border: "1px solid var(--border-subtle)",
                        color: "var(--text-secondary)",
                      }}
                    >
                      {item.source_type.replace(/_/g, " ")}
                    </span>

                    {item.investigationId && onViewDossier && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onViewDossier(item.investigationId!)}
                        title="View investigation dossier"
                        style={{ height: "26px", fontSize: "0.7rem", padding: "0 0.5rem" }}
                      >
                        <FileText size={11} />
                        <span>Dossier</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Domain & metadata row */}
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "0.72rem", color: "var(--text-muted)", flexWrap: "wrap" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                    <Globe size={12} />
                    <span style={{ fontWeight: 600, color: "var(--text-secondary)" }}>{item.source_domain}</span>
                  </div>
                  {item.published_at && (
                    <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
                      <Calendar size={12} />
                      <span>{new Date(item.published_at).toLocaleDateString("en-IN")}</span>
                    </div>
                  )}
                  {item.merchantName && (
                    <span>
                      Subject: <strong>{item.merchantName}</strong>
                    </span>
                  )}
                </div>

                {/* Content snippet */}
                {item.content_snippet && (
                  <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", lineHeight: 1.45, backgroundColor: "var(--bg-app)", padding: "0.6rem 0.75rem", borderRadius: "var(--radius-xs)", border: "1px solid var(--border-subtle)" }}>
                    "{item.content_snippet}"
                  </p>
                )}

                {/* Link */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.72rem" }}>
                  <span style={{ color: "var(--text-muted)" }}>
                    Discovery query: <code style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem" }}>{item.discovery_query}</code>
                  </span>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.25rem",
                      color: "var(--brand-primary)",
                      fontWeight: 600,
                      textDecoration: "none",
                    }}
                  >
                    <span>Canonical Source</span>
                    <ExternalLink size={11} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
