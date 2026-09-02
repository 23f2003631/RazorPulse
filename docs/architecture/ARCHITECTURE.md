# RazorPulse — System Architecture

## Overview

RazorPulse is an AI-powered external-context verification copilot for anomalous payment-risk events. It provides decision support to human risk analysts — it never makes autonomous financial decisions.

## High-Level Pipeline

```
    RISK ANOMALY (simulated or webhook)
            │
            ▼
┌─────────────────────────┐
│  Risk Event Ingestion   │  ← FastAPI endpoint
│  POST /api/v1/risk-events│
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Event Normalization    │  ← Pydantic validation
│  + Merchant Resolution  │  ← Find-or-create merchant
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Supabase Persistence   │  ← PostgreSQL via Supabase client
└───────────┬─────────────┘
            │
            ▼  (Day 2+)
┌─────────────────────────┐
│  Exa External Search    │  ← Discovers evidence candidates
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Gemini Verification    │  ← Interprets evidence quality
│  (Structured Output)    │  ← Entity match, temporal, credibility
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Deterministic ECI      │  ← Transparent, auditable scoring
│  Scoring Engine         │  ← Python rules, no LLM black box
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Evidence Dossier       │  ← Complete investigation report
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Human Risk Analyst     │  ← FINAL decision maker
│  (Dashboard)            │
└─────────────────────────┘
```

## Backend Architecture

### Layered Design

```
┌──────────────────────────────────────────┐
│           API Layer (routes/)            │
│  HTTP endpoints, request validation      │
├──────────────────────────────────────────┤
│          Service Layer (services/)       │
│  Business logic, orchestration           │
├──────────────────────────────────────────┤
│       Repository Layer (repositories/)   │
│  Data access, Supabase operations        │
├──────────────────────────────────────────┤
│          Schemas (schemas/)              │
│  Pydantic models for validation          │
├──────────────────────────────────────────┤
│            Core (core/)                  │
│  Exceptions, logging, security           │
└──────────────────────────────────────────┘
```

### Service Responsibility Boundaries

| Service | Responsibility | Boundary |
|---------|---------------|----------|
| `risk_event_service` | Ingestion orchestration | Validate → persist → return |
| `exa/client` | External event discovery | Search → return evidence candidates |
| `gemini/client` | Evidence interpretation | Assess → return structured assessment |
| `scoring/` (future) | ECI calculation | Deterministic rules → transparent score |
| `investigation/` (future) | Pipeline orchestration | Exa → Gemini → scoring → dossier |

### Critical Architectural Boundaries

1. **Exa DISCOVERS** evidence. It does not interpret or score.
2. **Gemini INTERPRETS** evidence. It provides structured assessments as INPUT to scoring.
3. **Python rules ENGINE SCORES** evidence. The ECI is a deterministic function.
4. **Human DECIDES**. RazorPulse provides evidence and scores; humans make risk decisions.

## Database Design

See [DATA_MODEL.md](DATA_MODEL.md) for detailed schema documentation.

## Security Model

- All API keys are server-side only (never exposed to frontend)
- Supabase RLS restricts table access to service_role key
- No secrets in logs (loguru configured with secret filtering)
- `.env` files are in `.gitignore` and never committed
- No autonomous financial actions — read-only intelligence gathering

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend Framework | FastAPI | Async, Pydantic-native, fast development |
| Validation | Pydantic v2 | Type-safe, schema validation with JSON output |
| Database | Supabase (PostgreSQL) | Managed, instant APIs, RLS, free tier |
| DB Client | supabase-py | Direct Supabase integration, simpler than ORM |
| External Search | Exa AI | Semantic web search, content retrieval |
| Evidence Verification | Google Gemini | Structured output, reasoning, cost-effective |
| Gemini Model | gemini-2.5-flash | Fast, affordable, structured output support |
| Scoring | Deterministic Python | Transparent, auditable, no LLM black box |
| Frontend | Next.js + TypeScript | React ecosystem, SSR, Tailwind CSS |
| Logging | Loguru | Structured, colorized, easy configuration |
| Testing | Pytest | Standard Python testing framework |
