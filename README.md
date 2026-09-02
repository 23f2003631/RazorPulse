# RazorPulse

AI-powered external-context verification for anomalous payment-risk events.

**Status:** Repository initialized — application implementation has not started.

## Overview

RazorPulse is a risk investigation copilot system designed for the Razorpay AI Risk Manager track. It is intended to assist risk analysts in investigating anomalous payment events by automatically discovering external context, verifying evidence, and providing deterministic corroboration scores.

### Problem

High-risk payment anomalies require rapid, evidence-based investigation. Manual investigation is time-consuming and prone to cognitive bias. RazorPulse aims to augment human risk analysts with AI-driven discovery and deterministic, explainable scoring.

## Architecture at a Glance

```
Razorpay Test Mode / simulated risk event
        ↓
Risk anomaly ingestion
        ↓
External event discovery (Exa AI)
        ↓
Evidence verification and interpretation (Gemini)
        ↓
Deterministic corroboration-scoring engine
        ↓
Human-readable risk evidence dossier
        ↓
Supabase persistence
        ↓
Risk Analyst Dashboard
```

### Design Principles

- **Defense-Only**: Read-only intelligence gathering. No autonomous financial action.
- **Human-in-the-Loop**: Analysts make final decisions; system provides evidence.
- **Explainable**: All scoring decisions must be transparent and audit-able.
- **Evidence-Driven**: All conclusions backed by traceable, provenance-tracked evidence.
- **Deterministic Final Scoring**: No probabilistic black boxes in the final corroboration score.
- **Fail-Closed**: Insufficient evidence → conservative (safe) scores.

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Validation**: Pydantic
- **Environment**: Python virtual environment

### Frontend
- **Framework**: Next.js
- **Language**: TypeScript
- **UI Library**: React
- **Styling**: Tailwind CSS

### Database
- **Primary**: Supabase (PostgreSQL)
- **ORM**: SQLAlchemy (planned)

### AI / External Services
- **External Intelligence**: Exa AI (web/event discovery)
- **Evidence Interpretation**: Gemini (LLM-based verification)
- **Scoring**: Deterministic Python rules engine

### DevOps
- **Version Control**: Git / GitHub
- **CI/CD**: GitHub Actions (planned)

## Repository Structure

```
razorpulse/
├── README.md                     # This file
├── .gitignore                    # Git ignore rules
├── .env.example                  # Environment variables template
├── LICENSE                       # MIT or applicable license
│
├── docs/                         # Documentation
│   ├── architecture/             # System architecture docs
│   ├── product/                  # Product requirements
│   ├── security/                 # Security principles
│   ├── api/                      # API specifications
│   └── evaluation/               # Evaluation methodology
│
├── backend/                      # FastAPI backend
│   ├── README.md
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example
│   ├── app/
│   │   ├── main.py              # Application entry point
│   │   ├── config/              # Configuration
│   │   ├── api/routes/          # API route definitions
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   │   ├── razorpay/        # Razorpay integration
│   │   │   ├── exa/             # Exa discovery service
│   │   │   ├── gemini/          # Gemini verification
│   │   │   ├── scoring/         # Corroboration scoring
│   │   │   └── investigation/   # Investigation orchestration
│   │   ├── repositories/        # Data access layer
│   │   ├── core/                # Core utilities (exceptions, logging)
│   │   └── utils/               # Helper functions
│   ├── tests/
│   │   ├── unit/                # Unit tests
│   │   ├── integration/         # Integration tests
│   │   └── fixtures/            # Test fixtures
│   └── scripts/                 # Utility scripts
│
├── frontend/                     # Next.js frontend
│   ├── README.md
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── app/                     # Next.js App Router
│   ├── components/              # React components
│   ├── lib/                     # Utility libraries
│   ├── hooks/                   # Custom React hooks
│   ├── types/                   # TypeScript type definitions
│   ├── services/                # API and external services
│   └── public/                  # Static assets
│
├── database/                     # Database schema and migrations
│   ├── README.md
│   ├── migrations/              # Alembic migrations
│   ├── schemas/                 # Schema definitions
│   └── seed/                    # Seed data
│
├── evaluation/                   # Benchmark and evaluation suite
│   ├── README.md
│   ├── datasets/                # Benchmark datasets
│   ├── experiments/             # Experiment definitions
│   ├── results/                 # Experiment results
│   └── reports/                 # Analysis reports
│
├── data/                         # Data directory
│   ├── raw/                     # Raw data
│   ├── processed/               # Processed data
│   └── synthetic/               # Synthetic test data
│
├── scripts/                      # Repository-level scripts
│
└── .github/workflows/            # CI/CD workflows
```

## Development Phases

### Phase 0: Repository Initialization ✓
Repository structure and development environment setup.

### Phase 1: Razorpay Event Ingestion
Webhook ingestion and risk event normalization.

### Phase 2: Risk Anomaly Simulation
Test harness for simulated anomalies.

### Phase 3: Exa External-Event Discovery
Integration with Exa AI for external event discovery.

### Phase 4: Gemini Evidence Verification
LLM-based evidence verification and interpretation.

### Phase 5: Deterministic Corroboration Engine
Rules-based scoring and corroboration.

### Phase 6: Supabase Persistence
PostgreSQL schema and data access layer.

### Phase 7: Risk Analyst Dashboard
Frontend UI for investigation and decision-making.

### Phase 8: Evaluation Benchmark
Precision, recall, citation correctness metrics.

### Phase 9: Adversarial Testing
Robustness and edge-case testing.

### Phase 10: Demo & Production Polish
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

**Note**: This repository is in initialization phase. No application logic has been implemented. Features and integrations are planned for upcoming phases.
