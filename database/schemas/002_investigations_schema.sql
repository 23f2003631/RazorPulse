-- ============================================================
-- RazorPulse — Schema Migration 002: Investigation Results
-- ============================================================
-- Target: Supabase (PostgreSQL 15+)
-- Purpose: Adds structured ECI, dossier, and evidence columns
--          to the investigations table for Day 2 pipeline persistence.
--
-- INSTRUCTIONS:
--   1. Open Supabase Dashboard → SQL Editor
--   2. Paste this entire file
--   3. Click "Run"
-- ============================================================

-- Add ECI scoring and metadata columns to investigations
ALTER TABLE investigations
    ADD COLUMN IF NOT EXISTS eci_score          INTEGER,
    ADD COLUMN IF NOT EXISTS eci_band           TEXT,
    ADD COLUMN IF NOT EXISTS eci_version        TEXT NOT NULL DEFAULT 'v1',
    ADD COLUMN IF NOT EXISTS evidence_count     INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS error_stage        TEXT,
    ADD COLUMN IF NOT EXISTS error_message      TEXT,
    ADD COLUMN IF NOT EXISTS search_queries     JSONB,
    ADD COLUMN IF NOT EXISTS eci_breakdown      JSONB,
    ADD COLUMN IF NOT EXISTS dossier            JSONB,
    ADD COLUMN IF NOT EXISTS evidence_items     JSONB,
    ADD COLUMN IF NOT EXISTS verification_items JSONB;

-- Add index on eci_band for filtering/reporting
CREATE INDEX IF NOT EXISTS idx_investigations_eci_band
    ON investigations (eci_band)
    WHERE eci_band IS NOT NULL;

-- Add index on eci_score
CREATE INDEX IF NOT EXISTS idx_investigations_eci_score
    ON investigations (eci_score)
    WHERE eci_score IS NOT NULL;

-- ============================================================
-- END OF MIGRATION 002
-- ============================================================
