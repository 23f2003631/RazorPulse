# RazorPulse — Day 1 Development Log

## Objective

Establish the backend foundation, data model, risk event ingestion pipeline, and external AI service connectivity for RazorPulse. This is the first implementation phase after repository initialization.

## Starting State

- Repository initialized with directory structure (Phase 0)
- All Python files were placeholder stubs with no application logic
- No git commits existed
- No database schema, no tests, no working endpoints
- Supabase project created by human developer (credentials available)
- `.env` file with placeholder values (not committed)

## Completed

### Backend Foundation
- ✅ FastAPI application with lifespan management
- ✅ Pydantic-settings configuration with typed environment variables
- ✅ Custom exception hierarchy (ConfigurationError, DatabaseError, ExternalServiceError, etc.)
- ✅ Structured logging with loguru (secret filtering)
- ✅ CORS middleware
- ✅ Global exception handlers
- ✅ Backend `.env.example` template

### Risk Event Domain Model
- ✅ `RiskEventCreate` schema with full validation
- ✅ `RiskEventResponse` schema
- ✅ `AnomalyType` enum (6 types)
- ✅ `RiskEventStatus` enum (5 statuses)
- ✅ `EventSource` enum (simulated, razorpay_webhook, razorpay_api, manual)
- ✅ `MerchantBase`, `MerchantCreate`, `MerchantResponse` schemas
- ✅ Percentage change computation
- ✅ Currency normalization (uppercase)
- ✅ Input validation with boundary checks

### Risk Event Ingestion
- ✅ `POST /api/v1/risk-events` — ingest simulated risk events
- ✅ `GET /api/v1/risk-events/{id}` — retrieve by ID
- ✅ `GET /api/v1/risk-events` — list with pagination and status filter
- ✅ Service layer: validate → find/create merchant → compute fields → persist → return
- ✅ Supabase client singleton with service_role key
- ✅ Merchant repository with find-or-create by domain
- ✅ Risk event repository with CRUD operations

### External Integrations
- ✅ Exa AI client wrapper (`services/exa/client.py`)
- ✅ Exa search method with merchant name, domain, and date filtering
- ✅ Gemini client wrapper (`services/gemini/client.py`)
- ✅ Gemini structured output verification
- ✅ Integration health check endpoints
- ✅ Integration status endpoint (credential configuration check)

### Database
- ✅ SQL DDL file for Supabase (`database/schemas/001_initial_schema.sql`)
- ✅ Row Level Security policies (service_role only)

### Testing
- ✅ 37 automated tests — all passing
- ✅ Smoke test scripts for Exa and Gemini (live API verification)

## Not Completed (Intentionally Deferred)

- ❌ Exa search strategy optimization (Day 2)
- ❌ Gemini evidence verification prompt design (Day 2)
- ❌ Investigation orchestration pipeline (Day 2)
- ❌ ECI deterministic scoring engine (Day 2+)
- ❌ Evidence dossier generation (Day 2+)
- ❌ Frontend dashboard (separate phase)
- ❌ Authentication / RBAC
- ❌ Razorpay webhook integration
- ❌ Evaluation benchmark dataset
- ❌ Precision/recall measurement
- ❌ Production deployment

## Database

### Tables Created
1. **merchants** — Merchant identity (name, domain)
2. **risk_events** — Anomalous payment events with quantitative signals
3. **investigations** — Investigation lifecycle tracking

### Schema Rationale
- Merchants separated for domain-based deduplication across events
- Risk events capture anomaly data (not individual transactions)
- Source field distinguishes simulated vs real data
- Investigations separated to allow re-investigation
- UUIDs for all primary keys
- TIMESTAMPTZ for all timestamps
- RLS restricts access to service_role only

## Backend

### Endpoints Implemented
| Method | Path | Status |
|--------|------|--------|
| GET | `/health` | ✅ Working |
| POST | `/api/v1/risk-events` | ✅ Working (mocked DB tests pass) |
| GET | `/api/v1/risk-events/{id}` | ✅ Working (mocked DB tests pass) |
| GET | `/api/v1/risk-events` | ✅ Working (mocked DB tests pass) |
| GET | `/api/v1/integrations/exa/health` | ✅ Working (requires API key) |
| GET | `/api/v1/integrations/gemini/health` | ✅ Working (requires API key) |
| GET | `/api/v1/integrations/status` | ✅ Working |

## External Integrations

### Exa
- **Status:** Client created, health check endpoint available
- **Connectivity:** NOT YET VERIFIED (requires valid EXA_API_KEY)
- **Smoke test:** `backend/scripts/smoke_test_exa.py`

### Gemini
- **Status:** Client created with gemini-2.5-flash model
- **Connectivity:** NOT YET VERIFIED (requires valid GEMINI_API_KEY)
- **Smoke test:** `backend/scripts/smoke_test_gemini.py`
- **Model:** gemini-2.5-flash (selected for cost, latency, structured output)

### Razorpay
- **Status:** SIMULATED only
- **Real integration:** No public risk webhook confirmed
- **Test Mode:** Credentials available but not yet verified
- **Note:** EventSource enum tracks data provenance honestly

## Tests

| Test File | Tests | Result |
|-----------|-------|--------|
| tests/unit/test_config.py | 12 | ✅ All passed |
| tests/unit/test_schemas.py | 14 | ✅ All passed |
| tests/integration/test_health.py | 4 | ✅ All passed |
| tests/integration/test_risk_events.py | 7 | ✅ All passed |
| **Total** | **37** | **✅ All passed** |

## Known Issues

1. Supabase tables not yet created (SQL provided, needs manual execution)
2. Exa/Gemini connectivity not verified with real API keys
3. `pytest-asyncio` deprecation warning (non-blocking)

## Human Actions Required

1. **Enter API keys** in `backend/.env`:
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
   - `EXA_API_KEY`
   - `GEMINI_API_KEY`
   - `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`
2. **Run SQL schema** in Supabase Dashboard:
   - Navigate to SQL Editor
   - Paste contents of `database/schemas/001_initial_schema.sql`
   - Execute
3. **Run smoke tests**:
   - `cd backend && .\venv\Scripts\python.exe scripts/smoke_test_exa.py`
   - `cd backend && .\venv\Scripts\python.exe scripts/smoke_test_gemini.py`
4. **Test live ingestion**:
   - Start server: `cd backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --reload`
   - POST a synthetic risk event to `/api/v1/risk-events`

## Next Step (Day 2)

1. Design Exa search strategy for merchant anomaly investigation
2. Design Gemini evidence verification prompt (structured output)
3. Build investigation orchestration service
4. Implement deterministic ECI scoring engine
5. Create evidence dossier data model
6. Begin evaluation dataset design
