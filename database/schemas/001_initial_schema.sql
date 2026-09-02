-- ============================================================
-- RazorPulse — Initial Database Schema
-- ============================================================
-- Target: Supabase (PostgreSQL 15+)
-- Purpose: Day 1 foundation tables for risk event ingestion
--          and investigation tracking.
--
-- INSTRUCTIONS:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Paste this entire file
--   3. Click "Run"
--
-- TABLES CREATED:
--   1. merchants       — Merchant identity
--   2. risk_events     — Anomalous payment events
--   3. investigations  — Investigation lifecycle tracking
--
-- DESIGN RATIONALE:
--   - merchants: Separated from risk_events so multiple events
--     for the same merchant share a single identity record.
--     Domain is critical for Exa search.
--   - risk_events: The CENTRAL domain object. Represents an
--     anomaly (NOT a payment). Source field honestly distinguishes
--     simulated vs real data.
--   - investigations: Tracks the lifecycle of each investigation
--     pipeline run (Exa search → Gemini verification → ECI scoring).
--     Separated from risk_events because an event may be
--     re-investigated or investigated multiple times.
--
-- SECURITY:
--   - Row Level Security (RLS) is enabled on all tables.
--   - Policies allow full access only via service_role key
--     (backend server). The anon key has NO access.
--   - This ensures the frontend cannot directly read/write these
--     tables without going through the backend API.
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. MERCHANTS
-- ============================================================
CREATE TABLE IF NOT EXISTS merchants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_name   TEXT NOT NULL,
    merchant_domain TEXT,                     -- e.g. "example.com"
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ
);

-- Index on domain for upsert lookups
CREATE INDEX IF NOT EXISTS idx_merchants_domain
    ON merchants (merchant_domain)
    WHERE merchant_domain IS NOT NULL;

-- ============================================================
-- 2. RISK EVENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS risk_events (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_id                 UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,

    -- Anomaly characterization
    anomaly_type                TEXT NOT NULL,   -- e.g. "transaction_velocity_spike"
    occurred_at                 TIMESTAMPTZ NOT NULL,

    -- Quantitative signals
    baseline_transaction_count  INTEGER,
    observed_transaction_count  INTEGER,
    percentage_change           DOUBLE PRECISION,
    transaction_amount          DOUBLE PRECISION,
    currency                    TEXT NOT NULL DEFAULT 'INR',

    -- Context
    risk_reason                 TEXT,
    geographic_info             TEXT,

    -- Source tracking (SIMULATED / razorpay_webhook / razorpay_api / manual)
    source                      TEXT NOT NULL DEFAULT 'simulated',

    -- Investigation lifecycle
    status                      TEXT NOT NULL DEFAULT 'pending',

    -- Timestamps
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ
);

-- Index on merchant for lookups
CREATE INDEX IF NOT EXISTS idx_risk_events_merchant_id
    ON risk_events (merchant_id);

-- Index on status for filtering
CREATE INDEX IF NOT EXISTS idx_risk_events_status
    ON risk_events (status);

-- Index on created_at for chronological listing
CREATE INDEX IF NOT EXISTS idx_risk_events_created_at
    ON risk_events (created_at DESC);

-- ============================================================
-- 3. INVESTIGATIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS investigations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    risk_event_id   UUID NOT NULL REFERENCES risk_events(id) ON DELETE CASCADE,

    -- Lifecycle
    status          TEXT NOT NULL DEFAULT 'pending',
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,

    -- Results (populated by later pipeline phases)
    -- eci_score, evidence_summary, etc. will be added in future migrations

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_investigations_risk_event_id
    ON investigations (risk_event_id);

CREATE INDEX IF NOT EXISTS idx_investigations_status
    ON investigations (status);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
-- Enable RLS on all tables
ALTER TABLE merchants ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;

-- Service role (backend) has full access
CREATE POLICY "Service role full access on merchants"
    ON merchants FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on risk_events"
    ON risk_events FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role full access on investigations"
    ON investigations FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================
-- END OF INITIAL SCHEMA
-- ============================================================
