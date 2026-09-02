# RazorPulse — Investigation Pipeline Architecture

## Overview

The Investigation Pipeline is the core intelligence workflow of RazorPulse. It ingests an anomalous risk event, generates hypothesis-driven search queries, discovers external web evidence via Exa AI, verifies evidence credibility and relevance via Google Gemini, deterministically calculates the Event Corroboration Index (ECI v1), and generates an analyst-facing Evidence Dossier.

## Pipeline Lifecycle & Stages

```
   [Risk Event Created]
            │
            ▼
┌───────────────────────┐
│       PENDING         │  ← Investigation record initialized
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│      SEARCHING        │  ← QueryIntentBuilder generates bounded intents
│                       │  ← ExaSearchStrategy executes searches & deduplicates
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│      VERIFYING        │  ← GeminiVerifier assesses evidence items with
│                       │    Pydantic response schema enforcement
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│       SCORING         │  ← ECIEngine calculates deterministic ECI v1 heuristic
│                       │  ← DossierGenerator compiles Evidence Dossier
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│      COMPLETED        │  ← Full results persisted to Supabase
└───────────────────────┘
            │  (if unrecoverable error occurs at any stage)
            ▼
┌───────────────────────┐
│        FAILED         │  ← error_stage & error_message persisted
└───────────────────────┘
```

## Stage Details

### 1. Context Construction & Query Intent Generation
- Resolves merchant name, domain, anomaly category, occurred_at timestamp, and risk reason.
- Generates up to 4 bounded query intents:
  1. `TIMEFRAME_EVENT`: `"[merchant]" news [month year]`
  2. `MERCHANT_ANNOUNCEMENT`: `site:[domain] launch OR sale OR announcement`
  3. `COMMERCIAL_CAMPAIGN`: `"[merchant]" sale OR campaign OR launch OR viral`
  4. `ANOMALY_CONTEXT`: `"[merchant]" surge OR demand OR sold out`

### 2. Evidence Normalization & Deduplication
- Canonicalizes discovered URLs (stripping tracking parameters like `utm_*` and `fbclid`).
- Classifies structural `source_type` (merchant official, news media, press release, social, industry, general web).
- Assigns stable UUID `evidence_id` for provenance tracking.
- Merges duplicate URL records, preserving highlights and richest text content.

### 3. Gemini Structured Verification
- System prompt enforces strict evidence grounding in provided snippets (anti-hallucination).
- Returns `EvidenceVerificationItem` structured objects evaluating:
  - `merchant_match` (`direct_match`, `related_entity`, `unrelated`, `uncertain`)
  - `temporal_match` (`exact_match`, `window_match`, `historical_previous`, `post_anomaly`, `unrelated_timing`, `uncertain`)
  - `explanation_support` (`strong_explanation`, `moderate_explanation`, `weak_explanation`, `no_explanation`, `uncertain`)
  - `evidence_strength` (`strong_direct`, `moderate_indirect`, `weak_circumstantial`, `unsupported`, `contradicted`)
  - `source_credibility` (`high`, `medium`, `low`, `unknown`)
  - Extracted key facts, contradictions, and uncertainties.

### 4. Deterministic ECI Scoring & Dossier Synthesis
- See [ECI_SCORING.md](ECI_SCORING.md) for full formula breakdown.
- Synthesizes `EvidenceDossier` with citations (`[E1]`, `[E2]`), executive summary, contradictions, evidence gaps, and analyst review checklist.
- Persists all outputs to Supabase.
