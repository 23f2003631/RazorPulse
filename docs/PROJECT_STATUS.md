# RazorPulse — Project Status

**Last updated:** 2026-09-03 (Day 3)

## Current Phase

**Day 3 — Evaluation Dataset + Benchmark Suite + Pipeline Hardening ✅**

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
- **Test Suite**: 98 automated tests.

### Day 3: Evaluation Dataset, Benchmark Suite, & Robustness ✅
- **Evaluation Ground Truth Model**: Independent corroboration classification (4-class) and binary contradiction detection data model.
- **25-Case Synthetic Evaluation Dataset**: 25 labeled cases covering all 12 scenario archetypes (A–L), split into 18 development and 7 held-out cases.
- **Canonical Offline Benchmark Runner**: Reproducible fixture-only benchmark measuring Accuracy, Macro P/R/F1, Confusion Matrix, and Contradiction F1.
- **ECI Calibration & Separation Analysis**: Proved strictly monotonic mean ECI ($23.6 < 51.4 < 85.7 < 96.0$) and cataloged 4 systemic failure modes in additive scoring.
- **Evidence Quality Gates**: Non-destructive annotation service for URL validation, source domain verification, content availability, and claim syndication clustering (`evidence_group_id`).
- **Reproducibility Metadata**: Structured `PipelineMetadata` capturing pipeline version ("0.3.0"), prompt version ("v1"), stage timings, and counts persisted inside Supabase.
- **Analyst Checklist Provenance**: Enhanced dossier checklist referencing specific citation markers (e.g. `[E1] (economictimes.indiatimes.com)`).
- **Deterministic Demo Scenarios**: `scripts/run_demo.py` showcasing 3 realistic scenarios without artificial score tuning.
- **Directional Invariant Tests**: Formal monotonicity tests verifying directional integrity across all scoring dimensions.
- **128 Automated Tests**: 100% passing across the entire test suite.

## Work Remaining

### Day 4 (Next)
- Model calibration and search query tuning based on Day 3 failure modes (entity gating, causal directionality, credibility ceilings)
- Risk Analyst Dashboard (React / Vite)
- API contract finalization for frontend visualization
- End-to-end visual walkthrough and demonstration

### Future Phases
- High-volume batch ingestion workflows
- Production deployment polish

## Decisions Made

| Decision | Status |
|----------|--------|
| FastAPI for backend | ✅ Confirmed |
| Supabase/PostgreSQL for database | ✅ Confirmed |
| Exa AI for external event discovery | ✅ Implemented |
| Google Gemini for evidence verification (`gemini-3.5-flash-lite`) | ✅ Implemented |
| Deterministic Python ECI v1 heuristic scoring engine | ✅ Implemented |
| Independent Corroboration and Contradiction evaluation dimensions | ✅ Implemented |
| Non-destructive evidence quality annotation (no silent deletion) | ✅ Implemented |
| Synchronous MVP investigation execution model | ✅ Implemented |
| Neutral corroboration terminology (no "red flags" / fraud claims) | ✅ Implemented |
| Simulated risk events (no fake Razorpay risk webhooks) | ✅ Implemented |

## Technologies Selected
- **Backend:** Python 3.14, FastAPI, Pydantic v2
- **Database:** Supabase (PostgreSQL)
- **External Search:** Exa AI (`exa-py`)
- **Evidence Verification:** Google Gemini (`google-genai`, `gemini-3.5-flash-lite`)
- **Scoring:** Deterministic Python rule engine (ECI v1)
- **Evaluation:** Canonical offline fixture benchmark (25 cases, 18 dev / 7 held-out)
- **Testing:** pytest (128 tests passing, 100%)
