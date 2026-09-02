# RazorPulse — AI Handoff Document

> **Purpose:** Provide another AI coding agent with enough context to continue development without guessing.

## Project Identity

| Field | Value |
|-------|-------|
| **Project** | RazorPulse |
| **Track** | AI Risk Manager (Razorpay AI Buildathon 2026) |
| **Product** | External-context verification copilot for anomalous payment-risk events |
| **Core Metric** | Event Corroboration Index (ECI) |

## What RazorPulse Does

When a merchant experiences an anomalous transaction pattern (e.g., 17x velocity spike), RazorPulse:

1. **Ingests** the risk anomaly
2. **Discovers** external events via Exa AI (news, press, social media)
3. **Verifies** evidence via Google Gemini (entity match, temporal relevance, credibility)
4. **Scores** corroboration deterministically (ECI — transparent, auditable)
5. **Presents** an evidence dossier to a human risk analyst

**RazorPulse does NOT:** unfreeze accounts, release funds, approve transactions, modify Razorpay risk decisions, or make autonomous financial decisions. It is READ-ONLY decision support.

## Current Architecture

```
Razorpay / simulated risk event
    → FastAPI backend (Python)
    → Supabase (PostgreSQL)
    → Exa AI (external event discovery)
    → Gemini (evidence verification)
    → Deterministic ECI scoring engine
    → Risk Analyst Dashboard (Next.js — not yet built)
```

## Current Development Phase

**Day 1 — COMPLETE**

## What Has Been Built

### Backend (`backend/app/`)
- **Entry point:** `main.py` — FastAPI app with CORS, exception handlers, lifespan
- **Configuration:** `config/settings.py` — Pydantic-settings with credential validation
- **Exceptions:** `core/exceptions.py` — Typed exception hierarchy
- **Logging:** `core/logging.py` — Structured logging with loguru
- **Schemas:** `schemas/risk_event.py`, `schemas/merchant.py`, `schemas/common.py`
- **Repositories:** `repositories/supabase_client.py`, `repositories/risk_event_repository.py`, `repositories/merchant_repository.py`
- **Services:** `services/risk_event_service.py`, `services/exa/client.py`, `services/gemini/client.py`
- **Routes:** `api/routes/health.py`, `api/routes/risk_events.py`, `api/routes/integrations.py`

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/risk-events` | Ingest risk event |
| GET | `/api/v1/risk-events/{id}` | Get risk event by ID |
| GET | `/api/v1/risk-events` | List risk events |
| GET | `/api/v1/integrations/exa/health` | Exa connectivity check |
| GET | `/api/v1/integrations/gemini/health` | Gemini connectivity check |
| GET | `/api/v1/integrations/status` | All integrations status |

### Database (`database/schemas/001_initial_schema.sql`)
- `merchants` — Merchant identity (name, domain)
- `risk_events` — Anomalous payment events with quantitative signals
- `investigations` — Investigation lifecycle tracking
- Row Level Security: service_role only

### Tests (37 tests, all passing)
- Unit: config loading, schema validation
- Integration: health endpoint, risk event CRUD (mocked Supabase)
- Fixtures: 3 synthetic risk events

### External Integrations
- **Exa:** Client wrapper created, health check endpoint available
- **Gemini:** Client wrapper created (gemini-2.5-flash), structured output tested
- **Supabase:** Client initialization, CRUD operations implemented
- **Razorpay:** No direct integration (simulated events). Test Mode credentials available.

## What Has NOT Been Built

- [ ] Exa search strategy optimization
- [ ] Gemini evidence verification prompts (full pipeline)
- [ ] Investigation orchestration (Exa → Gemini flow)
- [ ] Deterministic ECI scoring engine
- [ ] Evidence dossier generation
- [ ] Frontend dashboard
- [ ] Authentication / RBAC
- [ ] Evaluation benchmark dataset
- [ ] Precision/recall measurement
- [ ] Production deployment
- [ ] Razorpay webhook integration (no confirmed public risk webhook)

## Important Architectural Decisions

1. **Supabase Python client** (not SQLAlchemy ORM) — simpler, Supabase-native
2. **gemini-2.5-flash** model — cost-effective prototype, supports structured output
3. **Simulated risk events** — no public Razorpay risk webhook confirmed
4. **Three-table design** — merchants, risk_events, investigations
5. **Service layer pattern** — routes → services → repositories
6. **Strict AI boundary** — Exa discovers, Gemini interprets, Python scores, human decides

## DO NOT CHANGE WITHOUT HUMAN APPROVAL

- Technology stack (FastAPI, Supabase, Exa, Gemini, Next.js)
- Human-in-the-loop principle (NO autonomous financial actions)
- ECI scoring must remain deterministic (no LLM-decided scores)
- Source distinction (simulated vs real data must be honest)

## Known Risks

1. Exa search quality for Indian merchants is untested
2. Gemini verification prompt not yet designed (Day 2)
3. ECI scoring weights not yet calibrated
4. No benchmark dataset for precision/recall evaluation
5. Supabase RLS policies need testing with real credentials

## Next Task (Day 2)

1. Design and implement the Exa search strategy for merchant anomalies
2. Design Gemini evidence verification prompt with structured output
3. Build investigation orchestration service (Exa → Gemini → results)
4. Implement deterministic ECI scoring engine with initial weights
5. Create evidence dossier data model and generation
6. Begin evaluation dataset design

## Human Intervention Required

1. **Set API keys** in `backend/.env` — Supabase URL/keys, Exa API key, Gemini API key
2. **Run SQL schema** — Copy `database/schemas/001_initial_schema.sql` into Supabase SQL Editor and execute
3. **Run smoke tests** — `cd backend && python scripts/smoke_test_exa.py` and `python scripts/smoke_test_gemini.py`
4. **Verify Supabase** — Confirm tables created, RLS policies active
