import React, { useState } from "react";
import { AlertCircle, Plus, X } from "lucide-react";
import { RiskEventCreate } from "../types";

export interface SimulateAnomalyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: RiskEventCreate) => Promise<void>;
  isSubmitting: boolean;
}

const PRESETS: (RiskEventCreate & { label: string; desc: string })[] = [
  {
    label: "UrbanCraft India (Festive Campaign Surge)",
    desc: "1606% velocity surge (1,450 txns vs 85 baseline). Commercial festive handicraft collection.",
    merchant_name: "UrbanCraft India",
    merchant_domain: "urbancraft.in",
    anomaly_type: "transaction_velocity_spike",
    baseline_transaction_count: 85,
    observed_transaction_count: 1450,
    transaction_amount: 725000,
    currency: "INR",
    risk_reason: "Transaction velocity increased 17x above baseline over 3 hours.",
    geographic_info: "Bengaluru, Karnataka, IN",
    source: "simulated",
  },
  {
    label: "QuickDeal Bazaar (Unexplained Velocity Spike)",
    desc: "5400% velocity surge (2,200 txns vs 40 baseline). Zero external commercial announcement.",
    merchant_name: "QuickDeal Bazaar",
    merchant_domain: "quickdealbazaar.co.in",
    anomaly_type: "transaction_velocity_spike",
    baseline_transaction_count: 40,
    observed_transaction_count: 2200,
    transaction_amount: 1100000,
    currency: "INR",
    risk_reason: "Transaction count surged 55x above historical baseline within 2 hours.",
    geographic_info: "Surat, Gujarat, IN",
    source: "simulated",
  },
  {
    label: "TrendWear Daily (Disputed Commercial Event)",
    desc: "700% velocity surge (400 txns vs 50 baseline). Merchant public notice refutes flash sale.",
    merchant_name: "TrendWear Daily",
    merchant_domain: "trendweardaily.com",
    anomaly_type: "transaction_velocity_spike",
    baseline_transaction_count: 50,
    observed_transaction_count: 400,
    transaction_amount: 320000,
    currency: "INR",
    risk_reason: "Velocity spike during alleged promotional campaign contradicted by merchant refutation.",
    geographic_info: "Mumbai, Maharashtra, IN",
    source: "simulated",
  },
];

export const SimulateAnomalyModal: React.FC<SimulateAnomalyModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
}) => {
  const [selectedPresetIndex, setSelectedPresetIndex] = useState<number>(0);
  const [isCustom, setIsCustom] = useState<boolean>(false);
  const [formData, setFormData] = useState<RiskEventCreate>({
    merchant_name: "",
    merchant_domain: "",
    anomaly_type: "transaction_velocity_spike",
    baseline_transaction_count: 100,
    observed_transaction_count: 1200,
    transaction_amount: 500000,
    currency: "INR",
    risk_reason: "Unusual volume increase above baseline",
    source: "simulated",
  });

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isCustom) {
      await onSubmit({
        ...formData,
        occurred_at: new Date().toISOString(),
      });
    } else {
      const preset = PRESETS[selectedPresetIndex];
      await onSubmit({
        ...preset,
        occurred_at: new Date().toISOString(),
      });
    }
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="panel-header">
          <div className="panel-title">
            <Plus size={18} color="var(--accent-primary)" />
            <span>Simulate Payment Risk Anomaly</span>
          </div>
          <button
            onClick={onClose}
            style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.75rem",
                backgroundColor: "var(--brand-primary-subtle)",
                border: "1px solid var(--brand-primary-border)",
                borderRadius: "var(--radius-sm)",
                fontSize: "0.78rem",
                color: "var(--brand-primary-text)",
              }}
            >
              <AlertCircle size={16} style={{ flexShrink: 0 }} />
              <span>
                Ingests a simulated risk anomaly via <code>POST /api/v1/risk-events</code>. Does NOT execute payments or make automated decisions.
              </span>
            </div>

            {/* Mode selection: Preset vs Custom */}
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button
                type="button"
                className={`btn btn-sm ${!isCustom ? "btn-primary" : "btn-secondary"}`}
                style={{ flex: 1 }}
                onClick={() => setIsCustom(false)}
              >
                Standard Test Fixtures
              </button>
              <button
                type="button"
                className={`btn btn-sm ${isCustom ? "btn-primary" : "btn-secondary"}`}
                style={{ flex: 1 }}
                onClick={() => setIsCustom(true)}
              >
                Custom Event
              </button>
            </div>

            {!isCustom ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                <label className="kv-label">Select Representative Anomaly</label>
                {PRESETS.map((preset, idx) => (
                  <div
                    key={preset.merchant_name}
                    onClick={() => setSelectedPresetIndex(idx)}
                    style={{
                      padding: "0.75rem 1rem",
                      borderRadius: "var(--radius-md)",
                      backgroundColor: selectedPresetIndex === idx ? "var(--bg-surface-elevated)" : "var(--bg-app)",
                      border: "1px solid",
                      borderColor: selectedPresetIndex === idx ? "var(--accent-primary)" : "var(--border-subtle)",
                      cursor: "pointer",
                      transition: "all var(--transition-fast)",
                    }}
                  >
                    <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-primary)" }}>
                      {preset.label}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                      {preset.desc}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <div>
                  <label className="kv-label">Merchant Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.merchant_name}
                    onChange={(e) => setFormData({ ...formData, merchant_name: e.target.value })}
                    placeholder="e.g. UrbanCraft India"
                    style={{
                      width: "100%",
                      padding: "0.5rem 0.75rem",
                      backgroundColor: "var(--bg-input)",
                      border: "1px solid var(--border-medium)",
                      borderRadius: "var(--radius-md)",
                      marginTop: "0.25rem",
                    }}
                  />
                </div>
                <div>
                  <label className="kv-label">Merchant Domain (for external Exa search)</label>
                  <input
                    type="text"
                    value={formData.merchant_domain || ""}
                    onChange={(e) => setFormData({ ...formData, merchant_domain: e.target.value })}
                    placeholder="e.g. urbancraft.in"
                    style={{
                      width: "100%",
                      padding: "0.5rem 0.75rem",
                      backgroundColor: "var(--bg-input)",
                      border: "1px solid var(--border-medium)",
                      borderRadius: "var(--radius-md)",
                      marginTop: "0.25rem",
                    }}
                  />
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                  <div>
                    <label className="kv-label">Baseline Txn Count</label>
                    <input
                      type="number"
                      value={formData.baseline_transaction_count || 100}
                      onChange={(e) => setFormData({ ...formData, baseline_transaction_count: parseInt(e.target.value) || 0 })}
                      style={{
                        width: "100%",
                        padding: "0.5rem 0.75rem",
                        backgroundColor: "var(--bg-input)",
                        border: "1px solid var(--border-medium)",
                        borderRadius: "var(--radius-md)",
                        marginTop: "0.25rem",
                      }}
                    />
                  </div>
                  <div>
                    <label className="kv-label">Observed Txn Count</label>
                    <input
                      type="number"
                      value={formData.observed_transaction_count || 1200}
                      onChange={(e) => setFormData({ ...formData, observed_transaction_count: parseInt(e.target.value) || 0 })}
                      style={{
                        width: "100%",
                        padding: "0.5rem 0.75rem",
                        backgroundColor: "var(--bg-input)",
                        border: "1px solid var(--border-medium)",
                        borderRadius: "var(--radius-md)",
                        marginTop: "0.25rem",
                      }}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div
            style={{
              padding: "0.875rem 1.25rem",
              backgroundColor: "var(--bg-surface-elevated)",
              borderTop: "1px solid var(--border-subtle)",
              display: "flex",
              justifyContent: "flex-end",
              gap: "0.5rem",
            }}
          >
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? "Ingesting..." : "Ingest Anomaly"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
