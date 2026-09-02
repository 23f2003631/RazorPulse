# RazorPulse — System Architecture

## Strategic Mission

RazorPulse is an **external-context verification copilot** for anomalous payment-risk events. It provides decision support to human risk analysts.

> [!IMPORTANT]
> **RazorPulse is NOT a fraud decision engine.**
> It is an **external-context corroboration engine**.
> It evaluates whether public real-world events (promotions, viral spikes, launches, press coverage) explain an observed anomaly.
> It never makes autonomous financial decisions, approves/rejects transactions, or overrides Razorpay risk systems.

## End-to-End Pipeline Architecture

```
                 ANOMALOUS RISK EVENT
                          │
                          ▼
             ┌─────────────────────────┐
             │   Risk Event Store      │  ← PostgreSQL (Supabase)
             │   (status: pending)     │
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │ Investigation Service   │  ← POST /api/v1/investigations
             │ (status: SEARCHING)     │
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │ Exa Query Intent Builder│  ← Bounded multi-intent generation
             │ (Exa AI Discovery)      │  ← Normalized & deduplicated evidence
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │ Gemini Verifier         │  ← Grounded prompt (anti-hallucination)
             │ (status: VERIFYING)     │  ← Structured Pydantic evaluation
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │ Deterministic ECI Engine│  ← Pure Python rule engine (v1 heuristic)
             │ (status: SCORING)       │  ← 0..100 bounded score + factor breakdown
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │ Dossier Generator       │  ← Executive summary, citations [E1],
             │ (Evidence Dossier)      │    evidence gaps, analyst checklist
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │ Supabase Persistence    │  ← Persists dossier, ECI, and verifications
             │ (status: COMPLETED)     │
             └────────────┬────────────┘
                          │
                          ▼
             ┌─────────────────────────┐
             │ Human Risk Analyst      │  ← GET /api/v1/investigations/{id}
             │ (Decision Support)      │
             └─────────────────────────┘
```

## Service Responsibility Boundaries

| Service | Responsibility | Architectural Boundary |
|---------|---------------|------------------------|
| `risk_event_service` | Risk event ingestion | Ingests, normalizes, and stores payment anomalies. |
| `exa/search_strategy` | External discovery | Generates query intents, discovers web candidates, canonicalizes URLs. Does NOT verify. |
| `gemini/verifier` | Evidence assessment | Evaluates entity match, temporal alignment, and explanation support. Does NOT score ECI. |
| `scoring/eci_engine` | Corroboration calculation | Deterministic, transparent Python formula converting verified items to 0..100 score. |
| `investigation/dossier` | Dossier synthesis | Compiles citations, gaps, uncertainties, and analyst checklist. |
| `investigation/orchestrator` | Pipeline orchestration | Coordinates lifecycle states (`PENDING` -> `SEARCHING` -> `VERIFYING` -> `SCORING` -> `COMPLETED`). |

## Critical Architectural Rules

1. **Exa DISCOVERS evidence**: Search results are candidates, not confirmed facts.
2. **Gemini INTERPRETS evidence**: Assesses evidence relevance using structured output. Does not generate ECI scores.
3. **Python rules ENGINE SCORES evidence**: The ECI is a deterministic, auditable heuristic.
4. **Human DECIDES**: RazorPulse provides evidence dossiers; human analysts make risk decisions.
