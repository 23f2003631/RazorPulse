"""
Synthetic Investigation Evaluation Scenarios.

Provides 3 realistic test fixtures with known external evidence profiles
for evaluating the complete investigation pipeline without live APIs.

SCENARIOS:
1. SCENARIO_STRONG_CORROBORATION: Publicly documented viral campaign / launch -> Strong Corroboration
2. SCENARIO_ZERO_EVIDENCE: Unexplained anomalous velocity spike -> Low / Zero Evidence Corroboration
3. SCENARIO_CONTRADICTED_EVENT: Outdated campaign + official statement refuting sale -> Penalized Corroboration
"""

from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.evidence import NormalizedEvidence, SourceType
from app.schemas.verification import (
    EvidenceStrength,
    EvidenceVerificationItem,
    ExplanationSupportLevel,
    MerchantMatchLevel,
    SourceCredibilityLevel,
    TemporalMatchLevel,
    VerificationResult,
)

# ============================================================
# SCENARIO 1: Legitimate Viral Product Launch (Strong Corroboration)
# ============================================================
SCENARIO_1_EVENT_ID = uuid4()
SCENARIO_1_RISK_EVENT = {
    "id": str(SCENARIO_1_EVENT_ID),
    "merchant_id": str(uuid4()),
    "merchant_name": "UrbanCraft India",
    "merchant_domain": "urbancraft.in",
    "anomaly_type": "transaction_velocity_spike",
    "occurred_at": "2026-08-28T14:30:00+05:30",
    "baseline_transaction_count": 85,
    "observed_transaction_count": 1450,
    "percentage_change": 1605.88,
    "transaction_amount": 725000.00,
    "currency": "INR",
    "risk_reason": "Transaction velocity increased 17x above baseline over 3 hours.",
    "geographic_info": "Bengaluru, Karnataka, IN",
    "source": "simulated",
    "status": "pending",
    "merchants": {
        "merchant_name": "UrbanCraft India",
        "merchant_domain": "urbancraft.in",
    },
}

SCENARIO_1_EVIDENCE_1 = NormalizedEvidence(
    evidence_id=uuid4(),
    url="https://yourstory.com/2026/08/urbancraft-india-viral-handicraft-sale",
    title="UrbanCraft India's Heritage Collection Goes Viral on Social Media",
    source_domain="yourstory.com",
    source_type=SourceType.NEWS_MEDIA,
    published_at="2026-08-28T11:00:00Z",
    content_snippet="UrbanCraft India launched its nationwide artisan festive collection today, generating over 100,000 visitors within hours following celebrity endorsements.",
    highlights=["festive collection launch", "over 100,000 visitors in hours"],
    discovery_query='"UrbanCraft India" sale launch viral',
    discovery_query_intent="commercial_campaign",
    external_score=0.92,
)

SCENARIO_1_EVIDENCE_2 = NormalizedEvidence(
    evidence_id=uuid4(),
    url="https://economictimes.indiatimes.com/industry/services/retail/urbancraft-records-record-surge/articleshow/998877.cms",
    title="D2C Brand UrbanCraft Records Massive Surge During Festive Flash Sale",
    source_domain="economictimes.indiatimes.com",
    source_type=SourceType.NEWS_MEDIA,
    published_at="2026-08-28T16:00:00Z",
    content_snippet="Artisan direct-to-consumer platform UrbanCraft India saw orders surge 15-20x on Friday afternoon after kicking off its annual mega discount drive.",
    highlights=["orders surge 15-20x", "annual mega discount drive"],
    discovery_query='"UrbanCraft India" news August 2026',
    discovery_query_intent="timeframe_event",
    external_score=0.88,
)

SCENARIO_1_EVIDENCE_3 = NormalizedEvidence(
    evidence_id=uuid4(),
    url="https://urbancraft.in/pages/festive-sale-2026",
    title="Official Announcement: Festive Artisan Sale 2026 - UrbanCraft India",
    source_domain="urbancraft.in",
    source_type=SourceType.MERCHANT_OFFICIAL,
    published_at="2026-08-28T09:00:00Z",
    content_snippet="Welcome to UrbanCraft India's Annual Artisan Festive Sale! Enjoy up to 60% off across all handmade categories starting August 28.",
    highlights=["Annual Artisan Festive Sale", "starting August 28"],
    discovery_query="site:urbancraft.in launch OR sale OR announcement",
    discovery_query_intent="merchant_announcement",
    external_score=0.95,
)

SCENARIO_1_EVIDENCE_ITEMS = [SCENARIO_1_EVIDENCE_1, SCENARIO_1_EVIDENCE_2, SCENARIO_1_EVIDENCE_3]

SCENARIO_1_VERIFICATIONS = [
    EvidenceVerificationItem(
        evidence_id=SCENARIO_1_EVIDENCE_1.evidence_id,
        merchant_match=MerchantMatchLevel.DIRECT_MATCH,
        temporal_match=TemporalMatchLevel.EXACT_MATCH,
        explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
        evidence_strength=EvidenceStrength.STRONG_DIRECT,
        source_credibility=SourceCredibilityLevel.HIGH,
        event_category="viral_campaign",
        key_facts=["Festive collection launch on August 28", "Viral surge with 100k visitors"],
        contradictions_identified=[],
        uncertainties_noted=[],
        reasoning_summary="Article directly reports massive demand surge for UrbanCraft India on the exact anomaly date.",
    ),
    EvidenceVerificationItem(
        evidence_id=SCENARIO_1_EVIDENCE_2.evidence_id,
        merchant_match=MerchantMatchLevel.DIRECT_MATCH,
        temporal_match=TemporalMatchLevel.EXACT_MATCH,
        explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
        evidence_strength=EvidenceStrength.STRONG_DIRECT,
        source_credibility=SourceCredibilityLevel.HIGH,
        event_category="flash_sale",
        key_facts=["15-20x order surge recorded on Friday afternoon"],
        contradictions_identified=[],
        uncertainties_noted=[],
        reasoning_summary="Economic Times confirms 15-20x order surge matching transaction velocity spike magnitude.",
    ),
    EvidenceVerificationItem(
        evidence_id=SCENARIO_1_EVIDENCE_3.evidence_id,
        merchant_match=MerchantMatchLevel.DIRECT_MATCH,
        temporal_match=TemporalMatchLevel.EXACT_MATCH,
        explanation_support=ExplanationSupportLevel.STRONG_EXPLANATION,
        evidence_strength=EvidenceStrength.STRONG_DIRECT,
        source_credibility=SourceCredibilityLevel.HIGH,
        event_category="merchant_announcement",
        key_facts=["Official festive sale began August 28"],
        contradictions_identified=[],
        uncertainties_noted=[],
        reasoning_summary="Merchant official domain confirms planned nationwide sale starting August 28.",
    ),
]


# ============================================================
# SCENARIO 2: Unexplained Velocity Spike (Zero External Evidence)
# ============================================================
SCENARIO_2_EVENT_ID = uuid4()
SCENARIO_2_RISK_EVENT = {
    "id": str(SCENARIO_2_EVENT_ID),
    "merchant_id": str(uuid4()),
    "merchant_name": "QuickDeal Bazaar",
    "merchant_domain": "quickdealbazaar.com",
    "anomaly_type": "transaction_velocity_spike",
    "occurred_at": "2026-08-30T02:15:00+05:30",
    "baseline_transaction_count": 40,
    "observed_transaction_count": 2200,
    "percentage_change": 5400.0,
    "transaction_amount": 3300000.00,
    "currency": "INR",
    "risk_reason": "Extreme velocity spike at 2:15 AM IST (55x baseline). High-value transactions concentrated in 45 mins.",
    "geographic_info": "New Delhi, Delhi, IN",
    "source": "simulated",
    "status": "pending",
    "merchants": {
        "merchant_name": "QuickDeal Bazaar",
        "merchant_domain": "quickdealbazaar.com",
    },
}

SCENARIO_2_EVIDENCE_ITEMS = []
SCENARIO_2_VERIFICATIONS = []


# ============================================================
# SCENARIO 3: Contradicted / Misaligned Evidence (Penalized Corroboration)
# ============================================================
SCENARIO_3_EVENT_ID = uuid4()
SCENARIO_3_RISK_EVENT = {
    "id": str(SCENARIO_3_EVENT_ID),
    "merchant_id": str(uuid4()),
    "merchant_name": "TrendWear Daily",
    "merchant_domain": "trendweardaily.in",
    "anomaly_type": "transaction_velocity_spike",
    "occurred_at": "2026-08-29T18:00:00+05:30",
    "baseline_transaction_count": 50,
    "observed_transaction_count": 400,
    "percentage_change": 700.0,
    "transaction_amount": 280000.00,
    "currency": "INR",
    "risk_reason": "Sudden 8x velocity spike on Saturday evening.",
    "geographic_info": "Mumbai, Maharashtra, IN",
    "source": "simulated",
    "status": "pending",
    "merchants": {
        "merchant_name": "TrendWear Daily",
        "merchant_domain": "trendweardaily.in",
    },
}

SCENARIO_3_EVIDENCE_1 = NormalizedEvidence(
    evidence_id=uuid4(),
    url="https://inc42.com/buzz/trendwear-daily-diwali-campaign-2024",
    title="TrendWear Daily Gears Up for Diwali 2024 with Flash Deals",
    source_domain="inc42.com",
    source_type=SourceType.INDUSTRY_PORTAL,
    published_at="2024-10-15T10:00:00Z",
    content_snippet="Apparel startup TrendWear Daily announced heavy discounts for Diwali 2024, running exclusive sales across India.",
    highlights=["Diwali 2024 flash deals"],
    discovery_query='"TrendWear Daily" sale campaign',
    discovery_query_intent="commercial_campaign",
    external_score=0.65,
)

SCENARIO_3_EVIDENCE_2 = NormalizedEvidence(
    evidence_id=uuid4(),
    url="https://twitter.com/trendweardaily/status/1829000000000000000",
    title="TrendWear Daily Official Support Notice",
    source_domain="twitter.com",
    source_type=SourceType.SOCIAL_COMMUNITY,
    published_at="2026-08-29T18:30:00Z",
    content_snippet="Notice to customers: We are currently experiencing a technical bug causing duplicate checkout requests. No flash sale or promotional discount is currently active.",
    highlights=["technical bug causing duplicate checkout requests", "No flash sale is currently active"],
    discovery_query='"TrendWear Daily" news August 2026',
    discovery_query_intent="timeframe_event",
    external_score=0.85,
)

SCENARIO_3_EVIDENCE_ITEMS = [SCENARIO_3_EVIDENCE_1, SCENARIO_3_EVIDENCE_2]

SCENARIO_3_VERIFICATIONS = [
    EvidenceVerificationItem(
        evidence_id=SCENARIO_3_EVIDENCE_1.evidence_id,
        merchant_match=MerchantMatchLevel.DIRECT_MATCH,
        temporal_match=TemporalMatchLevel.HISTORICAL_PREVIOUS,
        explanation_support=ExplanationSupportLevel.WEAK_EXPLANATION,
        evidence_strength=EvidenceStrength.WEAK_CIRCUMSTANTIAL,
        source_credibility=SourceCredibilityLevel.MEDIUM,
        event_category="historical_sale",
        key_facts=["Diwali sale occurred in October 2024"],
        contradictions_identified=["Article relates to 2024, nearly 2 years before the observed 2026 anomaly."],
        uncertainties_noted=["Timing is completely disconnected from August 2026."],
        reasoning_summary="Historical article from 2024 cannot explain an August 2026 transaction spike.",
    ),
    EvidenceVerificationItem(
        evidence_id=SCENARIO_3_EVIDENCE_2.evidence_id,
        merchant_match=MerchantMatchLevel.DIRECT_MATCH,
        temporal_match=TemporalMatchLevel.EXACT_MATCH,
        explanation_support=ExplanationSupportLevel.NO_EXPLANATION,
        evidence_strength=EvidenceStrength.CONTRADICTED,
        source_credibility=SourceCredibilityLevel.HIGH,
        event_category="merchant_statement",
        key_facts=["Merchant states checkout glitch occurring", "Explicitly denies active flash sale"],
        contradictions_identified=["Merchant official notice explicitly refutes that a legitimate flash sale is occurring."],
        uncertainties_noted=[],
        reasoning_summary="Merchant directly refutes commercial promotion and cites technical duplicate request malfunction.",
    ),
]
