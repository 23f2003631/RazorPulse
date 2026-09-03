# RazorPulse — Evaluation Benchmark Results (v1 vs. v1.1)

> **Essential Disclaimer:** The following results are measured on a **small synthetic engineering benchmark** (7 held-out cases, 18 development cases, 25 total). These numbers do **NOT** represent real-world production accuracy on live Razorpay traffic. Per-class metrics with 1–2 examples are statistically unstable and are reported for architectural transparency and failure mode discovery.

---

## 1. Executive Summary: ECI v1 vs. ECI v1.1

| Metric | Full Benchmark ($N=25$) | Held-out Partition ($N=7$) | Development Partition ($N=18$) |
|--------|-------------------------|----------------------------|--------------------------------|
| **v1 Corroboration Accuracy** | **32.00%** (8/25) | **42.86%** (3/7) | **27.78%** (5/18) |
| **v1.1 Corroboration Accuracy** | **60.00%** (15/25) | **57.14%** (4/7) | **61.11%** (11/18) |
| **Absolute Improvement** | **+28.00%** | **+14.28%** | **+33.33%** |
| **v1 Macro F1 Score** | 0.2667 | 0.3000 | 0.2409 |
| **v1.1 Macro F1 Score** | **0.5015** | **0.4000** | **0.5025** |
| **v1 Contradiction Detection F1** | **1.0000** (P: 1.0, R: 1.0) | **1.0000** (P: 1.0, R: 1.0) | **1.0000** (P: 1.0, R: 1.0) |
| **v1.1 Contradiction Detection F1** | **1.0000** (P: 1.0, R: 1.0) | **1.0000** (P: 1.0, R: 1.0) | **1.0000** (P: 1.0, R: 1.0) |
| **Score Monotonicity** | **Strictly Monotonic** | **Strictly Monotonic** | **Strictly Monotonic** |

---

## 2. Held-Out Benchmark Performance ($N=7$)

The held-out partition represents our primary generalization measurement. It was evaluated only after v1.1 scoring rules were frozen.

### Dimension A: Corroboration Classification (4-Class)

| Ground-Truth Class | Precision | Recall | F1 | Support ($N$) | Stability Flag |
|---|---|---|---|---|---|
| `no_corroboration` | 1.0000 | 0.6667 | 0.8000 | 3 | Stable |
| `weak_corroboration` | 0.0000 | 0.0000 | 0.0000 | 1 | `UNSTABLE` ($N=1$) |
| `moderate_corroboration` | 0.0000 | 0.0000 | 0.0000 | 1 | `UNSTABLE` ($N=1$) |
| `strong_corroboration` | 0.6667 | 1.0000 | 0.8000 | 2 | `UNSTABLE` ($N=2$) |

#### Held-Out Confusion Matrix (v1.1)
```
Predicted →     no_corro  weak_cor  moderate  strong_c
True ↓
no_corroboration       2         0         1         0
weak_corroboration     0         0         1         0
moderate_corroboration 0         0         0         1
strong_corroboration   0         0         0         2
```
*Note: In v1, `no_corroboration` was 1 correct (1/3). In v1.1, it is 2 correct (2/3), as Case `L02` was correctly classified as `no_corroboration` (ECI 0) due to entity mismatch gating.*

### Dimension B: Binary Contradiction Detection (Held-Out)

- **Precision:** 1.0000
- **Recall:** 1.0000
- **F1 Score:** 1.0000
- **True Positives:** 1 | **False Positives:** 0 | **True Negatives:** 6 | **False Negatives:** 0
- *Support:* 1 Present, 6 Absent (`UNSTABLE` due to single positive example in held-out split).

---

## 3. Development Benchmark Performance ($N=18$)

| Ground-Truth Class | Precision | Recall | F1 | Support ($N$) | Stability Flag |
|---|---|---|---|---|---|
| `no_corroboration` | 1.0000 | 0.5556 | 0.7143 | 9 | Stable |
| `weak_corroboration` | 0.4286 | 0.7500 | 0.5455 | 4 | Stable |
| `moderate_corroboration` | 0.0000 | 0.0000 | 0.0000 | 2 | `UNSTABLE` ($N=2$) |
| `strong_corroboration` | 0.6000 | 1.0000 | 0.7500 | 3 | Stable |

#### Development Confusion Matrix (v1.1)
```
Predicted →     no_corro  weak_cor  moderate  strong_c
True ↓
no_corroboration       5         4         0         0
weak_corroboration     0         3         1         0
moderate_corroboration 0         0         0         2
strong_corroboration   0         0         0         3
```

---

## 4. Score Separation Analysis (All 25 Cases)

| Ground-Truth Class | Count | v1 Mean ECI | v1.1 Mean ECI | v1.1 Median | v1.1 Min | v1.1 Max | Score Distribution (v1.1) |
|---|---|---|---|---|---|---|---|
| `no_corroboration` | 12 | 23.6 | **11.0** | **0** | 0 | 55 | `[0, 0, 0, 0, 0, 0, 0, 4, 15, 29, 29, 55]` |
| `weak_corroboration` | 5 | 51.4 | **34.6** | **29** | 19 | 48 | `[19, 29, 29, 48, 48]` |
| `moderate_corroboration` | 3 | 85.7 | **82.3** | **80** | 77 | 90 | `[77, 80, 90]` |
| `strong_corroboration` | 5 | 96.0 | **96.0** | **95** | 95 | 100 | `[95, 95, 95, 95, 100]` |

### Key Observations:
1. **Strict Monotonic Central Tendency**: Mean scores strictly increase across classes ($11.0 < 34.6 < 82.3 < 96.0$).
2. **Substantial Compression of False Positives**: In v1, 75% of `no_corroboration` cases received $\ge 27$ ECI. In v1.1, the median `no_corroboration` score dropped to **0**, with 7 of 12 cases scoring exactly 0.
3. **Social Inflation Deflated**: In v1, cases `J01` and `J02` scored 69 and 61 (STRONG). In v1.1, both score **29 (LOW / WEAK)**, matching their ground truth.

---

## 5. Regression & Case-Level Comparison Analysis

### Summary of Transitions (v1 → v1.1):
- **Fixed:** **7 cases**
- **Unchanged (Correct):** **8 cases**
- **Unchanged (Remaining Failures):** **10 cases**
- **Regressed:** **0 cases** (Zero regressions across all 25 benchmark cases)

### Detailed Case Transitions:

| Case ID | Archetype | Expected Class | v1 ECI | v1 Class | v1.1 ECI | v1.1 Class | Outcome | Architectural Cause |
|---|---|---|---|---|---|---|---|---|
| `A01_strong_viral_campaign` | A | STRONG | 100 | STRONG | 100 | STRONG | UNCHANGED | Multi-source verified campaign |
| `A02_strong_news_driven` | A | STRONG | 95 | STRONG | 95 | STRONG | UNCHANGED | High credibility news media |
| `A03_strong_celeb_endorsement` | A | STRONG | 95 | STRONG | 95 | STRONG | UNCHANGED | Direct endorsement coverage |
| `B01_merchant_official_sale` | B | MODERATE | 90 | STRONG | 90 | STRONG | REMAINING | Single merchant announcement; direct evidence strength high |
| `B02_merchant_announcement_with_news` | B | STRONG | 95 | STRONG | 95 | STRONG | UNCHANGED | Merchant + news confirmation |
| `C01_news_driven_spike` | C | STRONG | 95 | STRONG | 95 | STRONG | UNCHANGED | Industry heatwave demand context |
| `D01_no_evidence_unknown_merchant` | D | NO | 0 | NO | 0 | NO | UNCHANGED | Zero evidence discovery |
| `D02_no_evidence_niche_merchant` | D | NO | 0 | NO | 0 | NO | UNCHANGED | Zero evidence discovery |
| `D03_evidence_found_but_gemini_failed` | D | NO | 0 | NO | 0 | NO | UNCHANGED | Zero verified evidence graceful path |
| `E01_wrong_merchant_similar_name` | E | NO | 27 | WEAK | 0 | NO | **FIXED** | Entity mismatch gate excluded item |
| `E02_wrong_merchant_partial_name` | E | NO | 27 | WEAK | 0 | NO | **FIXED** | Entity mismatch gate excluded item |
| `F01_wrong_date_historical` | F | WEAK | 31 | MODERATE | 19 | WEAK | **FIXED** | Historical timing points properly bounded |
| `F02_wrong_date_future` | F | NO | 27 | WEAK | 15 | WEAK | REMAINING | Direct entity match awards 25 - uncertainties |
| `G01_post_anomaly_event` | G | NO | 30 | MODERATE | 29 | WEAK | REMAINING | Explanation zeroed; entity match retains 25 pts |
| `G02_post_anomaly_launch` | G | NO | 30 | MODERATE | 29 | WEAK | REMAINING | Explanation zeroed; entity match retains 25 pts |
| `H01_merchant_refutes_sale` | H | NO | 33 | MODERATE | 4 | WEAK | REMAINING | Contradiction penalty reduced score from 33 to 4 |
| `H02_conflicting_sources` | H | NO | 55 | MODERATE | 55 | MODERATE | REMAINING | News + refutation creates mixed evidence |
| `I01_duplicate_press_release` | I | MODERATE | 87 | STRONG | 77 | STRONG | REMAINING | Reduced by 10 pts (no independence bonus), but direct evidence still 77 |
| `J01_social_only_evidence` | J | WEAK | 69 | STRONG | 29 | WEAK | **FIXED** | Source authority ceiling capped at 29 |
| `J02_social_mixed_low_cred` | J | WEAK | 61 | STRONG | 29 | WEAK | **FIXED** | Source authority ceiling capped at 29 |
| `K01_ambiguous_merchant_mention` | K | WEAK | 48 | MODERATE | 48 | MODERATE | REMAINING | Ambiguous mention scored in moderate band |
| `K02_ambiguous_timing` | K | WEAK | 48 | MODERATE | 48 | MODERATE | REMAINING | Ambiguous timing scored in moderate band |
| `K03_moderate_single_indirect` | K | MODERATE | 80 | STRONG | 80 | STRONG | REMAINING | Single indirect source scored in strong band |
| `L01_strong_irrelevant_event` | L | NO | 27 | WEAK | 0 | NO | **FIXED** | Entity mismatch gate excluded item |
| `L02_strong_event_wrong_geography` | L | NO | 27 | WEAK | 0 | NO | **FIXED** | Entity mismatch gate excluded item |

---

## 6. Analysis of Remaining 10 Failure Modes

1. **Entity Point Residual in Wrong-Timeframe Cases (4 cases: `F02`, `G01`, `G02`, `H01`)**:
   - In these cases, the merchant entity was confirmed (`DIRECT_MATCH` = 25 pts), but timing was future, post-anomaly, or refuted. While v1.1 successfully zeroed explanation support, the entity match factor alone awarded 25 pts (placing the score in `1–29`, which maps to `WEAK_CORROBORATION` instead of `NO_CORROBORATION`).
   - *Design Decision*: Entity points reflect factual identification ("we found the merchant"). The policy choice of whether $1–29$ is called "Weak Corroboration" or "Context Discovered Without Explanation" is a taxonomy decision, not an engine error.

2. **Direct Evidence Ceiling in Single/Duplicate Cases (3 cases: `B01`, `I01`, `K03`)**:
   - In `I01`, claim-group deduplication successfully eliminated the +10 independent corroboration bonus (reducing score from 87 to 77). However, because the press release contained strong promotional detail, the direct factors still summed to 77.
   - We intentionally did **NOT** apply an arbitrary 0.65 multiplier to force these cases into the `moderate` band, preserving principled scoring over artificial benchmark tuning.

3. **Ambiguity Band Alignment (2 cases: `K01`, `K02`)**:
   - Cases with partial/ambiguous mentions currently receive 48 points, crossing into the lower range of `MODERATE` (30–59) rather than `WEAK` (1–29).

4. **Conflicting Sources with Refutation (1 case: `H02`)**:
   - Both a positive news story and an official merchant refutation exist. Contradiction detection identified the conflict with 100% precision. The ECI score reflects both perspectives rather than forcing one to zero.
