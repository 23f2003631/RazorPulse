# RazorPulse

**External Evidence Corroboration Engine for Anomalous Payment-Risk Events**

> Built for the **Razorpay AI Buildathon 2026** — *AI Risk Manager Track*  
> **Status:** Day 5 Complete — Production-Grade Analyst Console, Deterministic Demo Scenarios, ECI v1.1 Scoring Engine, 152 Automated Tests (100% passing), 25-Case Ground Truth Benchmark Validated.

---

## Strategic Mission & Ethical Boundaries

When a merchant experiences an anomalous payment surge (e.g., $5\times$ volume spike, midnight velocity surge, sudden average ticket increase), payment risk teams face a critical dilemma: **Is this fraudulent transaction laundering / card testing, or is it a legitimate commercial event (viral social media campaign, flash sale, PR feature)?**

RazorPulse operates strictly as an **External Evidence Corroboration Engine**:
- **Core Question Answered**: *"How strongly does external evidence (news, social media, platform announcements, regulatory filings) corroborate a real-world explanation for this anomaly?"*
- **What RazorPulse Is NOT**:
  - It is **not** an internal fraud scoring model.
  - It does **not** estimate fraud probabilities or rate merchant safety.
  - It does **not** make autonomous fund holds, payment blocks, or merchant freezes.
- **Human Authority**: The final disposition always remains with the human risk analyst. RazorPulse equips analysts with a verifiable evidence dossier, transparent factor breakdown, auditable exclusion logs, canonical citations, and an interactive review checklist.

---

## System Architecture

```
                      +---------------------------------------+
                      | Razorpay Risk Anomaly / Test Webhook  |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |   POST /api/v1/risk-events Ingestion  |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |         4-STAGE PIPELINE RUNNER       |
                      |                                       |
                      | 1. Query Generation (Multi-intent)    |
                      | 2. Evidence Search (Exa / Mock)       |
                      | 3. Verification & Gating (Gemini/Det) |
                      |    - Entity match gating              |
                      |    - Temporal causality gating        |
                      |    - Source authority ceiling         |
                      |    - Claim-group deduplication        |
                      | 4. Synthesis & ECI v1.1 Scoring       |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |     Evidence Dossier & ECI Score      |
                      |  - Band: Low / Mod / Strong / V.Strong|
                      |  - Factor Breakdown (5 dimensions)    |
                      |  - Contradiction Alert Box            |
                      |  - Auditable Gating Exclusion Log     |
                      |  - Canonical Evidence Citations [E1]  |
                      +---------------------------------------+
                                          |
                         +----------------+----------------+
                         |                                 |
                         v                                 v
        +---------------------------------+  +-------------------------------+
        |   FastAPI REST Backend (:8000)   |  |   Deterministic Demo Engine   |
        |   - /api/v1/risk-events         |  |   - In-memory offline run     |
        |   - /api/v1/investigations      |  |   - Network-independent demo  |
        |   - /api/v1/demo-scenarios      |  |   - Zero API dependency       |
        +---------------------------------+  +-------------------------------+
                         |                                 |
                         +----------------+----------------+
                                          |
                                          v
                      +---------------------------------------+
                      |      ANALYST DASHBOARD (React 19)     |
                      |   - Mode Switch: Demo vs Live Queue   |
                      |   - Interactive Anomaly Simulator     |
                      |   - Real-time 4-Stage Stepper         |
                      |   - Comprehensive Evidence Dossier    |
                      |   - Human Analyst Review Checklist    |
                      +---------------------------------------+
```

---

## Deterministic Demo Scenarios

For hackathon jury evaluations and live presentations, RazorPulse includes a network-independent demonstration path that executes without external API dependencies:

| Scenario | Merchant | Anomaly Context | ECI Score | Band | Engine Findings |
|---|---|---|---|---|---|
| **Scenario 1** | **UrbanCraft India** | $5.2\times$ volume spike during Diwali festive season | **100 / 100** | `VERY STRONG` | High-credibility external footprint: Viral Instagram reel (2.4M views) and NDTV Lifestyle feature. Direct entity match, contemporaneous timing, 4/4 high factor contributions. |
| **Scenario 2** | **QuickDeal Bazaar** | $8.0\times$ midnight volume surge | **0 / 100** | `LOW` | Zero external evidence found across news, social platforms, or registry. Confirms transaction pattern anomaly without public commercial event. |
| **Scenario 3** | **TrendWear Daily** | $4.1\times$ flash sale surge | **4 / 100** | `LOW` *(Contradicted)* | **ECI v1.1 Scoring**: Self-asserted social source caps base score at 29 (authority ceiling). Two severe consumer scam/non-delivery contradictions deduct 25 points, arriving at a net score of 4. Prominent contradiction alert displayed. |

---

## Technology Stack

### Frontend (Analyst Console)
- **Framework**: React 19, TypeScript, Vite
- **Styling**: Hand-crafted Vanilla CSS Design System (`theme.css`, `index.css`) with deep slate fintech palette
- **Port**: `localhost:3000` (Vite proxy forwards `/api` requests to backend `:8000`)
- **Purity**: Zero business logic duplication (all scores, bands, factor weights derived by backend)

### Backend & Scoring
- **Framework**: FastAPI (Python 3.10+)
- **Validation**: Pydantic v2 schemas
- **Scoring Engine**: Deterministic ECI v1.1 (5-factor formula, authority ceilings, temporal/entity gating, claim-group deduplication)
- **Database**: SQLite / PostgreSQL (Supabase-compatible)
- **Port**: `localhost:8000`

### Testing & Evaluation Benchmark
- **Pytest**: 152 automated tests (unit, integration, invariants, gating, E2E), 100% passing.
- **Ground Truth Benchmark**: 25 synthetic merchant cases across 12 archetypes (18 development, 7 held-out).
- **Benchmark Performance**:
  - Corroboration Accuracy: **60.00%** (15/25)
  - Macro F1: **0.5015**
  - Contradiction Precision: **1.0000** (100.0%)
  - Contradiction Recall: **1.0000** (100.0%)
  - Contradiction F1: **1.0000** (100.0%)

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# Clone repository and enter backend directory
cd backend

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 3. Frontend Setup
```bash
# In a new terminal, enter frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Analyst Console will be live at [http://localhost:3000](http://localhost:3000).

---

## Running Verification & Tests

### Automated Test Suite (152 Tests)
```bash
cd backend
pytest tests -q
# Expected output: 152 passed in ~13s
```

### 25-Case Evaluation Benchmark
```bash
cd backend
python -m evaluation.runner
# Expected output: 60.00% accuracy, 0.5015 macro F1, 1.0000 contradiction F1
```

### Frontend Production Build
```bash
cd frontend
npm run build
# Expected output: Built in ~2.6s, 0 errors, ~260 kB bundle
```

---

## Project Documentation Index

- [Project Status](docs/PROJECT_STATUS.md): Complete milestone tracking across Days 1–5.
- [AI Handoff Guide](docs/AI_HANDOFF.md): Engineering handoff and architectural guidelines.
- [Day 5 Productization Log](docs/development/DAY_5.md): Detailed Day 5 implementation report.
- [Day 4 Calibration Log](docs/development/DAY_4.md): ECI v1.1 gating and authority ceiling upgrades.
- [Day 3 Evaluation Log](docs/development/DAY_3.md): 25-case benchmark and failure mode analysis.
- [Evaluation Results](docs/evaluation/RESULTS.md): Full analysis of benchmark metrics and case breakdowns.
- [Architecture](docs/architecture/ARCHITECTURE.md): System architecture and data flow.
- [ECI Scoring Specification](docs/architecture/ECI_SCORING.md): Formal ECI mathematical specification.

---

## License

Apache 2.0 / MIT. Developed for the Razorpay AI Buildathon 2026.
