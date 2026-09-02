# Event Corroboration Index (ECI) — Scoring Methodology (v1 Heuristic)

## Strategic Definition

The **Event Corroboration Index (ECI)** measures the strength of external web evidence corroborating a real-world, legitimate explanation for an observed payment transaction anomaly.

> [!IMPORTANT]
> **ECI IS NOT A RISK SCORE.**
> ECI does NOT indicate whether a merchant is fraudulent or safe.
> A high ECI (80/100) indicates strong external evidence explaining an activity surge.
> A low ECI (0/100) indicates that no external public explanation was found; it does NOT imply fraud.
> RazorPulse provides decision-support context to human risk analysts.

---

## ECI v1 Heuristic Formula

The ECI v1 is a deterministic rule-based calculation strictly bounded to `[0, 100]`:

$$\text{ECI} = \text{clamp}_{[0, 100]} \left( \sum \text{Positive Factors} - \sum \text{Penalty Deductions} \right)$$

---

## Factor Breakdown

| Dimension | Category | Max Points | Evaluation Logic |
|-----------|----------|------------|------------------|
| **1. Entity Match** | `entity_match` | **25 pts** | Direct merchant match = 25<br>Related entity (parent/partner) = 12<br>Uncertain / ambiguous = 5<br>Unrelated = 0 |
| **2. Temporal Alignment** | `temporal_alignment` | **25 pts** | Exact match (0–48h of anomaly) = 25<br>Window match (within 7-day window) = 18<br>Historical previous (weeks/months prior) = 5<br>Uncertain date = 5<br>Post-anomaly / unrelated timing = 0 |
| **3. Explanation Support** | `explanation_support` | **20 pts** | Strong explanation (flash sale, product launch, viral surge) = 20<br>Moderate context = 14<br>Weak tangential mention = 6<br>Uncertain = 4<br>No explanation = 0 |
| **4. Source Credibility & Directness** | `source_credibility` | **20 pts** | High Credibility + Direct Primary Evidence = 20<br>High Credibility + Indirect Reporting = 16<br>Medium Credibility + Direct/Indirect = 13<br>Low Credibility / Circumstantial = 5<br>Unknown / Unsupported = 2 |
| **5. Independent Corroboration** | `independent_corroboration` | **10 pts** | 3+ distinct independent domains = +10<br>2 distinct independent domains = +5<br>Single domain = +0 |
| **6. Contradiction Penalty** | `contradiction_penalty` | **-10 to -30 pts** | 2+ severe conflicts or explicit refutation = -25<br>1 minor discrepancy = -10<br>No contradictions = 0 |
| **7. Uncertainty Penalty** | `uncertainty_penalty` | **-5 to -15 pts** | Pervasive ambiguity across all items = -12<br>Moderate unresolved gaps = -6<br>Clear evidence = 0 |

---

## Qualitative Corroboration Bands

| ECI Range | Qualitative Band | Product Interpretation |
|-----------|------------------|------------------------|
| **80 – 100** | `Very Strong External Corroboration` | Discovered evidence directly, credibly, and independently corroborates a major real-world event explaining the transaction surge. |
| **60 – 79** | `Strong External Corroboration` | Discovered evidence provides strong contextual support aligned with the anomaly timeframe. |
| **30 – 59** | `Moderate External Corroboration` | Contextual evidence discovered, but exhibits minor temporal ambiguity, single-source dependency, or unverified claims. |
| **0 – 29** | `Low External Corroboration` | Little or no external public evidence found explaining the anomaly, or evidence is contradicted/unrelated. |

---

## Zero-Evidence State

When no external evidence is discovered:
- $\text{ECI} = 0$
- `is_zero_evidence = True`
- `band = "low"`
- `band_label = "Low External Corroboration (Zero Evidence)"`
- Itemized factor explicitly states: *"No relevant external public web evidence was discovered for this merchant and timeframe."*

---

## Provenance & Traceability

Every ECI factor contribution returns:
- `factor_id`: Machine-readable rule ID
- `name`: Title of the factor
- `raw_value`: Underlying evaluated attribute
- `points_awarded`: Points added or subtracted
- `explanation`: Traceable justification
- `evidence_ids`: UUIDs of the contributing evidence items
