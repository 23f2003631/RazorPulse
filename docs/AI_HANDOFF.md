# RazorPulse — AI Handoff Document

> **Purpose:** Provide any future AI coding agent or engineer with complete, unambiguous context to continue development, evaluation, or demonstration without guessing.

---

## Project Identity & Mission

| Field | Value |
|---|---|
| **Project** | RazorPulse |
| **Track** | AI Risk Manager (Razorpay AI Buildathon 2026) |
| **Product** | External Evidence Corroboration Engine for anomalous payment-risk events |
| **Core Metric** | Event Corroboration Index (ECI v1.1 heuristic engine) |
| **Status** | **Day 5 Complete** — Production-Grade Analyst Console, Offline-Ready Deterministic Demo Mode, 154 Tests (100% passing), 25-Case Benchmark Validated |

---

## Strategic Product Boundary

- **RazorPulse is NOT a fraud decision engine.**
- It is an **external evidence corroboration engine**.
- Its output answers: *"How strongly does available external evidence corroborate a real-world contextual explanation for this transaction anomaly?"*
- Its output does NOT answer: *"How risky is this merchant?"* or *"What is the probability of fraud?"*
- RazorPulse NEVER:
  - Automatically unfreezes accounts or holds funds.
  - Automatically releases funds or initiates payouts.
  - Automatically approves or declines merchants.
  - Overrides human risk analyst authority.
- The human risk analyst retains final authority. RazorPulse equips analysts with a verifiable evidence dossier, auditable exclusion logs, canonical citations, and an interactive review checklist.

---

## System Architecture

```
Risk Anomaly (simulated/internal ingestion)
    │
    ▼
FastAPI Backend (POST /api/v1/risk-events)
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
Evidence Quality Gates (URL check, domain check, content check, claim syndication clustering)
    │
    ▼
Google Gemini Verifier (Anti-hallucination structured prompt, Pydantic response schema)
    │
    ▼
Deterministic ECI v1.1 Engine (Per-item eligibility, entity gate, temporal causality, authority ceiling, claim groups)
    │
    ▼
Evidence Dossier (Executive summary, citations [E1], contradictions, gaps, analyst checklist, audit of excluded items)
    │
    ▼
Supabase / SQLite Persistence (investigations table with migration 002)
    │
    ▼
Analyst Presentation Layer
    ├── REST API (GET /api/v1/investigations/{id})
    ├── In-Memory Demo API (GET /api/v1/investigations/demo-scenarios)
    └── React 19 Frontend Console (http://localhost:3000)
```

---

## Complete Feature Inventory (Days 1–5)

### 1. Frontend Console (`frontend/`)
- **Stack**: React 19, TypeScript, Vite, Vanilla CSS Design System.
- **Components**:
  - `Navbar`: System branding, tab switcher, real-time backend health indicator.
  - `Dashboard`: Aggregate metric cards, active anomalies queue, one-click investigation trigger.
  - `DossierView`: Comprehensive dossier view with ECI hero card, 5-factor breakdown, prominent contradiction alert box, canonical source cards, auditable gating exclusion log, and interactive analyst review checklist.
  - `DemoScenarioSelector`: 3-scenario demo switcher with instant in-memory rendering.
  - `InvestigationProgress`: Live 4-stage pipeline stepper (`QUERY_GENERATION` -> `EVIDENCE_SEARCH` -> `VERIFICATION` -> `SYNTHESIS`).
  - `SimulateAnomalyModal`: Ingestion modal with 3 realistic merchant presets + custom form.
- **Architectural Purity**: Zero calculation duplication in the frontend. All numbers, bands, factor scores, and deduction penalties are computed exclusively by the backend.

### 2. Backend API (`backend/app/`)
- **API Routes**:
  - `GET /health` — Application health check
  - `POST /api/v1/risk-events` — Ingest simulated risk anomaly
  - `GET /api/v1/risk-events/{id}` — Get risk event by ID
  - `GET /api/v1/risk-events` — List risk events
  - `POST /api/v1/investigations` — Trigger investigation for `risk_event_id`
  - `GET /api/v1/investigations/demo-scenarios` — In-memory offline deterministic demo scenarios (UrbanCraft India, QuickDeal Bazaar, TrendWear Daily)
  - `GET /api/v1/investigations/{id}` — Get investigation details with complete Evidence Dossier, PipelineMetadata, and ECI v1.1 breakdown
  - `GET /api/v1/investigations` — List investigations with status/risk_event filtering
  - `GET /api/v1/integrations/status` — Status of configured credentials
  - `GET /api/v1/integrations/exa/health` — Exa live connectivity check
  - `GET /api/v1/integrations/gemini/health` — Gemini live connectivity check
- **Scoring Engine (`backend/app/services/scoring/eci_engine.py`)**:
  - Deterministic ECI v1.1 formula bounded strictly to $[0, 100]$.
  - Per-item entity gating (`merchant_match == UNRELATED` → 0 contribution, logged in `excluded_items`).
  - Per-item temporal causality gating (`POST_ANOMALY` → 0 causal explanation support).
  - Per-item source authority ceiling (low-credibility sources capped at 29 ECI points).
  - Claim-group aware independence bonus (syndicated copies of the same release share a group ID and yield 0 extra bonus).
  - Contradiction deduction penalties (-10 pts moderate, -25 pts severe).

### 3. Evaluation Benchmark Suite (`backend/evaluation/`)
- **25 Labeled Synthetic Cases**: Spanning all 12 archetypes (A through L), partitioned into 18 dev and 7 held-out cases.
- **Benchmark Performance (ECI v1.1)**:
  - **Full Benchmark (N=25)**: Accuracy **60.00%** (15/25), Macro F1 **0.5015**
  - **Held-Out Split (N=7)**: Accuracy **57.14%** (4/7), Macro F1 **0.4000**
  - **Development Split (N=18)**: Accuracy **61.11%** (11/18), Macro F1 **0.5025**
  - **Contradiction Detection F1**: **1.0000** (100% Precision & 100% Recall across all splits)
  - **Score Separation**: Strictly monotonic mean ECI ($11.0 < 34.6 < 82.3 < 96.0$)

---

## Deterministic Demo Scenarios Reference

The demo API (`GET /api/v1/investigations/demo-scenarios`) returns 3 pre-computed scenarios:

1. **UrbanCraft India** (Festive Handcrafted Decor):
   - **Simulated Anomaly**: $5.2\times$ volume spike during Diwali.
   - **ECI Score**: **100 / 100** (Band: `VERY STRONG`, Confidence: `HIGH`).
   - **Corroboration**: Viral Instagram reel (2.4M views) and NDTV Lifestyle feature. Direct entity match, contemporaneous timing, 4/4 high factor contributions.
2. **QuickDeal Bazaar** (Electronics & Accessories):
   - **Simulated Anomaly**: $8.0\times$ midnight volume surge.
   - **ECI Score**: **0 / 100** (Band: `LOW`, Confidence: `LOW`).
   - **Corroboration**: Zero external footprint across news, social media, or registry. Suggests transaction pattern anomaly without public commercial event.
3. **TrendWear Daily** (Fast Fashion Apparel):
   - **Simulated Anomaly**: $4.1\times$ flash sale surge.
   - **ECI Score**: **4 / 100** (Band: `LOW`, Confidence: `MEDIUM`, Contradiction: `PRESENT`).
   - **Scoring Breakdown**: Self-asserted social source caps base score at 29 (authority ceiling). Two severe consumer scam/non-delivery contradictions deduct 25 points, arriving at a net score of 4. Prominent contradiction alert box displayed.

> **Note on Score Consistency**: In Day 3 (ECI v1), TrendWear scored 33 (Moderate). In Day 4 (ECI v1.1), the introduction of the source authority ceiling (cap at 29) and severe contradiction deductions (-25 pts) legitimately adjusted this score to 4. The frontend never hardcodes any scores; it renders whatever the backend calculates.

---

## How to Run & Verify

### Running the Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Running the Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Running the Pytest Suite (154 Tests)
```bash
cd backend
pytest tests -q
# Expected: 154 passed in ~3s
```

### Syncing Demo Scenarios Fixture (Offline Snapshot)
```bash
cd backend
python scripts/export_demo_fixtures.py
# Validated by backend/tests/integration/test_demo_fixtures_sync.py
```

### Running the Evaluation Benchmark
```bash
cd backend
python -m evaluation.runner
# Expected: 60.00% accuracy, 0.5015 macro F1, 1.0000 contradiction F1
```

### Building the Frontend for Production
```bash
cd frontend
npm run build
# Expected: 0 errors, built in ~2.9s, ~340 kB bundle
```

---

## Engineering Guidelines & Rules of Engagement

1. **NO Hardcoded Scores in Frontend**:
   - The frontend must never calculate, override, or hardcode ECI scores, factor percentages, or bands.
2. **NO Arbitrary Retuning of ECI**:
   - ECI v1.1 mathematical rules and weights must remain consistent across benchmark and production.
3. **Preserve Neutral Terminology**:
   - Always use "External Evidence Corroboration", "Evidence Support", and "Contradictory Evidence".
   - Never use "Fraud Score", "Safe Merchant", or "Red Flags".
4. **Human in the Loop**:
   - Never implement automated payment freezes or fund holds.
   - The checklist recommendations are advisory for the human risk analyst.
5. **Git Hygiene**:
   - Only local commits (`git commit`). Never run `git push` without user instruction.
