/**
 * RazorPulse Domain Models and API Schemas.
 * 
 * Strict TypeScript mirror of the backend FastAPI / Pydantic v2 domain models.
 * Decision-support only — no autonomous payment decisions or fraud scores.
 */

// ============================================================
// Risk Events
// ============================================================

export type RiskEventStatus = "pending" | "investigating" | "completed" | "archived";

export interface RiskEvent {
  id: string;
  merchant_id?: string | null;
  merchant_name: string;
  merchant_domain?: string | null;
  anomaly_type: string;
  occurred_at: string;
  baseline_transaction_count?: number | null;
  observed_transaction_count?: number | null;
  percentage_change?: number | null;
  transaction_amount?: number | null;
  currency: string;
  risk_reason?: string | null;
  geographic_info?: string | null;
  source: string; // "simulated" | "manual" | "historical"
  status: RiskEventStatus;
  created_at: string;
  updated_at?: string | null;
}

export interface RiskEventCreate {
  merchant_name: string;
  merchant_domain?: string | null;
  anomaly_type?: string;
  occurred_at?: string;
  baseline_transaction_count?: number | null;
  observed_transaction_count?: number | null;
  transaction_amount?: number | null;
  currency?: string;
  risk_reason?: string | null;
  geographic_info?: string | null;
  source?: string;
}

export interface RiskEventListResponse {
  data: RiskEvent[];
  count: number;
}

// ============================================================
// Evidence & Normalization
// ============================================================

export type SourceType =
  | "merchant_official"
  | "news_media"
  | "press_release"
  | "social_community"
  | "industry_portal"
  | "general_web";

export interface NormalizedEvidence {
  evidence_id: string;
  url: string;
  title?: string | null;
  source_domain: string;
  source_type: SourceType;
  published_at?: string | null;
  retrieved_at: string;
  content_snippet?: string | null;
  highlights: string[];
  discovery_query: string;
  discovery_query_intent: string;
  external_score?: number | null;
}

// ============================================================
// Verification (Gemini)
// ============================================================

export type MerchantMatchLevel = "direct_match" | "related_entity" | "unrelated" | "uncertain";
export type TemporalMatchLevel =
  | "exact_match"
  | "window_match"
  | "historical_previous"
  | "post_anomaly"
  | "unrelated_timing"
  | "uncertain";
export type ExplanationSupportLevel =
  | "strong_explanation"
  | "moderate_explanation"
  | "weak_explanation"
  | "no_explanation"
  | "uncertain";
export type EvidenceStrength =
  | "strong_direct"
  | "moderate_indirect"
  | "weak_circumstantial"
  | "unsupported"
  | "contradicted";
export type SourceCredibilityLevel = "high" | "medium" | "low" | "unknown";
export type VerificationStatus = "verified" | "failed" | "skipped";

export interface EvidenceVerificationItem {
  evidence_id: string;
  status: VerificationStatus;
  failure_reason?: string | null;
  merchant_match: MerchantMatchLevel;
  temporal_match: TemporalMatchLevel;
  explanation_support: ExplanationSupportLevel;
  evidence_strength: EvidenceStrength;
  source_credibility: SourceCredibilityLevel;
  event_category?: string | null;
  key_facts: string[];
  contradictions_identified: string[];
  uncertainties_noted: string[];
  reasoning_summary: string;
}

// ============================================================
// Event Corroboration Index (ECI v1.1)
// ============================================================

export type ECIBand = "low" | "moderate" | "strong" | "very_strong";

export type ECIFactorCategory =
  | "entity_match"
  | "temporal_alignment"
  | "explanation_support"
  | "source_credibility"
  | "independent_corroboration"
  | "contradiction_penalty"
  | "uncertainty_penalty"
  | "gating_exclusion";

export interface ECIFactorContribution {
  factor_id: string;
  category: ECIFactorCategory;
  name: string;
  raw_value: string;
  points_awarded: number;
  max_possible_points: number;
  explanation: string;
  evidence_ids: string[];
}

export interface ECIExcludedItem {
  evidence_id: string;
  exclusion_reason: string; // "entity_mismatch" | "temporal_ineligible" | "contradicted_source"
  explanation: string;
  raw_contribution: number;
}

export interface ECIScoreResult {
  eci_score: number; // 0 to 100
  band: ECIBand;
  band_label: string;
  confidence_level: "HIGH" | "MEDIUM" | "LOW" | string;
  eci_version: string;
  positive_points: number;
  penalty_points: number;
  factors: ECIFactorContribution[];
  excluded_items: ECIExcludedItem[];
  eligible_evidence_count: number;
  is_zero_evidence: boolean;
  disclaimer: string;
}

// ============================================================
// Evidence Dossier
// ============================================================

export interface AnomalySummary {
  risk_event_id: string;
  merchant_name: string;
  merchant_domain?: string | null;
  anomaly_type: string;
  occurred_at: string;
  baseline_transaction_count?: number | null;
  observed_transaction_count?: number | null;
  percentage_change?: number | null;
  transaction_amount?: number | null;
  currency: string;
  risk_reason?: string | null;
  geographic_info?: string | null;
}

export interface EvidenceCitation {
  citation_id: string;
  evidence_id: string;
  url: string;
  title?: string | null;
  source_domain: string;
  source_type: string;
  key_fact: string;
  temporal_match: string;
  source_credibility: string;
}

export interface PipelineMetadata {
  pipeline_version: string;
  eci_version: string;
  search_strategy_version: string;
  verification_prompt_version: string;
  gemini_model: string;
  gemini_max_evidence_items: number;
  started_at: string;
  completed_at: string;
  total_duration_seconds?: number | null;
  stage_durations: Record<string, number>;
  query_count: number;
  evidence_discovered_count: number;
  evidence_usable_count: number;
  evidence_verified_count: number;
  evidence_skipped_count: number;
  evidence_failed_count: number;
  claim_clusters_count: number;
}

export interface EvidenceDossier {
  investigation_id: string;
  generated_at: string;
  pipeline_version: string;
  eci_version: string;
  pipeline_metadata?: PipelineMetadata | null;
  anomaly_context: AnomalySummary;
  executive_summary: string;
  eci_result: ECIScoreResult;
  evidence_count: number;
  evidence_citations: EvidenceCitation[];
  contradictions: string[];
  evidence_gaps: string[];
  verification_uncertainties: string[];
  analyst_review_checklist: string[];
  search_queries_used: Record<string, any>[];
}

// ============================================================
// Investigation Lifecycle
// ============================================================

export type InvestigationStatus =
  | "pending"
  | "searching"
  | "verifying"
  | "scoring"
  | "completed"
  | "failed";

export interface InvestigationResponse {
  id: string;
  risk_event_id: string;
  status: InvestigationStatus;
  eci_score?: number | null;
  eci_band?: ECIBand | null;
  eci_version: string;
  evidence_count: number;
  error_stage?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface InvestigationDetailResponse {
  id: string;
  risk_event_id: string;
  status: InvestigationStatus;
  eci_score?: number | null;
  eci_band?: ECIBand | null;
  eci_version: string;
  evidence_count: number;
  error_stage?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  updated_at?: string | null;
  dossier?: EvidenceDossier | null;
  evidence_items: NormalizedEvidence[];
  verification_items: EvidenceVerificationItem[];
  pipeline_metadata?: PipelineMetadata | null;
}

export interface InvestigationListResponse {
  data: InvestigationResponse[];
  count: number;
}

// ============================================================
// Demo Scenarios (Single Source of Truth from backend)
// ============================================================

export interface DemoScenarioResponse {
  scenario_name: string;
  scenario_title: string;
  semantic_expectation: string;
  merchant_name: string;
  anomaly_summary: string;
  evidence_count: number;
  eci_score: number;
  eci_band: string;
  factors_summary: {
    category: string;
    points: number;
    max: number;
    explanation: string;
  }[];
  contradictions: string[];
  analyst_checklist: string[];
  dossier: EvidenceDossier;
  evidence_items: NormalizedEvidence[];
  verification_items: EvidenceVerificationItem[];
}

export interface DemoScenarioListResponse {
  scenarios: DemoScenarioResponse[];
}
