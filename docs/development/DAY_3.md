# Day 3 — Evaluation, Measurability, & Pipeline Hardening

## Overview

Day 3 transformed RazorPulse from a functioning pipeline into a **measurably characterized, rigorously benchmarked, and hardened verification system**.

In accordance with strict hackathon engineering ethics, Day 3 prioritized **measuring what RazorPulse actually does rather than making metrics look artificially good**.

---

## What Was Built

### 1. Evaluation Data Model & Independent Ground Truth
- Created `backend/evaluation/ground_truth.py`:
  - Enforces strict separation between **Corroboration Classification** (`NO`, `WEAK`, `MODERATE`, `STRONG`) and **Contradiction Detection** (`PRESENT`, `ABSENT`).
  - Decouples ground-truth evidence state from calculated ECI scores to prevent benchmark gaming.
  - Documents explicit classification policy mapping ECI integer bands to corroboration classes.

### 2. 25-Case Synthetic Evaluation Dataset
- Created `backend/evaluation/dataset.py`:
  - 25 structured test cases covering all 12 scenario archetypes (A through L).
  - 18 development cases and 7 held-out cases.
  - Heavy adversarial representation: entity mismatches (similar names, brand collisions), temporal mismatches (historical, future), post-anomaly events, explicit contradictions, duplicate press releases, social-only rumors, and irrelevant events.
  - Pre-built fixtures enable **100% offline, reproducible benchmark execution** without live API calls.

### 3. Evaluation Metrics & Benchmark Runner
- Created `backend/evaluation/metrics.py` & `backend/evaluation/runner.py`:
  - Multi-class metrics: Accuracy, Macro Precision, Macro Recall, Macro F1, and $4 \times 4$ Confusion Matrix.
  - Binary contradiction metrics: Precision, Recall, F1, TP/FP/TN/FN.
  - Automatic instability flagging for classes with small support ($N \le 2$).
  - Full per-case audit trail and human-readable reporting.

### 4. Calibration & Score Separation Analysis
- Created `backend/evaluation/calibration.py`:
  - Quantified score distribution and separation gaps across ground-truth classes.
  - Verified that ECI v1 mean scores increase **strictly monotonically** across classes: $23.6 < 51.4 < 85.7 < 96.0$.
  - Categorized 4 systemic failure modes in the additive scoring heuristic (entity leakage, temporal leakage, social inflation, single-source over-corroboration).

### 5. Evidence Quality Gates & Annotation Service
- Created `backend/app/services/evidence_quality.py`:
  - **Audit-grade non-destructive architecture**: Annotates discovered items without silently discarding evidence.
  - Hard gates: URL structure validation, source domain presence, content availability.
  - Claim-level clustering: Assigns `evidence_group_id` for duplicated/syndicated press release text.
  - Advisory relevance signal: Entity token presence is treated strictly as an advisory signal, preserving Gemini as the authoritative semantic judge.

### 6. Reproducibility & Performance Metadata
- Created `backend/app/schemas/pipeline_metadata.py`:
  - Tracks `pipeline_version` ("0.3.0"), `eci_version` ("v1"), `search_strategy_version` ("v1"), `verification_prompt_version` ("v1"), and exact `gemini_model`.
  - Captures high-resolution stage timings (`searching`, `verifying`, `scoring`, `dossier`, `persistence`).
  - Embedded in `EvidenceDossier` and persisted in Supabase `investigations.dossier` JSONB column.

### 7. Analyst Checklist with Evidence ID Citations
- Upgraded `backend/app/services/investigation/dossier_generator.py`:
  - Review items now explicitly reference citation markers (e.g. `[E1] (economictimes.indiatimes.com)`).
  - Specific guidance generated for temporal ambiguity, entity uncertainty, identified contradictions, single-source reliance, and syndicated claim clusters.

### 8. Deterministic Demonstration Scenarios
- Created `backend/evaluation/demo_scenarios.py` & `backend/scripts/run_demo.py`:
  - 3 representative scenarios: Festive surge (`UrbanCraft India`, 100/100), Zero evidence (`QuickDeal Bazaar`, 0/100), and Contradicted sale (`TrendWear Daily`, 33/100).
  - Designed around semantic expected behavior rather than hard-coded score targets.

### 9. Test Suite Expansion (128 Passing Tests)
- Grew test suite from 98 to **128 automated tests (100% passing)**:
  - 6 new Directional Invariant / Monotonicity tests (`test_eci_monotonicity.py`).
  - 6 new Evaluation Dataset validation tests (`test_evaluation_dataset.py`).
  - 7 new Statistical Metrics calculation tests (`test_evaluation_metrics.py`).
  - 5 new Evidence Quality Gate tests (`test_evidence_quality.py`).
  - 2 new Pipeline Metadata schema tests (`test_pipeline_metadata.py`).
  - 4 new Demo Scenario execution tests (`test_demo_scenarios.py`).

---

## Benchmark Results Snapshot

```
========================================================================
RAZORPULSE EVALUATION BENCHMARK REPORT (HELD-OUT SPLIT: 7 CASES)
========================================================================
Corroboration Accuracy:       0.4286 (3/7)
Macro Precision:              0.4167
Macro Recall:                 0.3333
Macro F1:                     0.3000
Contradiction Detection F1:   1.0000 (P: 1.00, R: 1.00)
Monotonic Score Progression:  no (27.3) < weak (48.0) < mod (80.0) < strong (95.0)
========================================================================
```

> **Engineering Takeaway:** While ECI v1 perfectly distinguishes contradiction and orders corroboration strength monotonically, additive point accumulation without entity gating causes entity-mismatched articles to score 27 points instead of 0. Day 4 will address this with targeted gating rules.
