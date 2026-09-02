# RazorPulse — Project Status

**Last updated:** 2026-09-02 (Day 1)

## Current Phase

**Day 1 — Backend Foundation + Data Model + Risk Event Ingestion + External AI Connectivity**

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
- Risk event retrieval API (`GET /api/v1/risk-events/{id}`)
- Risk event listing API (`GET /api/v1/risk-events`)
- Supabase client initialization
- Merchant repository (find-or-create by domain)
- Risk event repository (CRUD)
- Exa AI client wrapper with search capability
- Gemini client wrapper with structured output support
- Integration health check endpoints
- SQL schema for Supabase (merchants, risk_events, investigations)
- 3 synthetic risk event fixtures
- 37 automated tests (all passing)
- Smoke test scripts for Exa and Gemini

## Work Remaining

### Day 2 (Next)
- Full Exa search strategy for merchant anomalies
- Gemini evidence verification prompts
- Investigation pipeline (Exa → Gemini → ECI)
- ECI scoring engine (deterministic)
- Evidence dossier generation

### Future Phases
- Complete investigation orchestration
- Frontend dashboard (Next.js)
- Evaluation benchmark (precision/recall on held-out test set)
- Adversarial testing
- Production polish and deployment

## Known Limitations
- Supabase tables must be created manually (SQL provided)
- Exa/Gemini connectivity requires valid API keys (not yet verified live)
- No authentication on API endpoints
- Risk events are SIMULATED, not from real Razorpay webhooks
- No Razorpay webhook integration (no confirmed public risk webhook)

## Decisions Made

| Decision | Status |
|----------|--------|
| FastAPI for backend | ✅ Confirmed |
| Supabase/PostgreSQL for database | ✅ Confirmed |
| Supabase Python client (not SQLAlchemy ORM) | ✅ Implemented |
| Exa AI for external event discovery | ✅ Client created |
| Google Gemini for evidence verification | ✅ Client created |
| gemini-2.5-flash model | ✅ Selected |
| Deterministic Python rules for ECI scoring | 🔲 Not yet implemented |
| Next.js/TypeScript/React/Tailwind for frontend | 🔲 Not yet started |
| Simulated risk events (not real Razorpay webhooks) | ✅ Implemented |

## Technologies Selected

- **Backend:** Python, FastAPI, Pydantic
- **Database:** Supabase (PostgreSQL)
- **External Search:** Exa AI (`exa-py`)
- **Evidence Verification:** Google Gemini (`google-genai`)
- **Scoring:** Deterministic Python rules (not yet implemented)
- **Frontend:** Next.js, TypeScript, React, Tailwind CSS (not yet started)
- **Testing:** pytest

## Human Intervention Required

1. **Set API keys** in `.env` file (Supabase, Exa, Gemini, Razorpay)
2. **Run SQL schema** in Supabase Dashboard SQL Editor
3. **Run smoke tests** to verify Exa/Gemini connectivity
4. **Verify Supabase project** settings and RLS policies
