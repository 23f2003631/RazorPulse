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

### 2. Evidence Normalization, Deduplication & Deterministic Ranking
- Canonicalizes discovered URLs (stripping tracking parameters like `utm_*` and `fbclid`).
- Classifies structural `source_type` (merchant official, news media, press release, social, industry, general web).
- Assigns stable UUID `evidence_id` for provenance tracking.
- Merges duplicate URL records, preserving highlights and richest text content.
- **Deterministic Selection**: Ranks discovered items by source type quality, highlight density, external relevance score, publication timestamp, and snippet length. Partitions items into the top $N$ (default: `GEMINI_MAX_EVIDENCE_ITEMS=4`) for LLM verification, and marks remaining items as `SKIPPED`.

### 3. Single-Batch Gemini Structured Verification
- **Model**: `gemini-3.5-flash-lite` via `google-genai` SDK (`2.21.0`).
- **Batch Evaluation**: Evaluates all top selected evidence items in a single Gemini request using `BatchEvidenceVerificationResponse` schema, reducing API call volume from $O(N)$ (e.g. 9 individual calls) to 1 single call per investigation.
- **Configuration**: Uses typed `types.GenerateContentConfig` with explicit `response_mime_type="application/json"`, Pydantic `response_schema=BatchEvidenceVerificationResponse`, and low `temperature=0.1`.
- **System Instruction**: Enforces strict evidence grounding in provided snippets (anti-hallucination) and non-fraud terminology.
- **Explicit Verification Statuses**:
  - `VERIFIED`: Successfully verified by Gemini structured evaluation.
  - `FAILED`: Verification failed due to model or provider limits (retains failure reason, contributes zero positive points to ECI).
  - `SKIPPED`: Exceeded top $N$ selection threshold (contributes zero positive points to ECI).
- **Resilience & Rate Limit Handling**:
  - Server-provided `retryDelay` headers (e.g. `45s`, `55s`) are honored directly instead of short exponential retries.
  - Non-transient daily quota exhaustion (`GenerateRequestsPerDay`, `generate_content_free_tier_requests`) fails immediately on attempt 1 without wasteful retries.
  - Transient provider load spikes (`503 UNAVAILABLE`, `504 DEADLINE_EXCEEDED`) use bounded exponential backoff (max 3 attempts).
  - Permanent client errors (400, 401, 403, 404, validation errors) fail immediately on attempt 1.
- **Verification Schema**: Returns `EvidenceVerificationItem` structured objects evaluating:
  - `merchant_match` (`direct_match`, `related_entity`, `unrelated`, `uncertain`)
  - `temporal_match` (`exact_match`, `window_match`, `historical_previous`, `post_anomaly`, `unrelated_timing`, `uncertain`)
  - `explanation_support` (`strong_explanation`, `moderate_explanation`, `weak_explanation`, `no_explanation`, `uncertain`)
  - `evidence_strength` (`strong_direct`, `moderate_indirect`, `weak_circumstantial`, `unsupported`, `contradicted`)
  - `source_credibility` (`high`, `medium`, `low`, `unknown`)
  - Extracted key facts, contradictions, and uncertainties.

### 4. Deterministic ECI Scoring & Dossier Synthesis
- See [ECI_SCORING.md](ECI_SCORING.md) for full formula breakdown.
- Positive points are awarded **ONLY** for `VERIFIED` items. `FAILED` and `SKIPPED` items award zero positive points.
- If 0 items are verified, ECI is 0 / Low External Corroboration.
- Synthesizes `EvidenceDossier` with traceable citations (`[E1]`, `[E2]`) for verified items, executive summary distinguishing verified vs unverified items, evidence gaps reflecting provider limits, and analyst review checklist.
- Persists all outputs to Supabase.
