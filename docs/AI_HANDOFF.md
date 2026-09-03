# RazorPulse — AI Handoff Document

> **Purpose:** Provide any future AI coding agent or engineer with complete, unambiguous context to continue development without guessing.

## Project Identity

| Field | Value |
|-------|-------|
| **Project** | RazorPulse |
| **Track** | AI Risk Manager (Razorpay AI Buildathon 2026) |
| **Product** | External-context verification copilot for anomalous payment-risk events |
| **Core Metric** | Event Corroboration Index (ECI v1 heuristic) |

## Strategic Product Boundary
- **RazorPulse is NOT a fraud decision engine.**
- It is an **external-context corroboration engine**.
- Its output answers: *"How strongly does available external evidence corroborate a real-world contextual explanation for this transaction anomaly?"*
- Its output does NOT answer: *"How risky is this merchant?"*
- RazorPulse NEVER: automatically unfreezes accounts, releases funds, approves merchants, rejects merchants, changes payment limits, or overrides Razorpay risk decisions.

## Current Architecture

```
Risk Anomaly (simulated/internal)
    │
    ▼
FastAPI Backend (POST /api/v1/investigations)
    │
    ▼
Investigation Orchestrator (app/services/investigation/)
    │
    ▼
Exa AI Search Strategy (Bounded multi-intent queries: Timeframe, Announcement, Campaign, Anomaly)
    │
    ▼
Normalized & Deduplicated Evidence (app/schemas/evidence.py)
    │
    ▼
Google Gemini Verifier (Anti-hallucination structured prompt, Pydantic response schema)
    │
    ▼
Deterministic ECI v1 Engine (Pure Python rules, 0..100 bounded score, explainable factors)
    │
    ▼
Evidence Dossier (Executive summary, citations [E1], gaps, analyst checklist)
    │
    ▼
Supabase Persistence (investigations table with migration 002)
    │
Human Risk Analyst API (GET /api/v1/investigations/{id})
```

## Current Development Phase

**Day 3 — COMPLETE**

## What Has Been Built (Day 1 + Day 2 + Day 3)

### Backend (`backend/app/`)
- **API Routes:**
  - `GET /health` — Health check
  - `POST /api/v1/risk-events` — Ingest simulated risk anomaly
  - `GET /api/v1/risk-events/{id}` — Get risk event by ID
  - `GET /api/v1/risk-events` — List risk events
  - `POST /api/v1/investigations` — Trigger synchronous investigation for `risk_event_id`
  - `GET /api/v1/investigations/{id}` — Get investigation details with complete Evidence Dossier and PipelineMetadata
  - `GET /api/v1/investigations` — List investigations with status/risk_event filtering
  - `GET /api/v1/integrations/status` — Status of configured credentials
  - `GET /api/v1/integrations/exa/health` — Exa live connectivity check
  - `GET /api/v1/integrations/gemini/health` — Gemini live connectivity check
- **Services:**
  - `services/evidence_quality.py` — Quality gates (URL check, domain check, content check, near-duplicate claim cluster grouping `evidence_group_id`, advisory entity relevance signal)
  - `services/exa/` — Client wrapper, QueryIntentBuilder, normalizer with URL deduplication, ExaSearchStrategy
  - `services/gemini/` — Client wrapper (`gemini-3.5-flash-lite`), batch verification prompt (`VERIFICATION_PROMPT_VERSION = "v1"`), GeminiVerifier with deterministic selection (`GEMINI_MAX_EVIDENCE_ITEMS=4`), `with_gemini_retry` with server retry delay and fast-fail
  - `services/scoring/` — Deterministic ECIEngine (v1 heuristic, scoring strictly VERIFIED items)
  - `services/investigation/` — DossierGenerator (citations only for verified items, checklist referencing citation IDs), InvestigationOrchestrator (stage timings, quality auditing, pipeline metadata persistence)
  - `services/risk_event_service.py` — Risk event ingestion logic
- **Repositories:**
  - `repositories/merchant_repository.py` — Merchant find-or-create by domain
  - `repositories/risk_event_repository.py` — Risk event CRUD
  - `repositories/investigation_repository.py` — Investigation CRUD and structured persistence
- **Schemas:**
  - `schemas/evidence.py` — SourceType, NormalizedEvidence, canonicalize_url
  - `schemas/pipeline_metadata.py` — PipelineMetadata (versions, prompt version, stage timings, counts)
  - `schemas/verification.py` — VerificationStatus (VERIFIED, FAILED, SKIPPED), Match levels, EvidenceVerificationItem, BatchEvidenceVerificationResponse, VerificationResult
  - `schemas/eci.py` — ECIBand, ECIFactorCategory, ECIFactorContribution, ECIScoreResult
  - `schemas/dossier.py` — AnomalySummary, EvidenceCitation, EvidenceDossier (with pipeline_metadata)
  - `schemas/investigation.py` — InvestigationStatus, InvestigationCreate, InvestigationResponse, InvestigationDetailResponse (with pipeline_metadata)

### Evaluation Framework (`backend/evaluation/`)
- `evaluation/ground_truth.py` — Independent CorroborationClass and ContradictionState ground truth data model; documented ECI classification policy
- `evaluation/dataset.py` — 25 labeled synthetic benchmark cases spanning all 12 archetypes (A through L), partitioned into 18 dev / 7 held-out cases
- `evaluation/metrics.py` — 4-class corroboration metrics (accuracy, macro P/R/F1, confusion matrix) and binary contradiction metrics with instability flags
- `evaluation/runner.py` — Canonical offline fixture-only benchmark runner with score separation analysis and failure mode reporting
- `evaluation/calibration.py` — Calibration analysis verifying strictly monotonic mean ECI and cataloging 4 structural failure modes
- `evaluation/demo_scenarios.py` — 3 deterministic demo scenarios (Festive Surge, Zero Evidence, Disputed Claim) without artificial score tuning

### Tests (128 automated tests, 100% passing)
- 13 Config unit tests
- 14 Schema validation unit tests
- 4 Health endpoint integration tests
- 7 Risk event endpoint integration tests
- 5 Query generation unit tests
- 6 Evidence normalization & deduplication unit tests
- 5 Gemini verifier unit tests
- 18 Gemini retry, delay, and quota handling unit tests
- 12 ECI Engine unit tests validating all 10 Score Invariants + partial/unverified cases
- 6 ECI Directional Invariant & Monotonicity tests (`test_eci_monotonicity.py`)
- 6 Evaluation dataset structure and coverage tests (`test_evaluation_dataset.py`)
- 7 Statistical metrics & confusion matrix tests (`test_evaluation_metrics.py`)
- 5 Evidence quality gate & syndication grouping tests (`test_evidence_quality.py`)
- 2 Pipeline metadata schema & timing tests (`test_pipeline_metadata.py`)
- 4 Demo scenarios execution tests (`test_demo_scenarios.py`)
- 4 Dossier generator unit tests
- 6 Investigation API endpoint integration tests
- 4 Full end-to-end pipeline execution tests

### Live & Demo Scripts
- `backend/scripts/run_demo.py` — Purely deterministic demonstration runner (no API keys or network required)
- `backend/scripts/smoke_test_exa.py` — Exa live connectivity test
- `backend/scripts/smoke_test_gemini.py` — Gemini live structured output test
- `backend/scripts/smoke_test_pipeline.py` — Complete end-to-end live pipeline test (Exa discovery + batch Gemini verification)

## Next Task (Day 4)

1. Model calibration and search query tuning based on Day 3 failure modes (entity gating, causal directionality, credibility ceilings).
2. Frontend analyst dashboard integration (React / Vite web application for investigating anomalies, reviewing ECI breakdown, and inspecting citations).
3. API contracts finalization for dashboard visualization.
