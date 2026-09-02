# RazorPulse — Data Model

## Overview

The Day 1 data model consists of three tables designed for risk event ingestion and investigation tracking. The design follows the principle that the central domain object is a **Risk Event** (an anomaly), not a payment or transaction.

## Entity Relationship

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  merchants   │ 1───N │   risk_events    │ 1───N │ investigations   │
│              │       │                  │       │                  │
│  id (PK)     │       │  id (PK)         │       │  id (PK)         │
│  merchant_   │       │  merchant_id(FK) │       │  risk_event_     │
│    name      │       │  anomaly_type    │       │    id (FK)       │
│  merchant_   │       │  occurred_at     │       │  status          │
│    domain    │       │  baseline_txn_   │       │  started_at      │
│  created_at  │       │    count         │       │  completed_at    │
│  updated_at  │       │  observed_txn_   │       │  created_at      │
│              │       │    count         │       │  updated_at      │
│              │       │  percentage_     │       │                  │
│              │       │    change        │       └──────────────────┘
│              │       │  txn_amount      │
│              │       │  currency        │
│              │       │  risk_reason     │
│              │       │  geographic_info │
│              │       │  source          │
│              │       │  status          │
│              │       │  created_at      │
│              │       │  updated_at      │
│              │       │                  │
└──────────────┘       └──────────────────┘
```

## Tables

### 1. `merchants`

**Purpose:** Stores merchant identity. Separated from risk_events so multiple events for the same merchant share a single identity record.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | UUID (PK) | No | uuid_generate_v4() | Auto-generated |
| merchant_name | TEXT | No | — | Display name |
| merchant_domain | TEXT | Yes | — | Web domain (critical for Exa search) |
| created_at | TIMESTAMPTZ | No | NOW() | Record creation time |
| updated_at | TIMESTAMPTZ | Yes | — | Last modification time |

**Indexes:**
- `idx_merchants_domain` on `merchant_domain` (partial, WHERE NOT NULL)

**Design rationale:** Merchant domain is the primary key for Exa search queries. By separating merchants, we can track domain changes and avoid duplication across events.

### 2. `risk_events`

**Purpose:** The CENTRAL domain object. Represents an anomalous payment pattern, not an individual transaction.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | UUID (PK) | No | uuid_generate_v4() | Auto-generated |
| merchant_id | UUID (FK→merchants) | No | — | ON DELETE CASCADE |
| anomaly_type | TEXT | No | — | e.g., "transaction_velocity_spike" |
| occurred_at | TIMESTAMPTZ | No | — | When the anomaly began |
| baseline_transaction_count | INTEGER | Yes | — | Normal expected count |
| observed_transaction_count | INTEGER | Yes | — | Actual count during anomaly |
| percentage_change | DOUBLE PRECISION | Yes | — | Computed: (observed-baseline)/baseline × 100 |
| transaction_amount | DOUBLE PRECISION | Yes | — | Total amount during anomaly |
| currency | TEXT | No | 'INR' | ISO 4217 code |
| risk_reason | TEXT | Yes | — | Human-readable reason |
| geographic_info | TEXT | Yes | — | Location context |
| source | TEXT | No | 'simulated' | CRITICAL: tracks data provenance |
| status | TEXT | No | 'pending' | Investigation lifecycle |
| created_at | TIMESTAMPTZ | No | NOW() | Ingestion time |
| updated_at | TIMESTAMPTZ | Yes | — | Last status change |

**Status values:** `pending`, `investigating`, `completed`, `failed`, `dismissed`

**Source values:** `simulated`, `razorpay_webhook`, `razorpay_api`, `manual`

**Indexes:**
- `idx_risk_events_merchant_id` on `merchant_id`
- `idx_risk_events_status` on `status`
- `idx_risk_events_created_at` on `created_at DESC`

**Design rationale:**
- `source` field honestly distinguishes simulated from real data
- `percentage_change` is pre-computed and stored for query performance
- Quantitative fields are nullable because not all anomaly types have all metrics

### 3. `investigations`

**Purpose:** Tracks the lifecycle of each investigation pipeline run. Separated from risk_events because an event may be re-investigated.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| id | UUID (PK) | No | uuid_generate_v4() | Auto-generated |
| risk_event_id | UUID (FK→risk_events) | No | — | ON DELETE CASCADE |
| status | TEXT | No | 'pending' | Investigation lifecycle |
| started_at | TIMESTAMPTZ | Yes | — | When investigation began |
| completed_at | TIMESTAMPTZ | Yes | — | When investigation finished |
| created_at | TIMESTAMPTZ | No | NOW() | Record creation time |
| updated_at | TIMESTAMPTZ | Yes | — | Last modification time |

**Future columns (to be added):**
- `eci_score` — Event Corroboration Index result
- `evidence_summary` — JSON summary of evidence
- `exa_results` — Raw Exa search results
- `gemini_assessments` — Structured Gemini assessments

**Indexes:**
- `idx_investigations_risk_event_id` on `risk_event_id`
- `idx_investigations_status` on `status`

## Security (Row Level Security)

All tables have RLS enabled. Policies:
- **service_role** (backend server): Full CRUD access
- **anon** (frontend/public): No access

This ensures the frontend cannot bypass the backend API.

## Migration Strategy

Day 1 uses a single SQL file (`001_initial_schema.sql`) run directly in the Supabase SQL Editor. As the schema evolves, new numbered SQL files will be added to `database/schemas/`.
