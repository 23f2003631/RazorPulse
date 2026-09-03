# RazorPulse

AI-powered external-context verification for anomalous payment-risk events.

**Status:** Day 3 complete — Evaluation benchmark suite (25 cases), canonical offline runner, ECI calibration analysis, evidence quality gates, pipeline reproducibility metadata, 128 tests passing (100%).

## Overview

RazorPulse is a risk investigation copilot system designed for the Razorpay AI Risk Manager track. It assists human risk analysts in investigating anomalous payment events by automatically discovering external context, verifying evidence, and providing deterministic corroboration scores.

### Problem

High-risk payment anomalies require rapid, evidence-based investigation. Manual investigation is time-consuming and prone to cognitive bias. RazorPulse augments human risk analysts with AI-driven discovery and deterministic, explainable scoring.

## Architecture at a Glance

```
Razorpay Test Mode / simulated risk event
        ↓
Risk anomaly ingestion
        ↓
External event discovery (Exa AI)
        ↓
Evidence Quality Gates & Claim Grouping
        ↓
Evidence verification and interpretation (Gemini)
        ↓
Deterministic corroboration-scoring engine (ECI v1)
        ↓
Human-readable risk evidence dossier with [E1] citations
        ↓
Supabase persistence (with PipelineMetadata)
        ↓
Risk Analyst Dashboard
```

### Design Principles

- **Defense-Only**: Read-only intelligence gathering. No autonomous financial action.
- **Human-in-the-Loop**: Analysts make final decisions; system provides evidence.
- **Explainable**: All scoring decisions must be transparent and auditable.
- **Evidence-Driven**: All conclusions backed by traceable, provenance-tracked evidence.
- **Deterministic Final Scoring**: No probabilistic black boxes in the final corroboration score.
- **Fail-Closed**: Insufficient evidence → conservative (safe) scores.

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.14
- **Validation**: Pydantic v2
- **Environment**: Python virtual environment

### Frontend (Day 4)
- **Framework**: React / Vite
- **Language**: TypeScript / JavaScript
- **Styling**: Vanilla CSS tokens

### Database
- **Primary**: Supabase (PostgreSQL)
- **Data Access**: supabase-py (direct client)

### AI / External Services
- **External Intelligence**: Exa AI (web/event discovery)
- **Evidence Interpretation**: Google Gemini (`gemini-3.5-flash-lite`, structured verification)
- **Scoring**: Deterministic Python rules engine (ECI v1)

### Testing & Evaluation
- **Testing**: pytest (128 automated tests, 100% passing)
- **Evaluation Suite**: 25 labeled synthetic benchmark cases (18 dev / 7 held-out) spanning 12 archetypes
- **Benchmark Runner**: Offline fixture-only execution measuring 4-class corroboration and binary contradiction F1

## Repository Structure

```
razorpulse/
├── README.md                     # This file
├── .gitignore                    # Git ignore rules
├── .env.example                  # Environment variables template
├── LICENSE                       # MIT or applicable license
│
├── docs/                         # Documentation
│   ├── architecture/             # System architecture docs (ARCHITECTURE, DATA_MODEL, INVESTIGATION_PIPELINE, ECI_SCORING)
│   ├── development/              # Development logs (DAY_1, DAY_2)
│   ├── product/                  # Product requirements
│   ├── security/                 # Security principles
│   └── api/                      # API specifications
│
├── backend/                      # FastAPI backend
│   ├── README.md
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example
│   ├── app/
│   │   ├── main.py              # Application entry point
│   │   ├── config/              # Configuration & settings
│   │   ├── api/routes/          # API route definitions (health, risk_events, investigations, integrations)
│   │   ├── schemas/             # Pydantic schemas (evidence, verification, eci, dossier, investigation)
│   │   ├── services/            # Business logic (exa, gemini, scoring, investigation)
│   │   ├── repositories/        # Data access layer (merchant, risk_event, investigation)
│   │   ├── core/                # Core utilities (exceptions, logging)
│   │   └── utils/               # Helper functions
│   ├── tests/
│   │   ├── unit/                # Unit tests (config, schemas, query gen, normalizer, ECI invariants, verifier, dossier)
│   │   ├── integration/         # Integration tests (health, risk_events, investigations API, pipeline E2E)
│   │   └── fixtures/            # Test fixtures (risk events, synthetic scenarios)
│   ├── evaluation/              # Evaluation Framework (ground truth, dataset, metrics, runner, calibration)
│   └── scripts/                 # Scripts (run_demo, smoke_test_exa, smoke_test_gemini, smoke_test_pipeline)
│
├── database/                     # Database schema and migrations
│   └── schemas/                 # SQL schemas (001_initial_schema.sql, 002_investigations_schema.sql)
│
└── docs/                         # Documentation
    ├── architecture/             # Architecture docs
    ├── development/              # Day 1, Day 2, Day 3 progress logs
    └── evaluation/               # EVALUATION_METHODOLOGY, DATASET, RESULTS
```

## Development Phases

### Phase 0: Repository Initialization ✓
Repository structure and development environment setup.

### Phase 1: Razorpay Event Ingestion ✓
Simulated risk event ingestion and normalization.

### Phase 2: Risk Anomaly Simulation ✓
Synthetic test fixtures for simulated anomalies.

### Phase 3: Exa External-Event Discovery ✓
Bounded multi-intent query generation, semantic search, evidence normalization, and URL deduplication.

### Phase 4: Gemini Evidence Verification ✓
Anti-hallucination prompt and structured Pydantic assessment for entity match, timing, explanation support, credibility, and contradictions.

### Phase 5: Deterministic Corroboration Engine ✓
Deterministic ECI v1 heuristic scoring engine with transparent factor breakdown and 10 score invariants verified.

### Phase 6: Supabase Persistence ✓
PostgreSQL schema migrations (001, 002) and repository CRUD for investigations and dossiers.

### Phase 7: Evaluation Benchmark Suite & Robustness ✓
25-case synthetic benchmark across 12 archetypes, canonical offline runner, ECI calibration analysis, evidence quality gates, and reproducibility metadata.

### Phase 8: Risk Analyst Dashboard (Day 4)
Frontend UI for investigation and decision-making (React / Vite).

### Phase 9: Adversarial Tuning & Polish (Day 4)
Model calibration based on Day 3 failure modes and production polish.
Final refinement and deployment-readiness.

## Data Flow (Planned)

1. **Ingestion**: Razorpay webhook → risk event normalization
2. **Discovery**: Risk context → Exa AI → external events & sources
3. **Verification**: Events + sources → Gemini → evidence interpretation
4. **Scoring**: Evidence + rules → deterministic corroboration score
5. **Persistence**: Events, evidence, scores → Supabase
6. **Presentation**: Dashboard → analyst review & action

## Security Principles

- **Secrets Management**: All secrets in `.env.local`, never committed
- **API Keys**: Server-side only; never exposed to frontend
- **Least Privilege**: Services have minimal required permissions
- **Read-Only Intelligence**: No autonomous writes to payment systems
- **Human Decision Boundary**: Final release decisions made by humans
- **Audit Trail**: All actions and decisions logged for compliance
- **Source Traceability**: Every evidence piece links to source

See [docs/security/](docs/security/) for detailed security design.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (local or Supabase)

### Backend Setup (Planned)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Frontend Setup (Planned)
```bash
cd frontend
npm install
npm run dev
```

## Architecture Documentation

See [docs/architecture/](docs/architecture/) for detailed system design, component descriptions, and data flow diagrams.

## Contributing

This repository follows a systematic phase-based development approach. All work must maintain the separation of concerns outlined in the architecture.

## License

[To be determined]

## Contact

For questions or collaboration, please see project documentation.

---

**Note**: Day 1 development is complete. See [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for current status and [docs/AI_HANDOFF.md](docs/AI_HANDOFF.md) for development context.
