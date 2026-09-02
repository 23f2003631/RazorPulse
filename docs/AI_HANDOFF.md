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
    ▼
Human Risk Analyst API (GET /api/v1/investigations/{id})
```

## Current Development Phase

**Day 2 — COMPLETE**

## What Has Been Built (Day 1 + Day 2)

### Backend (`backend/app/`)
- **API Routes:**
  - `GET /health` — Health check
  - `POST /api/v1/risk-events` — Ingest simulated risk anomaly
  - `GET /api/v1/risk-events/{id}` — Get risk event by ID
  - `GET /api/v1/risk-events` — List risk events
  - `POST /api/v1/investigations` — Trigger synchronous investigation for `risk_event_id`
  - `GET /api/v1/investigations/{id}` — Get investigation details with complete Evidence Dossier
  - `GET /api/v1/investigations` — List investigations with status/risk_event filtering
  - `GET /api/v1/integrations/status` — Status of configured credentials
  - `GET /api/v1/integrations/exa/health` — Exa live connectivity check
  - `GET /api/v1/integrations/gemini/health` — Gemini live connectivity check
- **Services:**
  - `services/exa/` — Client wrapper, QueryIntentBuilder, normalizer with URL deduplication, ExaSearchStrategy
  - `services/gemini/` — Client wrapper (`gemini-2.5-flash`), anti-hallucination verification prompt, GeminiVerifier with Pydantic structured output
  - `services/scoring/` — Deterministic ECIEngine (v1 heuristic)
  - `services/investigation/` — DossierGenerator, InvestigationOrchestrator
  - `services/risk_event_service.py` — Risk event ingestion logic
- **Repositories:**
  - `repositories/merchant_repository.py` — Merchant find-or-create by domain
  - `repositories/risk_event_repository.py` — Risk event CRUD
  - `repositories/investigation_repository.py` — Investigation CRUD and structured persistence
- **Schemas:**
  - `schemas/evidence.py` — SourceType, NormalizedEvidence, canonicalize_url
  - `schemas/verification.py` — Match levels, EvidenceVerificationItem, VerificationResult
  - `schemas/eci.py` — ECIBand, ECIFactorCategory, ECIFactorContribution, ECIScoreResult
  - `schemas/dossier.py` — AnomalySummary, EvidenceCitation, EvidenceDossier
  - `schemas/investigation.py` — InvestigationStatus, InvestigationCreate, InvestigationResponse, InvestigationDetailResponse
- **Database:**
  - `001_initial_schema.sql` — Initial tables: merchants, risk_events, investigations + RLS
  - `002_investigations_schema.sql` — Migration adding structured ECI, dossier, and evidence columns

### Tests (73 automated tests, all passing)
- 12 Config unit tests
- 14 Schema validation unit tests
- 4 Health endpoint integration tests
- 7 Risk event endpoint integration tests
- 5 Query generation unit tests
- 6 Evidence normalization & deduplication unit tests
- 3 Gemini verifier unit tests
- 10 ECI Engine unit tests validating all 10 Score Invariants
- 3 Dossier generator unit tests
- 6 Investigation API endpoint integration tests
- 3 Full end-to-end pipeline execution tests

### Live Scripts
- `backend/scripts/smoke_test_exa.py` — Exa live test
- `backend/scripts/smoke_test_gemini.py` — Gemini live test
- `backend/scripts/smoke_test_pipeline.py` — Complete end-to-end live pipeline test

## Next Task (Day 3)

1. Design evaluation dataset & benchmark suite (labeled synthetic scenarios representing various loss classes, viral surges, zero evidence, and contradicted events).
2. Measure precision, recall, and corroboration accuracy on held-out evaluation scenarios.
3. Conduct search query tuning and parameter calibration.
4. Prepare API contracts for frontend dashboard integration.
