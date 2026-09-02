# RazorPulse — Project Status

**Last updated:** 2026-09-02 (Day 2)

## Current Phase

**Day 2 — Investigation Pipeline + Evidence Verification + Deterministic ECI v1 Engine ✅**

## Completed Work

### Phase 0: Repository Initialization ✅
- Directory structure established
- Git repository initialized
- `.gitignore` configured
- README with architecture overview
- License file

### Day 1: Backend Foundation ✅
- FastAPI application with health endpoint
- Pydantic-settings configuration management
- Custom exception hierarchy
- Structured logging (loguru)
- Risk event domain model (Pydantic schemas)
- Risk event ingestion API (`POST /api/v1/risk-events`)
- Supabase client initialization
- Merchant and risk event repositories
- Exa AI client wrapper & Gemini client wrapper
- Initial SQL DDL schema (001_initial_schema.sql)
- 37 automated tests passing

### Day 2: Investigation Pipeline & Deterministic ECI Engine ✅
- **Investigation Domain & Lifecycle**: Strongly typed models for evidence, verification, ECI factors, dossier, and status (`PENDING` -> `SEARCHING` -> `VERIFYING` -> `SCORING` -> `COMPLETED` / `FAILED`).
- **Database Migration 002**: Authored `002_investigations_schema.sql` adding structured ECI and dossier columns.
- **Exa Search Strategy & Query Intent Builder**: Bounded multi-intent query generation (`TIMEFRAME_EVENT`, `MERCHANT_ANNOUNCEMENT`, `COMMERCIAL_CAMPAIGN`, `ANOMALY_CONTEXT`, `IDENTITY_CONTEXT`), evidence normalization, and URL canonicalization.
- **Gemini Structured Evidence Verification**: Anti-hallucination prompt enforcing strict grounding in provided text snippets, evaluating match levels, explanation support, evidence strength, credibility, contradictions, and uncertainties.
- **Deterministic ECI v1 Heuristic Engine**: Orthogonal factor calculations (Entity match, Temporal alignment, Explanation support, Source credibility, Independent domain bonus) with contradiction and uncertainty penalties, bounded strictly to `[0, 100]`.
- **Evidence Dossier Generator**: Comprehensive analyst report with executive summary, citations (`[E1]`, `[E2]`), contradictions, evidence gaps, uncertainties, and review checklist (neutral non-fraud language).
- **Orchestration & Persistence**: End-to-end investigation service coordinating discovery, verification, scoring, dossier synthesis, and Supabase persistence.
- **Investigation API**: `POST /api/v1/investigations` (synchronous execution), `GET /api/v1/investigations/{id}` (full dossier), `GET /api/v1/investigations` (paginated list).
- **Synthetic Evaluation Scenarios**: 3 realistic scenarios (Strong Viral Launch, Zero Evidence, Contradicted Event).
- **Test Suite**: 73 automated unit and integration tests (100% passing) verifying all 10 ECI Score Invariants, API routes, normalizers, and end-to-end pipeline execution.
- **Live Smoke Test Script**: `backend/scripts/smoke_test_pipeline.py`.

## Work Remaining

### Day 3 (Next)
- Evaluation dataset & benchmark suite (measuring precision and recall on held-out test scenarios)
- Investigation comparison and search tuning
- Refinements for multi-merchant and high-volume anomaly workflows
- Preparation for analyst frontend integration

### Future Phases
- Risk Analyst Dashboard (Next.js)
- Adversarial robustness testing
- Production deployment polish

## Decisions Made

| Decision | Status |
|----------|--------|
| FastAPI for backend | ✅ Confirmed |
| Supabase/PostgreSQL for database | ✅ Confirmed |
| Exa AI for external event discovery | ✅ Implemented |
| Google Gemini for evidence verification (`gemini-2.5-flash`) | ✅ Implemented |
| Deterministic Python ECI v1 heuristic scoring engine | ✅ Implemented |
| Synchronous MVP investigation execution model | ✅ Implemented |
| Neutral corroboration terminology (no "red flags" / fraud claims) | ✅ Implemented |
| Simulated risk events (no fake Razorpay risk webhooks) | ✅ Implemented |

## Technologies Selected
- **Backend:** Python 3.14, FastAPI, Pydantic v2
- **Database:** Supabase (PostgreSQL)
- **External Search:** Exa AI (`exa-py`)
- **Evidence Verification:** Google Gemini (`google-genai`, `gemini-2.5-flash`)
- **Scoring:** Deterministic Python rule engine (ECI v1)
- **Testing:** pytest (73 tests passing)
