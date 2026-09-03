# RazorPulse — Synthetic Evaluation Dataset

> **Warning:** This is a small synthetic engineering benchmark (25 cases) intended for architectural validation and failure mode discovery. It is **not** statistically representative of real-world production merchant traffic.

---

## 1. Dataset Overview

The dataset consists of **25 structured evaluation cases** partitioned into:
- **Development Partition (18 cases)**: Used for initial calibration analysis and invariant testing.
- **Held-out Partition (7 cases)**: Held out to evaluate generalization on unseen cases.

Every case contains:
1. Simulated transaction anomaly context (merchant name, domain, velocity magnitude, timestamp, risk reason).
2. Pre-built `NormalizedEvidence` items with domain and source classification.
3. Pre-built `EvidenceVerificationItem` fixtures simulating Gemini structured evaluation.
4. Independent ground-truth labels: `expected_corroboration` and `expected_contradiction`.
5. Documented `contextual_hypothesis` explaining the real-world scenario tested.

---

## 2. Archetype Taxonomy (A through L)

| Archetype | Description | Total Cases | Dev | Held-out | Key Challenge |
|-----------|-------------|-------------|-----|----------|---------------|
| **A** | Strong Corroboration (multi-source news/campaign) | 3 | 2 | 1 | Multi-domain independent corroboration bonus |
| **B** | Merchant-Owned Announcement | 2 | 1 | 1 | Credible primary source but single-domain dependency |
| **C** | News-Driven Demand Surge | 1 | 0 | 1 | External catalyst (heatwave, policy change) |
| **D** | Zero / Missing Evidence | 3 | 2 | 1 | Pure zero-evidence state; provider failure fallback |
| **E** | Entity Mismatch (Similar name / brand confusion) | 2 | 2 | 0 | Brand/name collision; unrelated company |
| **F** | Temporal Mismatch (Historical / Future) | 2 | 2 | 0 | Correct merchant, wrong date (e.g. 2 years prior) |
| **G** | Post-Anomaly Event | 2 | 1 | 1 | Event occurred days after the anomaly |
| **H** | Contradiction / Official Denial | 2 | 1 | 1 | Merchant explicitly refutes sale; conflicting news |
| **I** | Duplicate Press Release Syndication | 1 | 1 | 0 | Multiple domains reproducing same PR text |
| **J** | Social-Only / Low Credibility | 2 | 2 | 0 | Unverified Reddit/Twitter claims |
| **K** | Ambiguous Evidence (Sector mention / undated) | 3 | 1 | 2 | Sector surge without merchant name; undated blog |
| **L** | Strong But Irrelevant Event | 2 | 1 | 1 | Major national holiday or UK event for Mumbai seller |

---

## 3. Case Manifest

### Development Split (18 Cases)
- `A01_strong_viral_campaign` (Type A, Easy) — Viral launch with YourStory + Economic Times + official site.
- `A02_strong_news_driven` (Type A, Easy) — NDTV + LiveMint subsidy demand rush for FreshFarm Direct.
- `A03_strong_celeb_endorsement` (Type A, Easy) — Alia Bhatt collab for GlowUp Skincare on Hindustan Times.
- `B01_merchant_official_sale` (Type B, Medium) — Official 50% thali feast on spiceroutekitchen.com.
- `D01_no_evidence_unknown_merchant` (Type D, Easy) — QuickDeal Bazaar unexplained 55x spike.
- `D03_evidence_found_but_gemini_failed` (Type D, Medium) — RapidFix Repairs with Gemini quota 429 failure.
- `E01_wrong_merchant_similar_name` (Type E, Hard) — GreenLeaf Pharmaceuticals IPO vs GreenLeaf Organics.
- `E02_wrong_merchant_partial_name` (Type E, Hard) — Nova smartphone brand vs Nova Electronics Store.
- `F01_wrong_date_historical` (Type F, Medium) — TrendWear Daily 2024 Diwali article for 2026 anomaly.
- `F02_wrong_date_future` (Type F, Medium) — WinterWear Hub sale scheduled for November vs August anomaly.
- `G01_post_anomaly_event` (Type G, Medium) — BookHaven author event scheduled 10 days post-anomaly.
- `G02_post_anomaly_launch` (Type G, Medium) — TechGadget Hub launch announced after the surge.
- `H01_merchant_refutes_sale` (Type H, Hard) — TrendWear Daily tweet citing duplicate checkout bug.
- `I01_duplicate_press_release` (Type I, Hard) — CloudNest PR syndicated across PR Newswire and BusinessWire.
- `J01_social_only_evidence` (Type J, Medium) — PixelArt Prints clearance sale discussed on Reddit.
- `J02_social_mixed_low_cred` (Type J, Medium) — ZenYoga Mats customer tweet + generic Instagram deal.
- `K01_ambiguous_merchant_mention` (Type K, Hard) — TRAI tariff rush reported without naming SwiftPay.
- `L01_strong_irrelevant_event` (Type L, Hard) — Independence Day celebrations vs PetPals grooming spike.

### Held-out Split (7 Cases)
- `B02_merchant_announcement_with_news` (Type B, Easy) — PrintWorks Studio festive launch + YourStory.
- `C01_news_driven_spike` (Type C, Medium) — Delhi record heatwave driving CoolBreeze AC rentals.
- `D02_no_evidence_niche_merchant` (Type D, Easy) — Apex Fasteners B2B spike with no web footprint.
- `H02_conflicting_sources` (Type H, Hard) — MoneyControl sale report vs MegaMart postponed notice.
- `K02_ambiguous_timing` (Type K, Medium) — BrightSmile Dental new clinic without publication date.
- `K03_moderate_single_indirect` (Type K, Medium) — Indian Express edtech enrollment rush mentioning EduLearn.
- `L02_strong_event_wrong_geography` (Type L, Hard) — UK Tea Festival in London vs Mumbai chai merchant.

---

## 4. Dataset Limitations

1. **Small Sample Size ($N=25$)**: Insufficient for high-confidence statistical margins of error.
2. **Synthetic Pre-Structured Verification**: In canonical benchmark mode, Gemini verification verdicts are mocked to preserve deterministic reproducibility without live API variance.
3. **Hard-Negative Heavy**: 52% of cases represent adversarial conditions (mismatches, denials, irrelevant events). Real production merchant traffic may have different base rate distributions.
