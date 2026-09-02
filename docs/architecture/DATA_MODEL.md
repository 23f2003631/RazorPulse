# RazorPulse — Data Model

## Overview

The RazorPulse data model consists of three core tables in Supabase (PostgreSQL 15+), extended in Migration 002 for structured investigation outputs and dossiers.

## Entity Relationship

```
┌──────────────┐       ┌──────────────────┐       ┌───────────────────────────┐
│  merchants   │ 1───N │   risk_events    │ 1───N │      investigations       │
│              │       │                  │       │                           │
│  id (PK)     │       │  id (PK)         │       │  id (PK)                  │
│  merchant_   │       │  merchant_id(FK) │       │  risk_event_id (FK)       │
│    name      │       │  anomaly_type    │       │  status                   │
│  merchant_   │       │  occurred_at     │       │  eci_score                │
│    domain    │       │  baseline_txn_   │       │  eci_band                 │
│  created_at  │       │    count         │       │  eci_version              │
│  updated_at  │       │  observed_txn_   │       │  evidence_count           │
│              │       │    count         │       │  search_queries (JSONB)   │
│              │       │  percentage_     │       │  eci_breakdown (JSONB)    │
│              │       │    change        │       │  dossier (JSONB)          │
│              │       │  txn_amount      │       │  evidence_items (JSONB)   │
│              │       │  currency        │       │  verification_items(JSONB)│
│              │       │  risk_reason     │       │  error_stage              │
│              │       │  geographic_info │       │  error_message            │
│              │       │  source          │       │  started_at               │
│              │       │  status          │       │  completed_at             │
│              │       │  created_at      │       │  created_at               │
│              │       │  updated_at      │       │  updated_at               │
└──────────────┘       └──────────────────┘       └───────────────────────────┘
```

## Tables

### 1. `merchants`
Stores merchant identity and domain for query generation and entity matching.

### 2. `risk_events`
Stores anomalous transaction surge events.
- `source`: Tracks provenance (`simulated`, `razorpay_webhook`, `razorpay_api`, `manual`).
- `status`: Lifecycle (`pending`, `investigating`, `completed`, `failed`, `dismissed`).

### 3. `investigations`
Stores investigation executions, deterministic ECI results, and full analyst dossiers.
- `status`: `pending`, `searching`, `verifying`, `scoring`, `completed`, `failed`.
- `eci_score`: Integer (0–100).
- `eci_band`: Text (`low`, `moderate`, `strong`, `very_strong`).
- `eci_version`: Text (default `'v1'`).
- `dossier`: Full JSONB Evidence Dossier including citations and review checklist.
- `evidence_items`: JSONB list of normalized evidence records.
- `verification_items`: JSONB list of structured Gemini verification assessments.
- `search_queries`: JSONB list of executed search intents.

## Security (Row Level Security)
All tables have Row Level Security enabled, restricting access to `service_role` (backend server).
Anon key access is blocked.
