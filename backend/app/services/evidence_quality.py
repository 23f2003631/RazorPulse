"""
Evidence Quality Gates & Annotation Service.

Implements audit-grade pre-verification quality checks and annotations
for discovered evidence items.

ARCHITECTURAL PRINCIPLES (Day 3 User Corrections):
1. ANNOTATE, DO NOT SILENTLY DELETE:
   Every discovered evidence item is retained. Flags and exclusion recommendations
   are recorded as transparent annotations.
2. ADVISORY RELEVANCE SIGNAL:
   Entity token presence is an ADVISORY SIGNAL (INFO/WARNING), NOT an automatic
   exclusion filter. Gemini remains the authoritative semantic entity verifier.
3. CLAIM-LEVEL DEDUPLICATION (evidence_group_id):
   Assigns an evidence_group_id to items sharing near-identical text snippets
   (e.g., syndicated press releases across multiple domains), recognizing that
   independent domains are an approximation of independent corroboration.
"""

from dataclasses import dataclass, field
import hashlib
import re
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.evidence import NormalizedEvidence


class QualityGateResult(BaseModel):
    """Result of evaluating a single quality gate on an evidence item."""
    gate_name: str = Field(..., description="Name of the quality gate rule")
    passed: bool = Field(..., description="Whether the gate criteria were met")
    is_advisory: bool = Field(
        default=False,
        description="If True, failure is advisory metadata only and does not disqualify the item",
    )
    severity: str = Field(
        default="INFO",
        description="Severity level: INFO, WARNING, or ERROR",
    )
    reason: str = Field(..., description="Human-readable explanation of the check outcome")


class QualityAnnotatedEvidence(BaseModel):
    """
    Normalized evidence item augmented with quality annotations.

    Preserves full audit trail: discovered, flagged, usable, and grouped.
    """
    evidence: NormalizedEvidence
    annotations: list[QualityGateResult] = Field(default_factory=list)
    is_usable: bool = Field(
        default=True,
        description="Whether evidence passes hard validity gates (URL, domain, content)",
    )
    relevance_signal: str = Field(
        default="UNCHECKED",
        description="Advisory signal: STRONG_SIGNAL, WEAK_SIGNAL, or UNCERTAIN_SIGNAL",
    )
    evidence_group_id: Optional[str] = Field(
        default=None,
        description="Fingerprint ID grouping items with near-identical claim text (e.g. syndicated PR)",
    )


class EvidenceQualitySummary(BaseModel):
    """Summary report of quality gate evaluation across an evidence collection."""
    total_discovered: int
    total_usable: int
    total_excluded: int
    total_flagged: int
    unique_claim_groups: int
    exclusion_reasons: list[str] = Field(default_factory=list)
    flagged_reasons: list[str] = Field(default_factory=list)


class EvidenceQualityService:
    """
    Evaluates evidence items against structural and semantic quality gates.
    """

    @classmethod
    def annotate_collection(
        cls,
        evidence_items: list[NormalizedEvidence],
        merchant_name: str,
        merchant_domain: Optional[str] = None,
    ) -> tuple[list[QualityAnnotatedEvidence], EvidenceQualitySummary]:
        """
        Annotate all evidence items in a collection with quality checks.

        Returns:
            tuple of (annotated_items, quality_summary)
        """
        if not evidence_items:
            return [], EvidenceQualitySummary(
                total_discovered=0,
                total_usable=0,
                total_excluded=0,
                total_flagged=0,
                unique_claim_groups=0,
            )

        annotated: list[QualityAnnotatedEvidence] = []
        claim_groups: dict[str, str] = {}  # text_hash -> group_id

        for ev in evidence_items:
            gates: list[QualityGateResult] = []
            is_usable = True

            # Gate 1: Valid URL
            url_gate = cls._check_valid_url(ev.url)
            gates.append(url_gate)
            if not url_gate.passed and not url_gate.is_advisory:
                is_usable = False

            # Gate 2: Source Domain
            domain_gate = cls._check_source_domain(ev.source_domain)
            gates.append(domain_gate)
            if not domain_gate.passed and not domain_gate.is_advisory:
                is_usable = False

            # Gate 3: Content Availability
            content_gate = cls._check_content_availability(ev.content_snippet, ev.highlights)
            gates.append(content_gate)
            if not content_gate.passed and not content_gate.is_advisory:
                is_usable = False

            # Gate 4: Near-Duplicate Content / Syndication Fingerprint
            dup_gate, group_id = cls._check_near_duplicate(ev, claim_groups)
            gates.append(dup_gate)

            # Gate 5: Entity Relevance Signal (Advisory Only)
            rel_gate, rel_signal = cls._check_entity_relevance_signal(
                ev, merchant_name, merchant_domain
            )
            gates.append(rel_gate)

            annotated.append(QualityAnnotatedEvidence(
                evidence=ev,
                annotations=gates,
                is_usable=is_usable,
                relevance_signal=rel_signal,
                evidence_group_id=group_id,
            ))

        # Build summary
        total_discovered = len(annotated)
        total_usable = sum(1 for a in annotated if a.is_usable)
        total_excluded = total_discovered - total_usable
        total_flagged = sum(1 for a in annotated if any(not g.passed for g in a.annotations))
        unique_groups = len(set(a.evidence_group_id for a in annotated if a.evidence_group_id))

        exclusion_reasons = []
        flagged_reasons = []
        for a in annotated:
            for g in a.annotations:
                if not g.passed:
                    msg = f"[{a.evidence.url[:40]}] {g.gate_name}: {g.reason}"
                    if not g.is_advisory:
                        exclusion_reasons.append(msg)
                    else:
                        flagged_reasons.append(msg)

        summary = EvidenceQualitySummary(
            total_discovered=total_discovered,
            total_usable=total_usable,
            total_excluded=total_excluded,
            total_flagged=total_flagged,
            unique_claim_groups=unique_groups,
            exclusion_reasons=exclusion_reasons,
            flagged_reasons=flagged_reasons,
        )

        return annotated, summary

    # --- Quality Gate Implementations ---

    @staticmethod
    def _check_valid_url(url: str) -> QualityGateResult:
        if not url or not isinstance(url, str):
            return QualityGateResult(
                gate_name="valid_url",
                passed=False,
                is_advisory=False,
                severity="ERROR",
                reason="URL is missing or empty.",
            )
        try:
            parsed = urlparse(url.strip())
            if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
                return QualityGateResult(
                    gate_name="valid_url",
                    passed=False,
                    is_advisory=False,
                    severity="ERROR",
                    reason=f"URL '{url[:40]}' lacks a valid HTTP/HTTPS scheme or network location.",
                )
            return QualityGateResult(
                gate_name="valid_url",
                passed=True,
                is_advisory=False,
                severity="INFO",
                reason="URL is structurally valid.",
            )
        except Exception as e:
            return QualityGateResult(
                gate_name="valid_url",
                passed=False,
                is_advisory=False,
                severity="ERROR",
                reason=f"URL parsing failed: {str(e)}",
            )

    @staticmethod
    def _check_source_domain(domain: str) -> QualityGateResult:
        if not domain or domain.lower() in ("unknown", "none", ""):
            return QualityGateResult(
                gate_name="source_domain_present",
                passed=False,
                is_advisory=False,
                severity="ERROR",
                reason="Source domain could not be resolved from URL.",
            )
        return QualityGateResult(
            gate_name="source_domain_present",
            passed=True,
            is_advisory=False,
            severity="INFO",
            reason=f"Source domain '{domain}' is present.",
        )

    @staticmethod
    def _check_content_availability(
        content_snippet: Optional[str],
        highlights: list[str],
    ) -> QualityGateResult:
        has_snippet = bool(content_snippet and len(content_snippet.strip()) >= 20)
        has_highlights = bool(highlights and any(len(h.strip()) >= 10 for h in highlights))

        if not has_snippet and not has_highlights:
            return QualityGateResult(
                gate_name="content_availability",
                passed=False,
                is_advisory=False,
                severity="ERROR",
                reason="Evidence has no readable content snippet or key highlights.",
            )
        return QualityGateResult(
            gate_name="content_availability",
            passed=True,
            is_advisory=False,
            severity="INFO",
            reason="Substantive text content is available for verification.",
        )

    @classmethod
    def _check_near_duplicate(
        cls,
        evidence: NormalizedEvidence,
        claim_groups: dict[str, str],
    ) -> tuple[QualityGateResult, str]:
        """
        Detect near-duplicate text content (e.g. identical syndicated press releases).
        Assigns an evidence_group_id so callers can recognize duplicated claims.
        """
        # Create a simplified text fingerprint from snippet or title
        raw_text = (evidence.content_snippet or "")[:200] + (evidence.title or "")
        normalized_text = re.sub(r"\W+", " ", raw_text.lower()).strip()

        if len(normalized_text) < 30:
            group_id = f"group_{hashlib.md5(evidence.url.encode()).hexdigest()[:8]}"
            return (
                QualityGateResult(
                    gate_name="near_duplicate_claim",
                    passed=True,
                    is_advisory=True,
                    severity="INFO",
                    reason="Text is too brief for claim grouping; treated as unique.",
                ),
                group_id,
            )

        # Hash the first 120 normalized chars as a claim cluster key
        fingerprint = hashlib.md5(normalized_text[:120].encode()).hexdigest()[:12]

        if fingerprint in claim_groups:
            existing_group = claim_groups[fingerprint]
            return (
                QualityGateResult(
                    gate_name="near_duplicate_claim",
                    passed=False,
                    is_advisory=True,
                    severity="WARNING",
                    reason=(
                        f"Content exhibits strong text similarity to another discovered item "
                        f"(claim cluster: {existing_group}). Note: independent domains may reflect "
                        f"a single syndicated announcement rather than independent corroboration."
                    ),
                ),
                existing_group,
            )
        else:
            group_id = f"claim_{fingerprint}"
            claim_groups[fingerprint] = group_id
            return (
                QualityGateResult(
                    gate_name="near_duplicate_claim",
                    passed=True,
                    is_advisory=True,
                    severity="INFO",
                    reason="Content is distinct from other discovered items.",
                ),
                group_id,
            )

    @staticmethod
    def _check_entity_relevance_signal(
        evidence: NormalizedEvidence,
        merchant_name: str,
        merchant_domain: Optional[str] = None,
    ) -> tuple[QualityGateResult, str]:
        """
        Advisory-only heuristic signal checking whether merchant name tokens
        or domain stem appear in the title or snippet.

        CRITICAL USER INSTRUCTION:
        This is an ADVISORY METADATA SIGNAL, NOT an exclusion gate. A source may
        legitimately reference a brand, alias, product, or parent company.
        Gemini verification remains the authoritative semantic judge.
        """
        searchable_text = f"{evidence.title or ''} {evidence.content_snippet or ''} {' '.join(evidence.highlights or [])}".lower()

        # Check full name
        norm_name = merchant_name.lower().strip()
        if norm_name in searchable_text:
            return (
                QualityGateResult(
                    gate_name="entity_relevance_signal",
                    passed=True,
                    is_advisory=True,
                    severity="INFO",
                    reason=f"Full merchant name '{merchant_name}' found in text.",
                ),
                "STRONG_SIGNAL",
            )

        # Check domain stem
        if merchant_domain:
            domain_stem = merchant_domain.lower().split(".")[0]
            if len(domain_stem) >= 4 and domain_stem in searchable_text:
                return (
                    QualityGateResult(
                        gate_name="entity_relevance_signal",
                        passed=True,
                        is_advisory=True,
                        severity="INFO",
                        reason=f"Merchant domain stem '{domain_stem}' found in text.",
                    ),
                    "STRONG_SIGNAL",
                )

        # Check individual words (excluding common corporate suffixes)
        stop_words = {"india", "private", "limited", "pvt", "ltd", "corp", "inc", "the", "and", "co", "store", "online", "services"}
        name_tokens = [w for w in re.findall(r"\w+", norm_name) if len(w) >= 3 and w not in stop_words]

        found_tokens = [t for t in name_tokens if t in searchable_text]
        if found_tokens:
            return (
                QualityGateResult(
                    gate_name="entity_relevance_signal",
                    passed=True,
                    is_advisory=True,
                    severity="INFO",
                    reason=f"Merchant token(s) {found_tokens} detected in text.",
                ),
                "WEAK_SIGNAL",
            )

        return (
            QualityGateResult(
                gate_name="entity_relevance_signal",
                passed=False,
                is_advisory=True,
                severity="WARNING",
                reason=(
                    f"Merchant name '{merchant_name}' was not directly observed in title or snippet. "
                    f"Advisory signal only; semantic verification will evaluate brand/entity connection."
                ),
            ),
            "UNCERTAIN_SIGNAL",
        )
