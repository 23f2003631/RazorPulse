"""
Gemini Evidence Verification Prompts.

Anti-hallucination prompt templates enforcing strict evidence grounding,
neutral tone, factual quotation, and explicit uncertainty detection.
"""

VERIFICATION_SYSTEM_INSTRUCTION = """You are an objective Evidence Verification Analyst for RazorPulse.
Your sole job is to evaluate whether a supplied piece of external web evidence corroborates a real-world event that could explain an observed payment transaction anomaly.

CRITICAL CONSTRAINTS:
1. STRICT EVIDENCE GROUNDING: You MUST base your evaluation ONLY on the provided evidence text snippet. Do NOT assume, extrapolate, or hallucinate facts, dates, promotions, or merchant identities not present in the snippet.
2. NO RISK / FRAUD DECISIONS: You do NOT determine if a merchant is fraudulent or safe. You only evaluate the relevance, timing, credibility, and explanatory strength of this specific evidence piece.
3. SEPARATE EVIDENCE FROM HYPOTHESIS: If a story sounds plausible but the snippet does not contain concrete details, evaluate it as WEAK or UNCERTAIN. Plausibility without evidence is NOT corroboration.
4. EXPLICIT CONTRADICTION DETECTION: If the text indicates the event happened at a different time, involved a different merchant, was cancelled, or was refuted, explicitly list this in contradictions_identified.
5. EXPLICIT UNCERTAINTY: If key details (dates, entity names, figures) are missing, list them in uncertainties_noted.
"""


from app.schemas.evidence import NormalizedEvidence


def build_evidence_verification_prompt(
    merchant_name: str,
    merchant_domain: str | None,
    anomaly_type: str,
    occurred_at_str: str,
    risk_reason: str | None,
    evidence_id: str,
    evidence_url: str,
    evidence_title: str | None,
    source_domain: str,
    source_type: str,
    published_at: str | None,
    content_snippet: str | None,
    highlights: list[str],
) -> str:
    """
    Build structured verification prompt for a single evidence item.
    """
    highlights_text = "\n".join(f"- {h}" for h in highlights) if highlights else "None"
    snippet_text = content_snippet.strip() if content_snippet else "No snippet content provided."

    return f"""### CONTEXT: Observed Transaction Anomaly
- Merchant Name: {merchant_name}
- Merchant Domain: {merchant_domain or "Not specified"}
- Anomaly Category: {anomaly_type}
- Anomaly Timestamp: {occurred_at_str}
- Anomaly Risk Reason: {risk_reason or "Unusual transaction pattern flagged by risk engine"}

### EVIDENCE TO EVALUATE:
- Evidence ID: {evidence_id}
- Source URL: {evidence_url}
- Title: {evidence_title or "Untitled"}
- Source Domain: {source_domain} (Classified as: {source_type})
- Published Date: {published_at or "Unknown / Not specified in metadata"}

#### Text Content:
{snippet_text}

#### Highlights:
{highlights_text}

### INSTRUCTIONS:
Evaluate this evidence item against the anomaly context and return a structured assessment conforming strictly to the requested schema:
1. `evidence_id`: Return exactly "{evidence_id}".
2. `merchant_match`: Is this text directly about {merchant_name} (`direct_match`), a related entity (`related_entity`), a different entity (`unrelated`), or ambiguous (`uncertain`)?
3. `temporal_match`: Does the timing of the event in the text match the anomaly date ({occurred_at_str})? (`exact_match`, `window_match`, `historical_previous`, `post_anomaly`, `unrelated_timing`, `uncertain`)
4. `explanation_support`: Does the text describe an event that explains a surge in transactions? (`strong_explanation`, `moderate_explanation`, `weak_explanation`, `no_explanation`, `uncertain`)
5. `evidence_strength`: How direct is the evidence? (`strong_direct`, `moderate_indirect`, `weak_circumstantial`, `unsupported`, `contradicted`)
6. `source_credibility`: Assessed credibility of the source (`high`, `medium`, `low`, `unknown`)
7. `event_category`: Short string category (e.g. product_launch, viral_campaign, flash_sale, press_feature, none)
8. `key_facts`: List of factual claims stated in text
9. `contradictions_identified`: List of contradictions or discrepancies
10. `uncertainties_noted`: List of missing details or ambiguities
11. `reasoning_summary`: 1-2 sentences explaining your assessment.
"""


def build_batch_evidence_verification_prompt(
    merchant_name: str,
    merchant_domain: str | None,
    anomaly_type: str,
    occurred_at_str: str,
    risk_reason: str | None,
    evidence_items: list[NormalizedEvidence],
) -> str:
    """
    Build structured batch verification prompt for multiple evidence items in a single request.
    """
    evidence_blocks = []
    for idx, ev in enumerate(evidence_items, start=1):
        highlights_text = "\n".join(f"  - {h}" for h in ev.highlights) if ev.highlights else "  None"
        snippet_text = ev.content_snippet.strip() if ev.content_snippet else "No snippet content provided."
        block = f"""--- EVIDENCE ITEM {idx} ---
- Evidence ID: {ev.evidence_id}
- URL: {ev.url}
- Title: {ev.title or "Untitled"}
- Source Domain: {ev.source_domain} (Type: {ev.source_type.value})
- Published Date: {ev.published_at or "Unknown"}
- Snippet Content:
{snippet_text}
- Highlights:
{highlights_text}
"""
        evidence_blocks.append(block)

    all_evidence_text = "\n".join(evidence_blocks)

    return f"""### CONTEXT: Observed Transaction Anomaly
- Merchant Name: {merchant_name}
- Merchant Domain: {merchant_domain or "Not specified"}
- Anomaly Category: {anomaly_type}
- Anomaly Timestamp: {occurred_at_str}
- Anomaly Risk Reason: {risk_reason or "Unusual transaction pattern flagged by risk engine"}

### DISCOVERED EVIDENCE ITEMS ({len(evidence_items)} total to evaluate):
{all_evidence_text}

### INSTRUCTIONS:
Evaluate each of the {len(evidence_items)} evidence items individually against the transaction anomaly context.
Return a `BatchEvidenceVerificationResponse` containing a list of `verifications`, with exactly one structured assessment per input evidence item conforming to the schema:
1. `evidence_id`: Exactly match the corresponding UUID from the evidence item.
2. `merchant_match`: Direct entity match (`direct_match`), related (`related_entity`), different (`unrelated`), or ambiguous (`uncertain`).
3. `temporal_match`: Alignment with anomaly date ({occurred_at_str}): `exact_match` (0-48h), `window_match` (7d), `historical_previous`, `post_anomaly`, `unrelated_timing`, `uncertain`.
4. `explanation_support`: Explanatory power for a surge in volume: `strong_explanation`, `moderate_explanation`, `weak_explanation`, `no_explanation`, `uncertain`.
5. `evidence_strength`: Evidentiary directness: `strong_direct`, `moderate_indirect`, `weak_circumstantial`, `unsupported`, `contradicted`.
6. `source_credibility`: Source credibility: `high`, `medium`, `low`, `unknown`.
7. `event_category`: Short string category (e.g. product_launch, viral_campaign, flash_sale, press_feature, none).
8. `key_facts`: Factual claims directly stated in text.
9. `contradictions_identified`: Factual contradictions or discrepancies.
10. `uncertainties_noted`: Missing details or ambiguities.
11. `reasoning_summary`: Concise 1-2 sentence explanation.
"""
