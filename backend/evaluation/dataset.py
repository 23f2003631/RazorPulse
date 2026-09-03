"""
RazorPulse Synthetic Evaluation Dataset — 25 Labeled Cases.

Contains 25 deterministic benchmark cases spanning all 12 scenario archetypes (A–L).
Each case includes pre-built evidence fixtures and verification fixtures so the
benchmark runs WITHOUT external API calls (no Exa, no Gemini, no network).

Split: 18 development cases, 7 held-out cases (deterministic, documented).

LIMITATIONS (must be stated in all evaluation reports):
  - This is a SMALL SYNTHETIC ENGINEERING BENCHMARK.
  - It is NOT statistically representative of production performance.
  - Per-class metrics with 1–2 held-out examples are UNSTABLE and must be flagged.
  - Results should be reported as "on the synthetic held-out benchmark."

DESIGN PRINCIPLES:
  - Ground truth labels describe expected EVIDENCE STATE, not target ECI scores.
  - Difficult/adversarial cases are included intentionally (wrong merchant, wrong date, etc.).
  - The dataset is NOT designed to make RazorPulse look good.
"""

from uuid import UUID, uuid4

from app.schemas.evidence import NormalizedEvidence, SourceType
from app.schemas.verification import (
    EvidenceStrength,
    EvidenceVerificationItem,
    ExplanationSupportLevel,
    MerchantMatchLevel,
    SourceCredibilityLevel,
    TemporalMatchLevel,
    VerificationStatus,
)
from evaluation.ground_truth import (
    ContradictionState,
    CorroborationClass,
    DatasetSplit,
    DifficultyLevel,
    EvalCase,
)


def _uid() -> UUID:
    """Generate a deterministic-style UUID for fixtures."""
    return uuid4()


# =============================================================================
# TYPE A — STRONG CORROBORATION: Clear multi-source verified events
# =============================================================================

CASE_A01 = EvalCase(
    case_id="A01_strong_viral_campaign",
    archetype="A",
    description="Multiple credible independent sources report a viral product launch matching the anomaly timing exactly.",
    difficulty=DifficultyLevel.EASY,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="UrbanCraft India",
    merchant_domain="urbancraft.in",
    occurred_at="2026-08-28T14:30:00+05:30",
    baseline_transaction_count=85,
    observed_transaction_count=1450,
    percentage_change=1605.88,
    risk_reason="Transaction velocity increased 17x above baseline over 3 hours.",
    geographic_info="Bengaluru, Karnataka, IN",
    evidence_items=[
        NormalizedEvidence(
            url="https://yourstory.com/2026/08/urbancraft-india-viral-handicraft-sale",
            title="UrbanCraft India's Heritage Collection Goes Viral on Social Media",
            source_domain="yourstory.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-28T11:00:00Z",
            content_snippet="UrbanCraft India launched its nationwide artisan festive collection today, generating over 100,000 visitors within hours following celebrity endorsements.",
            highlights=["festive collection launch", "over 100,000 visitors in hours"],
            discovery_query='"UrbanCraft India" sale launch viral', discovery_query_intent="commercial_campaign",
            external_score=0.92,
        ),
        NormalizedEvidence(
            url="https://economictimes.indiatimes.com/industry/services/retail/urbancraft-records-record-surge/articleshow/998877.cms",
            title="D2C Brand UrbanCraft Records Massive Surge During Festive Flash Sale",
            source_domain="economictimes.indiatimes.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-28T16:00:00Z",
            content_snippet="Artisan D2C platform UrbanCraft India saw orders surge 15-20x on Friday afternoon after kicking off its annual mega discount drive.",
            highlights=["orders surge 15-20x", "annual mega discount drive"],
            discovery_query='"UrbanCraft India" news August 2026', discovery_query_intent="timeframe_event",
            external_score=0.88,
        ),
        NormalizedEvidence(
            url="https://urbancraft.in/pages/festive-sale-2026",
            title="Official Announcement: Festive Artisan Sale 2026",
            source_domain="urbancraft.in", source_type=SourceType.MERCHANT_OFFICIAL,
            published_at="2026-08-28T09:00:00Z",
            content_snippet="Welcome to UrbanCraft India's Annual Artisan Festive Sale! Enjoy up to 60% off across all handmade categories starting August 28.",
            highlights=["Annual Artisan Festive Sale", "starting August 28"],
            discovery_query="site:urbancraft.in launch OR sale OR announcement", discovery_query_intent="merchant_announcement",
            external_score=0.95,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=101), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            event_category="viral_campaign",
            key_facts=["Festive collection launch on August 28", "Viral surge with 100k visitors"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="Article directly reports massive demand surge for UrbanCraft India on the exact anomaly date."),
        EvidenceVerificationItem(evidence_id=UUID(int=102), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            event_category="flash_sale",
            key_facts=["15-20x order surge recorded on Friday afternoon"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="Economic Times confirms 15-20x order surge matching transaction velocity spike."),
        EvidenceVerificationItem(evidence_id=UUID(int=103), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            event_category="merchant_announcement",
            key_facts=["Official festive sale began August 28"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="Merchant official domain confirms planned nationwide sale starting August 28."),
    ],
    expected_corroboration=CorroborationClass.STRONG_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="A merchant launches a product and several independent credible sources report it around the anomaly period.",
)

CASE_A02 = EvalCase(
    case_id="A02_strong_news_driven",
    archetype="A",
    description="Major news event drives demand for a specific merchant, confirmed by 2 independent news sources.",
    difficulty=DifficultyLevel.EASY,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="FreshFarm Direct",
    merchant_domain="freshfarmdirect.in",
    occurred_at="2026-09-01T10:00:00+05:30",
    baseline_transaction_count=200,
    observed_transaction_count=2400,
    percentage_change=1100.0,
    risk_reason="12x velocity increase over 4 hours.",
    geographic_info="Pune, Maharashtra, IN",
    evidence_items=[
        NormalizedEvidence(
            url="https://ndtv.com/food/freshfarm-direct-organic-rush-2026",
            title="FreshFarm Direct sees organic food rush after government subsidy announcement",
            source_domain="ndtv.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-09-01T08:00:00Z",
            content_snippet="Organic food delivery platform FreshFarm Direct reported unprecedented order volumes today following the Union Agriculture Ministry's announcement of a 40% subsidy on organic produce purchases.",
            highlights=["unprecedented order volumes", "40% subsidy on organic produce"],
            discovery_query='"FreshFarm Direct" news September 2026', discovery_query_intent="timeframe_event",
            external_score=0.91,
        ),
        NormalizedEvidence(
            url="https://livemint.com/industry/retail/organic-food-orders-spike",
            title="Organic food platforms see order spikes after subsidy news",
            source_domain="livemint.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-09-01T12:00:00Z",
            content_snippet="Multiple organic food platforms including FreshFarm Direct and GreenBasket reported 10-15x normal order volumes after the subsidy announcement.",
            highlights=["10-15x normal order volumes", "subsidy announcement"],
            discovery_query='"FreshFarm Direct" surge demand', discovery_query_intent="commercial_campaign",
            external_score=0.85,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=201), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["40% subsidy on organic produce", "unprecedented order volumes"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="NDTV directly reports FreshFarm Direct order surge following government subsidy."),
        EvidenceVerificationItem(evidence_id=UUID(int=202), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.MODERATE_INDIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["10-15x order volumes", "subsidy announcement triggered demand"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="LiveMint independently confirms surge across organic platforms including FreshFarm Direct."),
    ],
    expected_corroboration=CorroborationClass.STRONG_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="External event (government policy) creates plausible demand increase confirmed by multiple independent news sources.",
)

# =============================================================================
# TYPE B — MERCHANT-OWNED ANNOUNCEMENT (Strong/Moderate)
# =============================================================================

CASE_B01 = EvalCase(
    case_id="B01_merchant_official_sale",
    archetype="B",
    description="Merchant's official website announces a major campaign exactly around the anomaly. Single merchant-owned source.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="SpiceRoute Kitchen",
    merchant_domain="spiceroutekitchen.com",
    occurred_at="2026-08-25T18:00:00+05:30",
    baseline_transaction_count=60,
    observed_transaction_count=480,
    percentage_change=700.0,
    risk_reason="8x transaction velocity spike during evening hours.",
    evidence_items=[
        NormalizedEvidence(
            url="https://spiceroutekitchen.com/independence-day-feast-2026",
            title="Independence Day Grand Feast — 50% Off All Thalis",
            source_domain="spiceroutekitchen.com", source_type=SourceType.MERCHANT_OFFICIAL,
            published_at="2026-08-25T10:00:00Z",
            content_snippet="Celebrate Independence Week with SpiceRoute Kitchen! Get 50% off all regional thali combos from August 25–31.",
            highlights=["50% off all thalis", "August 25–31"],
            discovery_query="site:spiceroutekitchen.com sale OR announcement", discovery_query_intent="merchant_announcement",
            external_score=0.90,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=301), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["50% off regional thali combos", "August 25-31 campaign"],
            contradictions_identified=[], uncertainties_noted=["Single merchant-owned source; no independent external confirmation."],
            reasoning_summary="Official merchant website confirms a large-scale promotion starting on the anomaly date."),
    ],
    expected_corroboration=CorroborationClass.MODERATE_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Merchant-owned announcement is credible but lacks independent external corroboration, resulting in moderate rather than strong.",
)

# =============================================================================
# TYPE C — NEWS-DRIVEN SPIKE (Moderate/Strong)
# =============================================================================

CASE_C01 = EvalCase(
    case_id="C01_news_driven_spike",
    archetype="C",
    description="External event creates plausible demand increase. Entity and timing align.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.HELD_OUT,
    merchant_name="CoolBreeze AC Rentals",
    merchant_domain="coolbreezerentals.in",
    occurred_at="2026-07-15T12:00:00+05:30",
    baseline_transaction_count=30,
    observed_transaction_count=350,
    percentage_change=1066.0,
    risk_reason="Sudden 11x velocity spike during midday.",
    geographic_info="Delhi NCR, IN",
    evidence_items=[
        NormalizedEvidence(
            url="https://hindustantimes.com/weather/delhi-heatwave-record-july-2026",
            title="Delhi records highest July temperature in 50 years",
            source_domain="hindustantimes.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-07-15T06:00:00Z",
            content_snippet="Delhi recorded 47.2°C on July 15, the highest July temperature in five decades. Demand for cooling appliances has surged across the NCR region.",
            highlights=["47.2°C on July 15", "demand for cooling appliances surged"],
            discovery_query='"CoolBreeze" OR "cooling" Delhi July 2026', discovery_query_intent="timeframe_event",
            external_score=0.78,
        ),
        NormalizedEvidence(
            url="https://coolbreezerentals.in/summer-emergency-offer",
            title="Emergency Summer Cooling Offer — CoolBreeze",
            source_domain="coolbreezerentals.in", source_type=SourceType.MERCHANT_OFFICIAL,
            published_at="2026-07-15T09:00:00Z",
            content_snippet="Due to extreme heat, CoolBreeze is offering same-day AC installation at discounted rates across Delhi NCR.",
            highlights=["same-day AC installation", "extreme heat"],
            discovery_query="site:coolbreezerentals.in", discovery_query_intent="merchant_announcement",
            external_score=0.88,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=401), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.RELATED_ENTITY, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
            evidence_strength=EvidenceStrength.MODERATE_INDIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Record heatwave in Delhi", "Cooling appliance demand surge"],
            contradictions_identified=[], uncertainties_noted=["Article mentions cooling appliances generally, does not name CoolBreeze directly."],
            reasoning_summary="Heatwave news explains demand surge for cooling services but does not name CoolBreeze specifically."),
        EvidenceVerificationItem(evidence_id=UUID(int=402), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Same-day AC installation offer", "Response to extreme heat"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="Merchant official page confirms emergency promotion in response to heatwave."),
    ],
    expected_corroboration=CorroborationClass.STRONG_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="External news event (heatwave) plus merchant response creates strong corroboration despite one source being indirect.",
)

# =============================================================================
# TYPE D — NO EVIDENCE
# =============================================================================

CASE_D01 = EvalCase(
    case_id="D01_no_evidence_unknown_merchant",
    archetype="D",
    description="Large anomaly but no external evidence exists whatsoever.",
    difficulty=DifficultyLevel.EASY,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="QuickDeal Bazaar",
    merchant_domain="quickdealbazaar.com",
    occurred_at="2026-08-30T02:15:00+05:30",
    baseline_transaction_count=40,
    observed_transaction_count=2200,
    percentage_change=5400.0,
    risk_reason="Extreme velocity spike at 2:15 AM IST (55x baseline).",
    geographic_info="New Delhi, Delhi, IN",
    evidence_items=[],
    verification_items=[],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Extreme anomaly with zero external evidence. ECI should be exactly 0.",
)

CASE_D02 = EvalCase(
    case_id="D02_no_evidence_niche_merchant",
    archetype="D",
    description="Niche B2B merchant with no public presence. Exa finds nothing.",
    difficulty=DifficultyLevel.EASY,
    split=DatasetSplit.HELD_OUT,
    merchant_name="Apex Industrial Fasteners",
    merchant_domain="apexfasteners.co.in",
    occurred_at="2026-08-20T09:00:00+05:30",
    baseline_transaction_count=15,
    observed_transaction_count=180,
    percentage_change=1100.0,
    risk_reason="12x velocity increase for niche B2B merchant.",
    evidence_items=[],
    verification_items=[],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="B2B niche merchant with no public web presence. Zero evidence expected.",
)

# =============================================================================
# TYPE E — WRONG MERCHANT (Entity Mismatch)
# =============================================================================

CASE_E01 = EvalCase(
    case_id="E01_wrong_merchant_similar_name",
    archetype="E",
    description="Evidence describes a different company with a similar name.",
    difficulty=DifficultyLevel.HARD,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="GreenLeaf Organics",
    merchant_domain="greenleaforganics.in",
    occurred_at="2026-08-15T14:00:00+05:30",
    baseline_transaction_count=50,
    observed_transaction_count=600,
    percentage_change=1100.0,
    risk_reason="12x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://bloomberg.com/news/greenleaf-pharma-ipo-2026",
            title="GreenLeaf Pharmaceuticals IPO opens to strong demand",
            source_domain="bloomberg.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-15T10:00:00Z",
            content_snippet="GreenLeaf Pharmaceuticals, a Mumbai-based drug manufacturer, opened its IPO today to strong institutional demand.",
            highlights=["GreenLeaf Pharmaceuticals IPO", "strong institutional demand"],
            discovery_query='"GreenLeaf" news August 2026', discovery_query_intent="timeframe_event",
            external_score=0.72,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=501), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.UNRELATED, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.UNSUPPORTED, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["GreenLeaf Pharmaceuticals IPO — different company"],
            contradictions_identified=[], uncertainties_noted=["Entity mismatch: GreenLeaf Pharmaceuticals ≠ GreenLeaf Organics"],
            reasoning_summary="Evidence refers to GreenLeaf Pharmaceuticals, an unrelated entity to GreenLeaf Organics."),
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Similar name but completely different company. Entity mismatch must produce zero corroboration.",
)

CASE_E02 = EvalCase(
    case_id="E02_wrong_merchant_partial_name",
    archetype="E",
    description="Evidence mentions a parent brand but the actual merchant is an unrelated small seller using a similar name.",
    difficulty=DifficultyLevel.HARD,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="Nova Electronics Store",
    merchant_domain="novaelectronicsstore.in",
    occurred_at="2026-09-02T16:00:00+05:30",
    baseline_transaction_count=20,
    observed_transaction_count=300,
    percentage_change=1400.0,
    risk_reason="15x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://techcrunch.com/2026/09/nova-smartphone-launch",
            title="Nova launches flagship smartphone in India",
            source_domain="techcrunch.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-09-02T08:00:00Z",
            content_snippet="Smartphone brand Nova today launched its Nova X1 Pro in India with a ₹15,999 introductory price.",
            highlights=["Nova X1 Pro launch", "₹15,999 introductory price"],
            discovery_query='"Nova" electronics news September 2026', discovery_query_intent="timeframe_event",
            external_score=0.80,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=601), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.UNRELATED, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.UNSUPPORTED, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Nova X1 Pro smartphone launch"],
            contradictions_identified=[], uncertainties_noted=["Nova smartphone brand ≠ Nova Electronics Store"],
            reasoning_summary="Evidence refers to Nova smartphone brand, not Nova Electronics Store reseller."),
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Prominent brand name collision. Correct entity match should prevent false corroboration.",
)

# =============================================================================
# TYPE F — WRONG DATE (Temporal Mismatch)
# =============================================================================

CASE_F01 = EvalCase(
    case_id="F01_wrong_date_historical",
    archetype="F",
    description="Evidence about the correct merchant but from months/years ago.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="TrendWear Daily",
    merchant_domain="trendweardaily.in",
    occurred_at="2026-08-29T18:00:00+05:30",
    baseline_transaction_count=50,
    observed_transaction_count=400,
    percentage_change=700.0,
    risk_reason="Sudden 8x velocity spike on Saturday evening.",
    evidence_items=[
        NormalizedEvidence(
            url="https://inc42.com/buzz/trendwear-daily-diwali-campaign-2024",
            title="TrendWear Daily Gears Up for Diwali 2024 with Flash Deals",
            source_domain="inc42.com", source_type=SourceType.INDUSTRY_PORTAL,
            published_at="2024-10-15T10:00:00Z",
            content_snippet="Apparel startup TrendWear Daily announced heavy discounts for Diwali 2024, running exclusive sales across India.",
            highlights=["Diwali 2024 flash deals"],
            discovery_query='"TrendWear Daily" sale campaign', discovery_query_intent="commercial_campaign",
            external_score=0.65,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=701), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.HISTORICAL_PREVIOUS,
            explanation_support=ExplanationSupportLevel.WEAK_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL, source_credibility=SourceCredibilityLevel.MEDIUM,
            key_facts=["Diwali 2024 flash deals campaign"],
            contradictions_identified=["Article relates to 2024, nearly 2 years before the observed 2026 anomaly."],
            uncertainties_noted=["Timing is completely disconnected from August 2026."],
            reasoning_summary="Historical article from 2024 cannot explain an August 2026 transaction spike."),
    ],
    overall_contradictions=["Article relates to 2024, nearly 2 years before the observed 2026 anomaly."],
    expected_corroboration=CorroborationClass.WEAK_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_PRESENT,
    contextual_hypothesis="Correct merchant, wrong date. Temporal mismatch should severely limit corroboration.",
)

# =============================================================================
# TYPE G — POST-ANOMALY EVENT
# =============================================================================

CASE_G01 = EvalCase(
    case_id="G01_post_anomaly_event",
    archetype="G",
    description="External event occurred days after the anomaly. Cannot explain the spike.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="BookHaven Online",
    merchant_domain="bookhaven.co.in",
    occurred_at="2026-08-10T09:00:00+05:30",
    baseline_transaction_count=70,
    observed_transaction_count=560,
    percentage_change=700.0,
    risk_reason="8x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://publishersweekly.com/bookhaven-author-event-2026",
            title="BookHaven announces major author signing event",
            source_domain="publishersweekly.com", source_type=SourceType.INDUSTRY_PORTAL,
            published_at="2026-08-18T10:00:00Z",
            content_snippet="BookHaven Online announced a major virtual author signing event for August 20–22, featuring bestselling Indian authors.",
            highlights=["author signing event August 20-22"],
            discovery_query='"BookHaven" news August 2026', discovery_query_intent="timeframe_event",
            external_score=0.70,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=801), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.POST_ANOMALY,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL, source_credibility=SourceCredibilityLevel.MEDIUM,
            key_facts=["Author signing event scheduled for August 20-22"],
            contradictions_identified=[], uncertainties_noted=["Event is 10 days after the anomaly on August 10."],
            reasoning_summary="Post-anomaly event cannot explain transaction spike that occurred on August 10."),
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Post-anomaly event. Correct merchant but wrong temporal direction.",
)

# =============================================================================
# TYPE H — CONTRADICTION
# =============================================================================

CASE_H01 = EvalCase(
    case_id="H01_merchant_refutes_sale",
    archetype="H",
    description="Merchant's official statement explicitly refutes a flash sale. Contradicts other evidence.",
    difficulty=DifficultyLevel.HARD,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="TrendWear Daily",
    merchant_domain="trendweardaily.in",
    occurred_at="2026-08-29T18:00:00+05:30",
    baseline_transaction_count=50,
    observed_transaction_count=400,
    percentage_change=700.0,
    risk_reason="Sudden 8x velocity spike on Saturday evening.",
    evidence_items=[
        NormalizedEvidence(
            url="https://inc42.com/buzz/trendwear-daily-diwali-campaign-2024",
            title="TrendWear Daily Gears Up for Diwali 2024 with Flash Deals",
            source_domain="inc42.com", source_type=SourceType.INDUSTRY_PORTAL,
            published_at="2024-10-15T10:00:00Z",
            content_snippet="Apparel startup TrendWear Daily announced heavy discounts for Diwali 2024.",
            highlights=["Diwali 2024 flash deals"],
            discovery_query='"TrendWear Daily" sale campaign', discovery_query_intent="commercial_campaign",
            external_score=0.65,
        ),
        NormalizedEvidence(
            url="https://twitter.com/trendweardaily/status/1829000000000000000",
            title="TrendWear Daily Official Support Notice",
            source_domain="twitter.com", source_type=SourceType.SOCIAL_COMMUNITY,
            published_at="2026-08-29T18:30:00Z",
            content_snippet="Notice to customers: We are experiencing a technical bug causing duplicate checkout requests. No flash sale or promotional discount is currently active.",
            highlights=["technical bug causing duplicate checkout", "No flash sale is currently active"],
            discovery_query='"TrendWear Daily" news August 2026', discovery_query_intent="timeframe_event",
            external_score=0.85,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=901), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.HISTORICAL_PREVIOUS,
            explanation_support=ExplanationSupportLevel.WEAK_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL, source_credibility=SourceCredibilityLevel.MEDIUM,
            key_facts=["Diwali sale occurred in October 2024"],
            contradictions_identified=["Article relates to 2024, not August 2026."],
            uncertainties_noted=["Timing is completely disconnected from August 2026."],
            reasoning_summary="Historical article from 2024 cannot explain August 2026 spike."),
        EvidenceVerificationItem(evidence_id=UUID(int=902), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.CONTRADICTED, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Technical bug causing duplicate checkouts", "No flash sale active"],
            contradictions_identified=["Merchant explicitly refutes flash sale — cites technical malfunction."],
            uncertainties_noted=[],
            reasoning_summary="Merchant directly refutes commercial promotion and cites checkout bug."),
    ],
    overall_contradictions=[
        "Article relates to 2024, not August 2026.",
        "Merchant explicitly refutes flash sale — cites technical malfunction.",
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_PRESENT,
    contextual_hypothesis="Evidence contains explicit contradiction from the merchant. ECI should be heavily penalized.",
)

CASE_H02 = EvalCase(
    case_id="H02_conflicting_sources",
    archetype="H",
    description="Two credible sources provide conflicting accounts of the same event.",
    difficulty=DifficultyLevel.HARD,
    split=DatasetSplit.HELD_OUT,
    merchant_name="MegaMart Express",
    merchant_domain="megamartexpress.in",
    occurred_at="2026-08-22T15:00:00+05:30",
    baseline_transaction_count=120,
    observed_transaction_count=900,
    percentage_change=650.0,
    risk_reason="7.5x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://moneycontrol.com/megamart-flash-sale-aug-2026",
            title="MegaMart Express announces Independence Day mega sale",
            source_domain="moneycontrol.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-22T10:00:00Z",
            content_snippet="MegaMart Express launched its Independence Day mega sale with up to 70% discounts.",
            highlights=["Independence Day mega sale", "up to 70% discounts"],
            discovery_query='"MegaMart Express" August 2026', discovery_query_intent="timeframe_event",
            external_score=0.82,
        ),
        NormalizedEvidence(
            url="https://megamartexpress.in/press-release/sale-postponed",
            title="Official Notice: Sale Postponed to September",
            source_domain="megamartexpress.in", source_type=SourceType.MERCHANT_OFFICIAL,
            published_at="2026-08-22T14:00:00Z",
            content_snippet="Due to supply chain disruptions, MegaMart Express has postponed its Independence Day sale to September 1. No promotional discounts are currently active.",
            highlights=["sale postponed to September", "No promotional discounts currently active"],
            discovery_query="site:megamartexpress.in announcement", discovery_query_intent="merchant_announcement",
            external_score=0.90,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1001), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
            evidence_strength=EvidenceStrength.MODERATE_INDIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Independence Day mega sale launched"],
            contradictions_identified=["Merchant official page says sale was postponed."],
            uncertainties_noted=[],
            reasoning_summary="News reports sale launch but merchant says it was postponed."),
        EvidenceVerificationItem(evidence_id=UUID(int=1002), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.CONTRADICTED, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Sale postponed to September", "No discounts active"],
            contradictions_identified=["Merchant says sale postponed, contradicting news report."],
            uncertainties_noted=[],
            reasoning_summary="Merchant official notice directly contradicts the news report of a live sale."),
    ],
    overall_contradictions=[
        "Merchant official page says sale was postponed.",
        "Merchant says sale postponed, contradicting news report.",
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_PRESENT,
    contextual_hypothesis="Conflicting sources: news says sale is live, merchant says it's postponed. Contradiction should be detected.",
)

# =============================================================================
# TYPE I — DUPLICATE REPORTING (Independence inflation)
# =============================================================================

CASE_I01 = EvalCase(
    case_id="I01_duplicate_press_release",
    archetype="I",
    description="Multiple sites reproduce the same press release. Should NOT inflate corroboration as if independent.",
    difficulty=DifficultyLevel.HARD,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="CloudNest Solutions",
    merchant_domain="cloudnest.io",
    occurred_at="2026-08-18T11:00:00+05:30",
    baseline_transaction_count=25,
    observed_transaction_count=200,
    percentage_change=700.0,
    risk_reason="8x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://prnewswire.com/cloudnest-enterprise-launch",
            title="CloudNest Solutions Launches Enterprise Tier",
            source_domain="prnewswire.com", source_type=SourceType.PRESS_RELEASE,
            published_at="2026-08-18T08:00:00Z",
            content_snippet="CloudNest Solutions today announced the launch of its Enterprise tier, offering advanced cloud infrastructure at competitive pricing.",
            highlights=["Enterprise tier launch", "advanced cloud infrastructure"],
            discovery_query='"CloudNest" launch announcement', discovery_query_intent="commercial_campaign",
            external_score=0.75,
        ),
        NormalizedEvidence(
            url="https://businesswire.com/cloudnest-enterprise-launch",
            title="CloudNest Solutions Launches Enterprise Tier",
            source_domain="businesswire.com", source_type=SourceType.PRESS_RELEASE,
            published_at="2026-08-18T08:00:00Z",
            content_snippet="CloudNest Solutions today announced the launch of its Enterprise tier, offering advanced cloud infrastructure at competitive pricing.",
            highlights=["Enterprise tier launch", "advanced cloud infrastructure"],
            discovery_query='"CloudNest" news August 2026', discovery_query_intent="timeframe_event",
            external_score=0.73,
        ),
        NormalizedEvidence(
            url="https://techstartups.com/cloudnest-enterprise-tier",
            title="CloudNest Rolls Out Enterprise Cloud Tier",
            source_domain="techstartups.com", source_type=SourceType.INDUSTRY_PORTAL,
            published_at="2026-08-18T09:00:00Z",
            content_snippet="CloudNest Solutions today announced the launch of its Enterprise tier, offering advanced cloud infrastructure at competitive pricing. [via PR Newswire]",
            highlights=["Enterprise tier launch"],
            discovery_query='"CloudNest" news August 2026', discovery_query_intent="timeframe_event",
            external_score=0.68,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1101), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
            evidence_strength=EvidenceStrength.MODERATE_INDIRECT, source_credibility=SourceCredibilityLevel.MEDIUM,
            key_facts=["Enterprise tier launch announced"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="PR Newswire distribution of enterprise launch announcement."),
        EvidenceVerificationItem(evidence_id=UUID(int=1102), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
            evidence_strength=EvidenceStrength.MODERATE_INDIRECT, source_credibility=SourceCredibilityLevel.MEDIUM,
            key_facts=["Enterprise tier launch announced"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="BusinessWire distribution of the same press release."),
        EvidenceVerificationItem(evidence_id=UUID(int=1103), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL, source_credibility=SourceCredibilityLevel.LOW,
            key_facts=["Enterprise tier launch — sourced from PR Newswire"],
            contradictions_identified=[], uncertainties_noted=["Content is republished PR, not independent reporting."],
            reasoning_summary="Aggregator site republishing PR Newswire content."),
    ],
    expected_corroboration=CorroborationClass.MODERATE_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Multiple domains but one underlying claim. Independent corroboration bonus should be limited. Documented limitation: independent domains are an approximation of independent corroboration.",
)

# =============================================================================
# TYPE J — SOCIAL-ONLY EVIDENCE
# =============================================================================

CASE_J01 = EvalCase(
    case_id="J01_social_only_evidence",
    archetype="J",
    description="Only low-authority social/community evidence exists. No news or official sources.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="PixelArt Prints",
    merchant_domain="pixelartprints.com",
    occurred_at="2026-08-12T20:00:00+05:30",
    baseline_transaction_count=35,
    observed_transaction_count=280,
    percentage_change=700.0,
    risk_reason="8x velocity spike in evening hours.",
    evidence_items=[
        NormalizedEvidence(
            url="https://reddit.com/r/IndianArt/comments/pixelart-prints-sale",
            title="r/IndianArt - PixelArt Prints is doing a massive clearance sale",
            source_domain="reddit.com", source_type=SourceType.SOCIAL_COMMUNITY,
            published_at="2026-08-12T18:00:00Z",
            content_snippet="Just saw PixelArt Prints is doing 70% off everything. Grabbed two canvas prints. Anyone else buying?",
            highlights=["70% off everything", "clearance sale"],
            discovery_query='"PixelArt Prints" sale', discovery_query_intent="commercial_campaign",
            external_score=0.55,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1201), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL, source_credibility=SourceCredibilityLevel.LOW,
            key_facts=["Reddit post mentions 70% off clearance sale"],
            contradictions_identified=[], uncertainties_noted=["Single unverified user post; cannot confirm sale authenticity."],
            reasoning_summary="Social media post mentions merchant sale but lacks official confirmation."),
    ],
    expected_corroboration=CorroborationClass.WEAK_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Social-only evidence with low credibility. Corroboration should be limited.",
)

# =============================================================================
# TYPE K — AMBIGUOUS EVIDENCE
# =============================================================================

CASE_K01 = EvalCase(
    case_id="K01_ambiguous_merchant_mention",
    archetype="K",
    description="Evidence is related to the merchant's sector but cannot establish a direct connection.",
    difficulty=DifficultyLevel.HARD,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="SwiftPay Recharge",
    merchant_domain="swiftpayrecharge.in",
    occurred_at="2026-08-05T14:00:00+05:30",
    baseline_transaction_count=500,
    observed_transaction_count=3000,
    percentage_change=500.0,
    risk_reason="6x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://economictimes.indiatimes.com/telecom-recharge-rush-august-2026",
            title="Telecom recharge volumes surge as new TRAI tariff rules take effect",
            source_domain="economictimes.indiatimes.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-05T07:00:00Z",
            content_snippet="Telecom recharge platforms across India saw elevated volumes as customers rushed to prepay before new TRAI pricing kicks in on August 6.",
            highlights=["elevated recharge volumes", "TRAI pricing changes August 6"],
            discovery_query='"recharge" surge August 2026', discovery_query_intent="timeframe_event",
            external_score=0.65,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1301), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.UNCERTAIN, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
            evidence_strength=EvidenceStrength.MODERATE_INDIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["TRAI tariff changes driving recharge rush"],
            contradictions_identified=[], uncertainties_noted=["Article does not mention SwiftPay Recharge specifically."],
            reasoning_summary="Industry-wide recharge surge reported but SwiftPay Recharge not named."),
    ],
    expected_corroboration=CorroborationClass.WEAK_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Industry-level event is plausible but merchant is not directly identified. Ambiguity should limit corroboration.",
)

CASE_K02 = EvalCase(
    case_id="K02_ambiguous_timing",
    archetype="K",
    description="Evidence mentions the merchant but the event timing is ambiguous — could be before or after anomaly.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.HELD_OUT,
    merchant_name="BrightSmile Dental",
    merchant_domain="brightsmiledental.in",
    occurred_at="2026-08-01T10:00:00+05:30",
    baseline_transaction_count=40,
    observed_transaction_count=240,
    percentage_change=500.0,
    risk_reason="6x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://brightsmiledental.in/blog/new-clinic-opening",
            title="BrightSmile Dental Opening New Clinic in Hyderabad",
            source_domain="brightsmiledental.in", source_type=SourceType.MERCHANT_OFFICIAL,
            content_snippet="BrightSmile Dental is excited to announce a new clinic in Hyderabad! Grand opening specials available.",
            highlights=["new clinic in Hyderabad", "grand opening specials"],
            discovery_query="site:brightsmiledental.in announcement", discovery_query_intent="merchant_announcement",
            external_score=0.80,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1401), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.UNCERTAIN,
            explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
            evidence_strength=EvidenceStrength.MODERATE_INDIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["New clinic opening in Hyderabad", "Grand opening specials"],
            contradictions_identified=[], uncertainties_noted=["No publication date available; cannot confirm temporal alignment."],
            reasoning_summary="Merchant announces new clinic but publication date is missing, preventing temporal verification."),
    ],
    expected_corroboration=CorroborationClass.WEAK_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Correct merchant but undated evidence. Temporal uncertainty should limit corroboration.",
)

# =============================================================================
# TYPE L — STRONG BUT IRRELEVANT EVENT
# =============================================================================

CASE_L01 = EvalCase(
    case_id="L01_strong_irrelevant_event",
    archetype="L",
    description="Major event exists but has no meaningful relationship to the merchant.",
    difficulty=DifficultyLevel.HARD,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="PetPals Grooming",
    merchant_domain="petpalsgrooming.in",
    occurred_at="2026-08-15T12:00:00+05:30",
    baseline_transaction_count=25,
    observed_transaction_count=250,
    percentage_change=900.0,
    risk_reason="10x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://ndtv.com/india/independence-day-celebrations-2026",
            title="India Celebrates 80th Independence Day with Grand Parades",
            source_domain="ndtv.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-15T06:00:00Z",
            content_snippet="India celebrated its 80th Independence Day with grand military parades and cultural events across the country.",
            highlights=["80th Independence Day", "grand military parades"],
            discovery_query='"August 15" event India 2026', discovery_query_intent="timeframe_event",
            external_score=0.90,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1501), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.UNRELATED, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.UNSUPPORTED, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Independence Day celebrations nationwide"],
            contradictions_identified=[], uncertainties_noted=["National holiday has no meaningful connection to pet grooming services."],
            reasoning_summary="Independence Day is a major event but has no causal connection to pet grooming demand."),
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Major event exists on the exact date but is completely irrelevant to the merchant's business.",
)

CASE_L02 = EvalCase(
    case_id="L02_strong_event_wrong_geography",
    archetype="L",
    description="Merchant is in India, event is in a different country.",
    difficulty=DifficultyLevel.HARD,
    split=DatasetSplit.HELD_OUT,
    merchant_name="ChaiPoint Express",
    merchant_domain="chaipointexpress.in",
    occurred_at="2026-08-20T08:00:00+05:30",
    baseline_transaction_count=80,
    observed_transaction_count=640,
    percentage_change=700.0,
    risk_reason="8x velocity spike in morning hours.",
    geographic_info="Mumbai, Maharashtra, IN",
    evidence_items=[
        NormalizedEvidence(
            url="https://bbc.com/news/uk-tea-festival-2026",
            title="UK Tea Festival 2026 breaks attendance records",
            source_domain="bbc.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-20T06:00:00Z",
            content_snippet="The UK Tea Festival 2026 in London broke attendance records with 50,000 visitors on its opening day.",
            highlights=["UK Tea Festival", "50,000 visitors"],
            discovery_query='"tea" festival August 2026', discovery_query_intent="timeframe_event",
            external_score=0.60,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1601), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.UNRELATED, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.UNSUPPORTED, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["UK Tea Festival in London"],
            contradictions_identified=[], uncertainties_noted=["Event is in London, merchant operates in Mumbai."],
            reasoning_summary="UK event cannot explain demand spike for an Indian chai merchant."),
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Thematically related but geographically irrelevant. Should produce no corroboration.",
)

# =============================================================================
# ADDITIONAL DEVELOPMENT CASES — Fill out difficult scenarios
# =============================================================================

CASE_A03 = EvalCase(
    case_id="A03_strong_celeb_endorsement",
    archetype="A",
    description="Celebrity endorsement drives viral traffic, confirmed by news and merchant.",
    difficulty=DifficultyLevel.EASY,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="GlowUp Skincare",
    merchant_domain="glowupskincare.in",
    occurred_at="2026-09-01T14:00:00+05:30",
    baseline_transaction_count=100,
    observed_transaction_count=1200,
    percentage_change=1100.0,
    risk_reason="12x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://hindustantimes.com/entertainment/glowup-celeb-launch",
            title="Bollywood star launches GlowUp Skincare collab collection",
            source_domain="hindustantimes.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-09-01T10:00:00Z",
            content_snippet="Bollywood actress Alia Bhatt launched a limited-edition skincare collection with GlowUp Skincare, driving massive online traffic.",
            highlights=["Alia Bhatt collab", "limited-edition collection"],
            discovery_query='"GlowUp Skincare" launch September 2026', discovery_query_intent="timeframe_event",
            external_score=0.93,
        ),
        NormalizedEvidence(
            url="https://glowupskincare.in/alia-collab",
            title="GlowUp x Alia Bhatt — Limited Edition Collection",
            source_domain="glowupskincare.in", source_type=SourceType.MERCHANT_OFFICIAL,
            published_at="2026-09-01T08:00:00Z",
            content_snippet="Introducing the GlowUp x Alia Bhatt collection. Available September 1 only while stocks last.",
            highlights=["limited edition", "September 1 only"],
            discovery_query="site:glowupskincare.in launch", discovery_query_intent="merchant_announcement",
            external_score=0.95,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1701), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Celebrity collaboration launch", "massive online traffic"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="News confirms celebrity-driven demand surge on exact anomaly date."),
        EvidenceVerificationItem(evidence_id=UUID(int=1702), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Limited edition collection September 1"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="Merchant official page confirms the launch."),
    ],
    expected_corroboration=CorroborationClass.STRONG_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Celebrity endorsement with dual independent sources. Clear strong corroboration.",
)

CASE_D03 = EvalCase(
    case_id="D03_evidence_found_but_gemini_failed",
    archetype="D",
    description="Evidence was discovered but all Gemini verifications failed due to quota. Should be NO corroboration.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="RapidFix Repairs",
    merchant_domain="rapidfixrepairs.in",
    occurred_at="2026-08-25T16:00:00+05:30",
    baseline_transaction_count=30,
    observed_transaction_count=300,
    percentage_change=900.0,
    risk_reason="10x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://yourstory.com/rapidfix-expansion-2026",
            title="RapidFix Repairs Expands to 10 New Cities",
            source_domain="yourstory.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-25T10:00:00Z",
            content_snippet="RapidFix Repairs announced expansion to 10 new cities across India.",
            highlights=["expansion to 10 new cities"],
            discovery_query='"RapidFix" news August 2026', discovery_query_intent="timeframe_event",
            external_score=0.80,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1801), status=VerificationStatus.FAILED,
            failure_reason="429 ResourceExhausted: GenerateRequestsPerDay quota exceeded",
            reasoning_summary="Gemini verification failed due to quota exhaustion."),
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Evidence exists but verification failed. ECI must be 0 — cannot claim corroboration without verification.",
)

CASE_F02 = EvalCase(
    case_id="F02_wrong_date_future",
    archetype="F",
    description="Evidence about the correct merchant but for a future sale not yet active.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="WinterWear Hub",
    merchant_domain="winterwearhub.in",
    occurred_at="2026-08-10T14:00:00+05:30",
    baseline_transaction_count=20,
    observed_transaction_count=200,
    percentage_change=900.0,
    risk_reason="10x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://winterwearhub.in/blog/winter-sale-preview",
            title="WinterWear Hub — Winter Sale 2026 Preview",
            source_domain="winterwearhub.in", source_type=SourceType.MERCHANT_OFFICIAL,
            published_at="2026-08-01T10:00:00Z",
            content_snippet="Get ready for WinterWear Hub's biggest sale yet! Starting November 1, 2026.",
            highlights=["biggest sale yet", "Starting November 1 2026"],
            discovery_query="site:winterwearhub.in sale", discovery_query_intent="merchant_announcement",
            external_score=0.70,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=1901), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.UNRELATED_TIMING,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.UNSUPPORTED, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Winter sale starts November 1, not August"],
            contradictions_identified=[], uncertainties_noted=["Sale is scheduled for November, not August."],
            reasoning_summary="Merchant sale is 3 months in the future. Cannot explain August anomaly."),
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Correct merchant, but sale is months in the future. Should produce no meaningful corroboration.",
)

CASE_J02 = EvalCase(
    case_id="J02_social_mixed_low_cred",
    archetype="J",
    description="Two social media posts — one mentions the merchant, one is ambiguous. Both low credibility.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="ZenYoga Mats",
    merchant_domain="zenyogamats.com",
    occurred_at="2026-08-08T08:00:00+05:30",
    baseline_transaction_count=15,
    observed_transaction_count=150,
    percentage_change=900.0,
    risk_reason="10x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://twitter.com/yogalover123/status/fake123",
            title="@yogalover123 tweet about ZenYoga Mats",
            source_domain="twitter.com", source_type=SourceType.SOCIAL_COMMUNITY,
            published_at="2026-08-08T07:00:00Z",
            content_snippet="Just bought 3 yoga mats from ZenYoga Mats for my studio. Great International Yoga Day deal!",
            highlights=["ZenYoga Mats deal", "International Yoga Day"],
            discovery_query='"ZenYoga Mats" sale', discovery_query_intent="commercial_campaign",
            external_score=0.45,
        ),
        NormalizedEvidence(
            url="https://instagram.com/p/fake456",
            title="Instagram post about yoga mats",
            source_domain="instagram.com", source_type=SourceType.SOCIAL_COMMUNITY,
            published_at="2026-08-08T09:00:00Z",
            content_snippet="Yoga mat deals everywhere today! #yogaday #deals",
            highlights=["yoga mat deals"],
            discovery_query='"yoga mats" sale August 2026', discovery_query_intent="commercial_campaign",
            external_score=0.35,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=2001), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.WEAK_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL, source_credibility=SourceCredibilityLevel.LOW,
            key_facts=["User bought 3 mats from ZenYoga"],
            contradictions_identified=[], uncertainties_noted=["Unverified social media user."],
            reasoning_summary="Single user tweet mentioning purchase from ZenYoga Mats."),
        EvidenceVerificationItem(evidence_id=UUID(int=2002), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.UNCERTAIN, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.WEAK_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL, source_credibility=SourceCredibilityLevel.LOW,
            key_facts=["Generic yoga mat deals trending"],
            contradictions_identified=[], uncertainties_noted=["Does not mention ZenYoga Mats by name."],
            reasoning_summary="Generic Instagram post about yoga mat deals, no merchant identification."),
    ],
    expected_corroboration=CorroborationClass.WEAK_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Social-only evidence with low credibility. One mentions merchant, one doesn't. Limited corroboration.",
)

CASE_B02 = EvalCase(
    case_id="B02_merchant_announcement_with_news",
    archetype="B",
    description="Merchant announcement corroborated by one independent news source.",
    difficulty=DifficultyLevel.EASY,
    split=DatasetSplit.HELD_OUT,
    merchant_name="PrintWorks Studio",
    merchant_domain="printworksstudio.in",
    occurred_at="2026-08-28T10:00:00+05:30",
    baseline_transaction_count=45,
    observed_transaction_count=540,
    percentage_change=1100.0,
    risk_reason="12x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://printworksstudio.in/launch/new-collection",
            title="PrintWorks Studio — New Festive Collection Launch",
            source_domain="printworksstudio.in", source_type=SourceType.MERCHANT_OFFICIAL,
            published_at="2026-08-28T06:00:00Z",
            content_snippet="Introducing our new festive season collection! Available from August 28 with launch-day special pricing.",
            highlights=["new festive collection", "August 28 launch"],
            discovery_query="site:printworksstudio.in launch", discovery_query_intent="merchant_announcement",
            external_score=0.92,
        ),
        NormalizedEvidence(
            url="https://yourstory.com/2026/08/printworks-studio-festive-launch",
            title="PrintWorks Studio launches festive collection",
            source_domain="yourstory.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-08-28T12:00:00Z",
            content_snippet="D2C brand PrintWorks Studio has launched a new festive season collection, seeing strong initial demand.",
            highlights=["festive collection launch", "strong initial demand"],
            discovery_query='"PrintWorks Studio" news August 2026', discovery_query_intent="timeframe_event",
            external_score=0.85,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=2101), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.STRONG_DIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Festive collection August 28", "launch-day pricing"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="Merchant official page confirms launch on anomaly date."),
        EvidenceVerificationItem(evidence_id=UUID(int=2102), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
            evidence_strength=EvidenceStrength.MODERATE_INDIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Festive collection launch", "strong initial demand"],
            contradictions_identified=[], uncertainties_noted=[],
            reasoning_summary="Independent news source confirms merchant launch and demand."),
    ],
    expected_corroboration=CorroborationClass.STRONG_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Merchant announcement plus independent news confirmation. Should be strong corroboration.",
)

CASE_G02 = EvalCase(
    case_id="G02_post_anomaly_launch",
    archetype="G",
    description="Merchant announces a product launch after the anomaly date.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.DEVELOPMENT,
    merchant_name="TechGadget Hub",
    merchant_domain="techgadgethub.in",
    occurred_at="2026-08-05T10:00:00+05:30",
    baseline_transaction_count=60,
    observed_transaction_count=420,
    percentage_change=600.0,
    risk_reason="7x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://techgadgethub.in/upcoming-launch",
            title="TechGadget Hub — New Product Line Coming August 15",
            source_domain="techgadgethub.in", source_type=SourceType.MERCHANT_OFFICIAL,
            published_at="2026-08-08T10:00:00Z",
            content_snippet="Exciting new product line launching August 15! Pre-orders opening soon.",
            highlights=["new product line August 15", "pre-orders"],
            discovery_query="site:techgadgethub.in launch", discovery_query_intent="merchant_announcement",
            external_score=0.75,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=2201), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.POST_ANOMALY,
            explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
            evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["Product launch August 15 — after anomaly on August 5"],
            contradictions_identified=[], uncertainties_noted=["Launch is 10 days after the anomaly."],
            reasoning_summary="Post-anomaly launch announcement cannot explain August 5 transaction spike."),
    ],
    expected_corroboration=CorroborationClass.NO_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Correct merchant, post-anomaly event. Temporal direction is wrong.",
)

# =============================================================================
# ADDITIONAL HELD-OUT CASE — Moderate corroboration
# =============================================================================

CASE_K03 = EvalCase(
    case_id="K03_moderate_single_indirect",
    archetype="K",
    description="One credible news source mentions the merchant indirectly in a broader industry article.",
    difficulty=DifficultyLevel.MEDIUM,
    split=DatasetSplit.HELD_OUT,
    merchant_name="EduLearn Plus",
    merchant_domain="edulearnplus.in",
    occurred_at="2026-07-01T09:00:00+05:30",
    baseline_transaction_count=150,
    observed_transaction_count=750,
    percentage_change=400.0,
    risk_reason="5x velocity spike.",
    evidence_items=[
        NormalizedEvidence(
            url="https://indianexpress.com/education/edtech-enrollment-surge-july-2026",
            title="EdTech platforms see enrollment surge as new academic year begins",
            source_domain="indianexpress.com", source_type=SourceType.NEWS_MEDIA,
            published_at="2026-07-01T06:00:00Z",
            content_snippet="EdTech platforms including EduLearn Plus, Byju's, and Unacademy reported increased enrollments as the new academic session commenced on July 1.",
            highlights=["EduLearn Plus reported increased enrollments", "new academic session"],
            discovery_query='"EduLearn Plus" news July 2026', discovery_query_intent="timeframe_event",
            external_score=0.78,
        ),
    ],
    verification_items=[
        EvidenceVerificationItem(evidence_id=UUID(int=2301), status=VerificationStatus.VERIFIED,
            merchant_match=MerchantMatchLevel.DIRECT_MATCH, temporal_match=TemporalMatchLevel.EXACT_MATCH,
            explanation_support=ExplanationSupportLevel.MODERATE_EXPLANATION,
            evidence_strength=EvidenceStrength.MODERATE_INDIRECT, source_credibility=SourceCredibilityLevel.HIGH,
            key_facts=["EduLearn Plus mentioned among platforms with enrollment surge"],
            contradictions_identified=[], uncertainties_noted=["Merchant mentioned alongside others; not the focus of the article."],
            reasoning_summary="Credible news source mentions EduLearn Plus in industry enrollment surge report."),
    ],
    expected_corroboration=CorroborationClass.MODERATE_CORROBORATION,
    expected_contradiction=ContradictionState.CONTRADICTION_ABSENT,
    contextual_hypothesis="Single credible source mentions merchant in industry context. Moderate corroboration — not strong due to lack of independence.",
)


# =============================================================================
# DATASET ASSEMBLY
# =============================================================================

ALL_CASES: list[EvalCase] = [
    # Type A — Strong Corroboration (3 cases)
    CASE_A01, CASE_A02, CASE_A03,
    # Type B — Merchant-Owned Announcement (2 cases)
    CASE_B01, CASE_B02,
    # Type C — News-Driven Spike (1 case)
    CASE_C01,
    # Type D — No Evidence (3 cases)
    CASE_D01, CASE_D02, CASE_D03,
    # Type E — Wrong Merchant (2 cases)
    CASE_E01, CASE_E02,
    # Type F — Wrong Date (2 cases)
    CASE_F01, CASE_F02,
    # Type G — Post-Anomaly Event (2 cases)
    CASE_G01, CASE_G02,
    # Type H — Contradiction (2 cases)
    CASE_H01, CASE_H02,
    # Type I — Duplicate Reporting (1 case)
    CASE_I01,
    # Type J — Social-Only Evidence (2 cases)
    CASE_J01, CASE_J02,
    # Type K — Ambiguous Evidence (3 cases)
    CASE_K01, CASE_K02, CASE_K03,
    # Type L — Strong But Irrelevant (2 cases)
    CASE_L01, CASE_L02,
]

DEVELOPMENT_CASES: list[EvalCase] = [c for c in ALL_CASES if c.split == DatasetSplit.DEVELOPMENT]
HELD_OUT_CASES: list[EvalCase] = [c for c in ALL_CASES if c.split == DatasetSplit.HELD_OUT]

# Sanity checks at import time
assert len(ALL_CASES) == 25, f"Expected 25 cases, got {len(ALL_CASES)}"
assert len(DEVELOPMENT_CASES) == 18, f"Expected 18 dev cases, got {len(DEVELOPMENT_CASES)}"
assert len(HELD_OUT_CASES) == 7, f"Expected 7 held-out cases, got {len(HELD_OUT_CASES)}"
assert len(set(c.case_id for c in ALL_CASES)) == 25, "Duplicate case_ids detected"
