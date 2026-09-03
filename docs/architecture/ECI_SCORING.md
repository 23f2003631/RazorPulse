# Event Corroboration Index (ECI) — Scoring Methodology

## Strategic Definition

The **Event Corroboration Index (ECI)** measures the strength of external web evidence corroborating a real-world, legitimate explanation for an observed payment transaction anomaly.

> [!IMPORTANT]
> **ECI IS NOT A RISK SCORE.**
> ECI does NOT indicate whether a merchant is fraudulent or safe.
> A high ECI (80/100) indicates strong external evidence explaining an activity surge.
> A low ECI (0/100) indicates that no external public explanation was found; it does NOT imply fraud.
> RazorPulse provides decision-support context to human risk analysts.

---

## Evolution: ECI v1 vs. ECI v1.1

| Dimension | ECI v1 (Day 2–3) | ECI v1.1 (Day 4) |
|---|---|---|
| **Evidence Selection** | Global "best" property across all items | **Per-item eligibility assessment** |
| **Entity Mismatches** | Scored 0 on entity factor, but accrued temporal/source points (leakage: 27 pts) | **Excluded from positive contribution** with transparent audit reason (`exclusion_reason = "entity_mismatch"`) |
| **Temporal Causality** | Post-anomaly timing received 0 on temporal factor, but accrued entity points | **Explanation support zeroed** for post-anomaly / unrelated timing (events cannot causally explain prior anomalies) |
| **Source Authority** | Low-credibility social rumors accrued full entity and temporal points (inflating to 60–69) | **Per-item authority ceiling**: LOW credibility / WEAK circumstantial evidence is capped at 29 pts |
| **Independence** | Approximated solely by unique domain count | **Claim-group aware**: groups items by `evidence_group_id` (near-duplicate text fingerprinting); syndicated releases share a single group |
| **Audit Completeness** | Factor contributions only | Factor contributions + `excluded_items` list + `eligible_evidence_count` |

---

## ECI v1.1 Architecture & Pipeline

```
Verified Evidence Items
         │
    ┌────┴────────────────────────┐
    │ Per-Item Eligibility Check   │  For each item:
    │                             │  1. Entity match: UNRELATED → Ineligible (points = 0)
    │                             │  2. Temporal match: POST_ANOMALY → Explanation points = 0
    │                             │  3. Authority ceiling: LOW / WEAK → Capped at 29 pts
    └────┬────────────────────────┘
         │
    ┌────┴────────────────────────┐
    │ Partition                    │  • Eligible items (contribute to score)
    │                             │  • Excluded items (preserved for audit, contribution = 0)
    └────┬────────────────────────┘
         │
    ┌────┴────────────────────────┐
    │ Factor Aggregation          │  From eligible items only:
    │                             │  1. Entity Match (best eligible, max 25)
    │                             │  2. Temporal Alignment (best eligible, max 25)
    │                             │  3. Explanation Support (best causally-eligible, max 20)
    │                             │  4. Source Credibility (best eligible, max 20)
    │                             │  5. Independent Corroboration (distinct claim groups, max 10)
    └────┬────────────────────────┘
         │
    ┌────┴────────────────────────┐
    │ Authority Cap Reconciliation│  If all eligible items have limited authority, cap aggregate
    └────┬────────────────────────┘
         │
    ┌────┴────────────────────────┐
    │ Penalty Deductions          │  6. Contradictions (-10 to -25 pts)
    │                             │  7. Uncertainties (-6 to -12 pts)
    └────┬────────────────────────┘
         │
    ┌────┴────────────────────────┐
    │ Clamping & Band Mapping     │  ECI = clamp([0, 100], positive - penalties)
    └─────────────────────────────┘
```

---

## Factor Breakdown (v1.1)

| Dimension | Category | Max Points | Evaluation Logic |
|-----------|----------|------------|------------------|
| **1. Entity Match** | `entity_match` | **25 pts** | Direct merchant match = 25<br>Related entity (parent/partner) = 12<br>Uncertain / ambiguous = 5<br>Unrelated = 0 (and excluded from corroboration) |
| **2. Temporal Alignment** | `temporal_alignment` | **25 pts** | Exact match (0–48h of anomaly) = 25<br>Window match (within 7-day window) = 18<br>Historical previous (weeks/months prior) = 5<br>Uncertain date = 5<br>Post-anomaly / unrelated timing = 0 |
| **3. Explanation Support** | `explanation_support` | **20 pts** | Strong explanation (flash sale, viral surge, product launch) = 20<br>Moderate context = 14<br>Weak tangential mention = 6<br>Uncertain = 4<br>No explanation / post-anomaly = 0 |
| **4. Source Credibility & Directness** | `source_credibility` | **20 pts** | High Credibility + Direct Primary Evidence = 20<br>High Credibility + Indirect Reporting = 16<br>Medium Credibility + Direct/Indirect = 13<br>Low Credibility / Circumstantial = 5<br>Unknown / Unsupported = 2 |
| **5. Independent Corroboration** | `independent_corroboration` | **10 pts** | 3+ distinct claim groups = +10<br>2 distinct claim groups = +5<br>Single claim group / syndicated = +0 |
| **6. Contradiction Penalty** | `contradiction_penalty` | **-10 to -25 pts** | 2+ severe conflicts or explicit refutation = -25<br>1 minor discrepancy = -10<br>No contradictions = 0 |
| **7. Uncertainty Penalty** | `uncertainty_penalty` | **-5 to -12 pts** | High ambiguity across all items = -12<br>Moderate unresolved gaps = -6<br>Clear evidence = 0 |

---

## Qualitative Corroboration Bands

| ECI Range | Qualitative Band | Product Interpretation |
|-----------|------------------|------------------------|
| **80 – 100** | `Very Strong External Corroboration` | Discovered evidence directly, credibly, and independently corroborates a major real-world event explaining the transaction surge. |
| **60 – 79** | `Strong External Corroboration` | Discovered evidence provides strong contextual support aligned with the anomaly timeframe. |
| **30 – 59** | `Moderate External Corroboration` | Contextual evidence discovered, but exhibits minor temporal ambiguity, single-source dependency, or unverified claims. |
| **0 – 29** | `Low External Corroboration` | Little or no external public evidence found explaining the anomaly, or evidence is contradicted/unrelated. |

---

## Zero-Evidence & Ineligible-Evidence States

### Case 1: Zero Discovered / Verified Evidence
When Exa discovers zero items, or all verifications fail:
- $\text{ECI} = 0$
- `is_zero_evidence = True`
- `eligible_evidence_count = 0`
- `band = "low"`
- `band_label = "Low External Corroboration"`
- Factor states: *"No relevant external public web evidence was discovered for this merchant and timeframe."*

### Case 2: Discovered Evidence Excluded by Eligibility Gates
When evidence was discovered and verified, but all items were disqualified (e.g. all about unrelated companies):
- $\text{ECI} = 0$
- `is_zero_evidence = False`
- `eligible_evidence_count = 0`
- `excluded_items` contains detailed audit records for each excluded item
- Standard factors display 0.0 pts awarded with transparent explanations

---

## Provenance & Audit Trail (v1.1)

Every ECI calculation returns:
- `eci_score`: Integer `[0, 100]`
- `eci_version`: `"v1.1"`
- `eligible_evidence_count`: Number of verified items that passed eligibility checks
- `factors`: List of itemized factor contributions with rule IDs, point values, explanations, and citation evidence IDs
- `excluded_items`: List of `ECIExcludedItem` records detailing excluded evidence items, machine-readable reason codes, human-readable explanations, and raw scores prior to exclusion
