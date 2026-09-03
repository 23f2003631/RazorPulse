# RazorPulse — Project Status

**Last updated:** 2026-09-03 (Day 4)

## Current Phase

**Day 4 — Evidence Quality, Corroboration Reliability & Benchmark Hardening ✅**

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
- **Deterministic ECI v1 Heuristic Engine**: Orthogonal factor calculations with contradiction and uncertainty penalties, bounded strictly to `[0, 100]`.
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

### Day 4: Evidence Quality, Corroboration Reliability & Benchmark Hardening ✅
- **ECI v1.1 Scoring Engine**: Replaced global "best" factor selection with per-item eligibility assessment.
- **Entity Mismatch Gating**: Unrelated merchant evidence is excluded from positive contribution with an explicit audit record (`exclusion_reason = "entity_mismatch"`).
- **Temporal Causality Gating**: Post-anomaly and unrelated timing items cannot provide causal explanation support.
- **Source Authority Ceiling**: Low-credibility social rumors and weak circumstantial claims are capped at 29 ECI points, preventing unverified claims from inflating into Strong corroboration.
- **Claim-Group Independence**: Connects near-duplicate text fingerprinting (`evidence_group_id`) to the independent corroboration bonus, preventing syndicated copies from inflating multi-source bonuses.
- **Audit Schemas**: Added `ECIExcludedItem` and `eligible_evidence_count` to ECI output schemas.
- **Benchmark Improvement**:
  - Full benchmark: 32% (8/25) -> **60% (15/25)**, Macro F1: 0.2667 -> **0.5015**
  - Held-out partition: 42.86% (3/7) -> **57.14% (4/7)**, Macro F1: 0.3000 -> **0.4000**
  - Development partition: 27.78% (5/18) -> **61.11% (11/18)**, Macro F1: 0.2409 -> **0.5025**
  - Contradiction detection: **1.0000 F1** (100% precision & recall preserved)
  - Zero regressions across all 25 benchmark cases (7 fixed, 8 unchanged correct, 0 regressed).
- **148 Automated Tests**: 100% passing across isolated gating tests, mixed-evidence scenarios, and existing test suites.

## Work Remaining

### Day 5 (Next)
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
| Deterministic Python ECI v1.1 heuristic scoring engine | ✅ Implemented |
| Independent Corroboration and Contradiction evaluation dimensions | ✅ Implemented |
| Non-destructive evidence quality annotation (no silent deletion) | ✅ Implemented |
| Per-item eligibility assessment (no global aggregation shortcuts) | ✅ Implemented |
| Synchronous MVP investigation execution model | ✅ Implemented |
| Neutral corroboration terminology (no "red flags" / fraud claims) | ✅ Implemented |
| Simulated risk events (no fake Razorpay risk webhooks) | ✅ Implemented |

## Technologies Selected
- **Backend:** Python 3.14, FastAPI, Pydantic v2
- **Database:** Supabase (PostgreSQL)
- **External Search:** Exa AI (`exa-py`)
- **Evidence Verification:** Google Gemini (`google-genai`, `gemini-3.5-flash-lite`)
- **Scoring:** Deterministic Python rule engine (ECI v1.1)
- **Evaluation:** Canonical offline fixture benchmark (25 cases, 18 dev / 7 held-out)
- **Testing:** pytest (148 tests passing, 100%)
