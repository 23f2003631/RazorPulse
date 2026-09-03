# RazorPulse — Evaluation Methodology

> **Disclaimer:** All metrics reported herein are derived from a small, synthetic engineering benchmark (25 cases total, 7 held-out cases). These results are **not statistically representative of production performance** and serve solely as an engineering baseline for component verification and failure-mode discovery.

---

## 1. Evaluation Philosophy

RazorPulse is an **external-context verification copilot** for anomalous payment-risk events. It evaluates whether public web evidence corroborates a legitimate real-world explanation for a transaction spike.

Our evaluation design enforces five core principles:

1. **Independent Dimensions**:
   - **Corroboration Classification**: How strongly external evidence corroborates an explanation (`NO`, `WEAK`, `MODERATE`, `STRONG`).
   - **Contradiction Detection**: Whether discovered sources contain factual refutations or conflicts (`PRESENT`, `ABSENT`).
   - *Contradiction is an evidence-state property, NOT inferred from a low ECI score.*

2. **Ground Truth Independence**:
   - Ground truth describes the **expected evidence state**, never target ECI numbers.
   - ECI scores are calculated by the pure Python rule engine and compared against the classification policy.
   - We do not tune weights to artificially inflate benchmark scores.

3. **Adversarial Rigor**:
   - The dataset intentionally includes hard negative archetypes: wrong merchants with similar names, outdated articles from previous years, future announcements, post-anomaly events, duplicate press release syndication, and unverified social rumors.

4. **Fixture-Only Canonical Benchmark**:
   - Canonical benchmark runs completely offline without network access, Exa calls, Gemini API calls, or Supabase.
   - Evaluates the deterministic ECI scoring engine and classification policy with 100% reproducibility.

5. **Component vs. End-to-End Separation**:
   - **ECI Engine Benchmark**: Evaluates deterministic scoring, monotonicity, and classification.
   - **Quality Gate Audit**: Evaluates pre-scoring structural and advisory checks.
   - **Live Smoke Tests**: Evaluates live Exa discovery, Gemini structured batch verification, and Supabase persistence.

---

## 2. Classification Policy

The ECI produces an integer score bounded in `[0, 100]`. The documented mapping policy translates ECI scores to corroboration classes:

| ECI Range | Corroboration Class | Semantic Description |
|-----------|---------------------|----------------------|
| **0** | `NO_CORROBORATION` | Zero verified evidence discovered, or all evidence failed verification |
| **1 – 29** | `WEAK_CORROBORATION` | Tangential, unaligned, or low-credibility external mention |
| **30 – 59** | `MODERATE_CORROBORATION` | Plausible context, single-source dependency, or minor temporal ambiguity |
| **60 – 100** | `STRONG_CORROBORATION` | Multi-source, aligned entity and timeframe, high-credibility reporting |

*Note: This mapping is a measurement policy, not a definitional identity.*

---

## 3. Evaluated Metrics

### Dimension A: Corroboration Classification (4-Class)
- **Accuracy**: Fraction of cases where predicted corroboration class equals ground truth.
- **Macro Precision**: Unweighted mean of per-class precision across classes with support.
- **Macro Recall**: Unweighted mean of per-class recall across classes with support.
- **Macro F1**: Harmonic mean of macro precision and macro recall.
- **Confusion Matrix**: Full $4 \times 4$ error matrix showing transition patterns.
- **Instability Flagging**: Any class with support $N \le 2$ is explicitly flagged as `UNSTABLE`.

### Dimension B: Contradiction Detection (Binary)
- Evaluates whether the system detects factual discrepancies when present.
- **Precision**: $\frac{\text{TP}}{\text{TP} + \text{FP}}$
- **Recall**: $\frac{\text{TP}}{\text{TP} + \text{FN}}$
- **F1**: Harmonic mean of precision and recall.

### Dimension C: Score Separation & Monotonicity
- **Central Tendency Ordering**: Mean and median ECI must increase monotonically across ground-truth classes.
- **Separation Gap**: $\text{Min}(\text{Upper}) - \text{Max}(\text{Lower})$ between adjacent classes.
- **Directional Invariants**: Formal property tests ensuring ECI does not decrease when timing, entity, or independent sources improve, and does not increase when contradictions or unrelated events are added.
