# RazorPulse — Day 2 Development Log

## Objective

Build and verify the first end-to-end RazorPulse Investigation Pipeline:
`Risk Event -> Investigation Context -> Exa External Evidence Search -> Normalized Evidence -> Gemini Verification -> Deterministic ECI v1 Engine -> Evidence Dossier -> Supabase Persistence -> Analyst API`.

## What Was Implemented

### 1. Investigation Domain & Schemas
- `NormalizedEvidence`: Decoupled evidence schema with canonical URL, domain extraction, `SourceType` metadata classification (merchant official, news media, press release, social community, industry portal, general web), highlights, and stable UUIDs.
- `canonicalize_url`: Conservative URL canonicalization stripping tracking parameters (`utm_*`, `fbclid`, `gclid`) while preserving functional query paths.
- `EvidenceVerificationItem`: Structured verification assessment evaluated by Gemini (Merchant match level, Temporal match level, Explanation support level, Evidence strength, Source credibility level, Key facts, Contradictions, Uncertainties, Reasoning summary).
- `VerificationResult`: Consolidated cross-evidence assessments.
- `ECIScoreResult` & `ECIFactorContribution`: Deterministic ECI scoring output with itemized positive contributions, contradiction deductions, uncertainty deductions, and qualitative bands.
- `EvidenceDossier`: Synthesized analyst dossier including anomaly context, executive summary, ECI breakdown, evidence citations (`[E1]`, `[E2]`), contradictions, evidence gaps, uncertainties, and human review checklist.
- `InvestigationStatus`: Lifecycle states (`PENDING`, `SEARCHING`, `VERIFYING`, `SCORING`, `COMPLETED`, `FAILED`).
- `InvestigationCreate`, `InvestigationResponse`, `InvestigationDetailResponse`, `InvestigationListResponse`.

### 2. Database Schema Migration 002
- Authored `database/schemas/002_investigations_schema.sql` adding structured columns:
  - `eci_score` (INTEGER)
  - `eci_band` (TEXT)
  - `eci_version` (TEXT DEFAULT 'v1')
  - `evidence_count` (INTEGER DEFAULT 0)
  - `error_stage` (TEXT)
  - `error_message` (TEXT)
  - `search_queries` (JSONB)
  - `eci_breakdown` (JSONB)
  - `dossier` (JSONB)
  - `evidence_items` (JSONB)
  - `verification_items` (JSONB)

### 3. Exa Search Strategy & Query Intent Builder
- `QueryIntentBuilder`: Generates bounded, deterministic search queries from risk event context across 5 structured query intents:
  - `TIMEFRAME_EVENT`: Specific month/year news search around the anomaly date.
  - `MERCHANT_ANNOUNCEMENT`: Official merchant domain search for product launches, flash sales, campaigns.
  - `COMMERCIAL_CAMPAIGN`: Public web search for promotional discounts, viral social events, launches.
  - `ANOMALY_CONTEXT`: Tailored to anomaly category (velocity spikes, volume surges, geographic expansion).
  - `IDENTITY_CONTEXT`: General brand background and corporate profile.
- `ExaSearchStrategy`: Executes multi-intent searches with per-query error resilience, normalizes raw results, and deduplicates canonical URLs.

### 4. Gemini Evidence Verifier & Resilience
- **Model**: `gemini-3.6-flash` using official unified `google-genai` SDK (v2.21.0).
- **Typed Configuration**: Uses typed `types.GenerateContentConfig` for structured output with Pydantic schemas (`response_schema=EvidenceVerificationItem`).
- **Anti-Hallucination Prompt**: `VERIFICATION_SYSTEM_INSTRUCTION` forces strict evidence grounding in provided text snippets, explicit distinction between factual proof and plausibility, explicit contradiction detection, and neutral non-fraud terminology.
- **Transient Retry Wrapper**: `with_gemini_retry` provides bounded exponential backoff (max 3 attempts with 2s, 4s delays) for transient provider errors (`503 UNAVAILABLE`, `429 RESOURCE_EXHAUSTED`). Non-transient errors (400, 401, 403, 404, validation errors) fail immediately.
- **Fallback & Error Stage**: Handles item evaluation exceptions gracefully; persistent 503 provider outages after retry exhaustion fail cleanly with `FAILED` status and `error_stage="verifying"`.

### 5. Deterministic ECI v1 Heuristic Engine
- Implemented pure Python rule engine (`app/services/scoring/eci_engine.py`) calculating ECI bounded to `[0, 100]` with `eci_version = "v1"`.
- Separated orthogonal dimensions:
  - **Entity Match (0–25 pts):** Direct (25), Related (12), Uncertain (5), Unrelated (0)
  - **Temporal Alignment (0–25 pts):** Exact (25), Window (18), Historical (5), Uncertain (5), Unrelated (0)
  - **Explanation Support (0–20 pts):** Strong (20), Moderate (14), Weak (6), Uncertain (4), None (0)
  - **Source Credibility & Directness (0–20 pts):** High Credibility + Direct (20), High + Indirect (16), Medium + Direct/Indirect (13), Low/Circumstantial (5), Unknown/Unsupported (2)
  - **Independent Corroboration Bonus (0–10 pts):** +5 for 2 independent domains, +10 for 3+ independent domains
  - **Contradiction Penalty (-10 to -30 pts):** -10 for 1 contradiction, -25 for severe/multiple conflicts
  - **Uncertainty Penalty (-5 to -15 pts):** -6 for moderate gaps, -12 for pervasive ambiguity
- Explicit zero-evidence state: ECI = 0, `is_zero_evidence = True`, `Low External Corroboration`.
- Complete itemized factor breakdown with evidence provenance IDs.

### 6. Evidence Dossier Generator
- `DossierGenerator`: Compiles comprehensive decision-support dossier for human risk analysts.
- Features traceable citations (`[E1]`, `[E2]`), neutral terminology (no "red flags" jargon), transparent ECI reconciliation, evidence gaps, and actionable review checklist.

### 7. Investigation Repository & Orchestrator
- `investigation_repository`: Supabase CRUD, status transitions, and structured result persistence.
- `InvestigationOrchestrator`: Coordinates the full synchronous lifecycle (`PENDING` -> `SEARCHING` -> `VERIFYING` -> `SCORING` -> `COMPLETED`), handles zero-evidence and partial failure gracefully, captures `error_stage` and `error_message` on unrecoverable failures.

### 8. API Endpoints
- `POST /api/v1/investigations`: Ingests `{ "risk_event_id": UUID }`, executes pipeline synchronously, returns `InvestigationDetailResponse` with full dossier (HTTP 201).
- `GET /api/v1/investigations/{id}`: Returns complete investigation details and dossier (HTTP 200).
- `GET /api/v1/investigations`: Lists investigations with pagination and optional `status` / `risk_event_id` filters (HTTP 200).

### 9. Test Suite & Invariant Validation
- Authored 87 automated tests (unit and integration) — **100% passing**:
  - `test_config.py` (12 tests)
  - `test_schemas.py` (14 tests)
  - `test_health.py` (4 tests)
  - `test_risk_events.py` (7 tests)
  - `test_query_generation.py` (5 tests)
  - `test_evidence_normalization.py` (6 tests)
  - `test_gemini_verifier.py` (3 tests)
  - `test_gemini_retry.py` (14 tests)
  - `test_eci_engine.py` (10 tests validating all 10 Score Invariants)
  - `test_dossier_generator.py` (3 tests across all 3 synthetic scenarios)
  - `test_investigations_api.py` (6 tests)
  - `test_pipeline_e2e.py` (3 end-to-end scenario tests)
- Authored live smoke test script: `backend/scripts/smoke_test_pipeline.py`.

## Core Product Distinction Re-affirmed
RazorPulse is **NOT a fraud decision engine**.
It is an **external-context corroboration engine**.
Its score represents the strength of public external evidence explaining an observed transaction anomaly. It never makes autonomous financial decisions or overrides Razorpay risk systems.
