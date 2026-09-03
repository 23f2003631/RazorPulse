# Day 4 — Evidence Quality, Corroboration Reliability & Benchmark Hardening

## Overview & Mission

Day 4 focused on upgrading the core deterministic corroboration pipeline from **ECI v1 → ECI v1.1**, directly resolving the four primary failure modes identified in Day 3 evaluation:
1. **Entity Mismatch Leakage**: Articles about unrelated merchants accrued temporal and source points.
2. **Temporal Directionality Errors**: Post-anomaly events accrued explanation support points.
3. **Social-Only ECI Inflation**: Low-authority social rumors scored into the 60s (Strong band).
4. **Single-Source Over-Corroboration**: Syndicated copies of press releases inflated the independent corroboration bonus.

In accordance with strict hackathon engineering ethics and user architectural guidance:
- **No benchmark overfitting**: Rules operate at the principled evidence-item level, not on case IDs or merchant names.
- **No arbitrary multipliers**: We rejected arbitrary numerical damping factors (e.g. $0.65\times$) in favor of clean semantic distinctions (direct evidence vs. independent corroboration).
- **No global gates**: Gating rules evaluate evidence items independently; an unrelated item never invalidates valid evidence in the same investigation.
- **Audit completeness**: Every excluded item is preserved with an explicit machine-readable reason code and human-readable explanation.

---

## Key Accomplishments

### 1. Schema Extensions for Audit Traceability
- Added `ECIExcludedItem` to `backend/app/schemas/eci.py`:
  - Captures `evidence_id`, `exclusion_reason`, `explanation`, and `raw_contribution`.
- Added `ECIFactorCategory.GATING_EXCLUSION` for transparent reporting of gate actions.
- Added `excluded_items: list[ECIExcludedItem]` and `eligible_evidence_count: int` to `ECIScoreResult`.

### 2. ECI v1.1 Scoring Engine
- Implemented in `backend/app/services/scoring/eci_engine.py`:
  - **Per-item entity gating**: Items with `merchant_match == UNRELATED` contribute 0 points and are recorded in `excluded_items`.
  - **Per-item temporal causality gating**: Items with `temporal_match in (POST_ANOMALY, UNRELATED_TIMING)` have their explanation support contribution forced to 0 (cannot causally explain preceding anomaly).
  - **Per-item source authority ceiling**: Low-credibility sources (`SourceCredibilityLevel.LOW` or `EvidenceStrength.WEAK_CIRCUMSTANTIAL` or `UNKNOWN`) are capped at 29 ECI points (the ceiling of the Low/Weak corroboration band).
  - **Claim-group aware independence**: Connects `EvidenceQualityService.annotate_collection`'s near-duplicate text fingerprinting (`evidence_group_id`). Syndicated copies of the same release share a claim group and yield 0 extra independence bonus.
  - **Standard factor preservation**: Zero-eligible investigations still provide the 5 standard positive factors with 0.0 pts awarded and explicit explanations.

### 3. Pipeline Integration
- Integrated `evidence_group_ids` from quality gates into:
  - `backend/app/services/investigation/orchestrator.py` (Investigation orchestrator)
  - `backend/evaluation/runner.py` (Benchmark runner)

### 4. Comprehensive Test Suite Expansion (148 Total Tests)
- **Isolated Gating Tests** (`backend/tests/unit/test_eci_v1_1_gating.py`):
  - 4 Entity gating tests (unrelated, direct match, related entity, uncertain)
  - 4 Temporal gating tests (post-anomaly, unrelated timing, exact match, window match)
  - 4 Source authority ceiling tests (low cred cap, high cred uncapped, unknown cap, contradicted zero)
  - 3 Claim-group independence tests (3 distinct groups = +10, 3 syndicated = 0, 2 distinct = +5)
- **Mixed-Evidence Tests** (`backend/tests/unit/test_eci_v1_1_mixed_evidence.py`):
  - `Mix-A`: Valid + Unrelated evidence (isolation verified)
  - `Mix-B`: Valid + Low-quality social (no global capping)
  - `Mix-C`: Pre-anomaly + Post-anomaly (temporal isolation)
  - `Mix-D`: Original + Syndicated copies (claim group independence)
  - `Mix-E`: Valid + Ambiguous entity (no reduction of confirmed match)
- **All 128 existing tests pass with 0 failures** (148 total passing tests, 100%).

---

## Benchmark Results (v1 vs. v1.1)

| Scope | Metric | ECI v1 | ECI v1.1 | Delta |
|---|---|---|---|---|
| **Full Benchmark ($N=25$)** | Corroboration Accuracy | 32.00% (8/25) | **60.00% (15/25)** | **+28.00%** |
| | Macro F1 | 0.2667 | **0.5015** | **+0.2348** |
| | Contradiction F1 | 1.0000 | **1.0000** | 0.0000 (preserved) |
| **Held-Out Split ($N=7$)** | Corroboration Accuracy | 42.86% (3/7) | **57.14% (4/7)** | **+14.28%** |
| | Macro F1 | 0.3000 | **0.4000** | **+0.1000** |
| | Contradiction F1 | 1.0000 | **1.0000** | 0.0000 (preserved) |
| **Development Split ($N=18$)** | Corroboration Accuracy | 27.78% (5/18) | **61.11% (11/18)** | **+33.33%** |
| | Macro F1 | 0.2409 | **0.5025** | **+0.2616** |
| | Contradiction F1 | 1.0000 | **1.0000** | 0.0000 (preserved) |

### Transition Summary:
- **7 cases fixed**: `E01`, `E02`, `F01`, `J01`, `J02`, `L01`, `L02`
- **8 cases unchanged (correct)**: `A01`, `A02`, `A03`, `B02`, `C01`, `D01`, `D02`, `D03`
- **0 cases regressed**: Zero regressions across all 25 cases.
- **10 remaining failures**: Fully documented with architectural root causes in `docs/evaluation/RESULTS.md`.

---

## Score Separation (v1.1)

Mean ECI scores strictly follow monotonic progression across ground-truth classes:
$$\text{NO } (11.0) < \text{WEAK } (34.6) < \text{MODERATE } (82.3) < \text{STRONG } (96.0)$$

Median ECI for `no_corroboration` dropped from **27 -> 0**, successfully eliminating false positive corroboration for unrelated merchant events.
