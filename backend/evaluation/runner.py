"""
Evaluation Runner for RazorPulse Benchmark.

Runs deterministic ECI v1 evaluation on synthetic fixture-only cases.
No external API calls (no Exa, no Gemini, no Supabase, no network).

Evaluates TWO independent dimensions:
A. Corroboration classification (4-class)
B. Contradiction detection (binary)

Reports metrics honestly with support counts and instability flags.
"""

from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from app.schemas.eci import ECIScoreResult
from app.schemas.verification import VerificationResult
from app.services.scoring.eci_engine import ECIEngine
from evaluation.ground_truth import (
    ContradictionState,
    CorroborationClass,
    DatasetSplit,
    EvalCase,
    eci_to_corroboration_class,
    has_contradiction_detected,
)
from evaluation.metrics import (
    CorroborationEvalResult,
    ContradictionEvalResult,
    compute_corroboration_metrics,
    compute_contradiction_metrics,
)


@dataclass
class CaseResult:
    """Result of evaluating a single case."""
    case_id: str
    archetype: str
    difficulty: str
    split: str

    # Ground truth
    expected_corroboration: CorroborationClass
    expected_contradiction: ContradictionState

    # System output
    eci_score: int
    eci_band: str
    predicted_corroboration: CorroborationClass
    predicted_contradiction: ContradictionState
    detected_contradictions: list[str]

    # Correctness
    corroboration_correct: bool
    contradiction_correct: bool

    # Failure analysis
    failure_mode: Optional[str] = None


@dataclass
class ScoreSeparationAnalysis:
    """Score distribution analysis per ground-truth class."""
    class_name: str
    count: int
    mean_eci: float
    median_eci: float
    min_eci: int
    max_eci: int
    scores: list[int]


@dataclass
class FailureModeReport:
    """Categorized failure analysis."""
    failure_modes: dict[str, list[str]]  # mode -> list of case_ids
    total_failures: int


@dataclass
class BenchmarkReport:
    """Complete benchmark evaluation report."""
    # Metadata
    split_evaluated: str
    total_cases: int
    eci_version: str
    benchmark_type: str = "synthetic_fixture_only"

    # Dimension A: Corroboration
    corroboration_result: Optional[CorroborationEvalResult] = None

    # Dimension B: Contradiction
    contradiction_result: Optional[ContradictionEvalResult] = None

    # Per-case details
    case_results: list[CaseResult] = field(default_factory=list)

    # Score separation
    score_separation: list[ScoreSeparationAnalysis] = field(default_factory=list)

    # Failure analysis
    failure_report: Optional[FailureModeReport] = None

    disclaimer: str = (
        "This is a small synthetic engineering benchmark and is not "
        "statistically representative of production performance. "
        "Per-class metrics with 1–2 held-out examples are unstable."
    )


def _classify_failure_mode(case: EvalCase, result: CaseResult) -> Optional[str]:
    """
    Categorize the failure mode for a misclassified case.

    Returns a failure mode string, or None if both dimensions are correct.
    """
    if result.corroboration_correct and result.contradiction_correct:
        return None

    # Analyze what went wrong
    if not result.corroboration_correct:
        expected = result.expected_corroboration
        predicted = result.predicted_corroboration

        # Check specific patterns
        if expected == CorroborationClass.NO_CORROBORATION and predicted != CorroborationClass.NO_CORROBORATION:
            # False positive corroboration
            if any(v.merchant_match.value == "unrelated" for v in case.verification_items):
                return "wrong_merchant"
            if any(v.temporal_match.value in ("post_anomaly", "unrelated_timing", "historical_previous") for v in case.verification_items):
                return "wrong_timeframe"
            if any(v.explanation_support.value == "no_explanation" for v in case.verification_items):
                return "irrelevant_event"
            if any(v.status.value == "failed" for v in case.verification_items):
                return "insufficient_evidence"
            return "false_positive_corroboration"

        if expected != CorroborationClass.NO_CORROBORATION and predicted == CorroborationClass.NO_CORROBORATION:
            return "insufficient_evidence"

        if expected.value > predicted.value:
            return "under_corroboration"
        else:
            return "over_corroboration"

    if not result.contradiction_correct:
        if result.expected_contradiction == ContradictionState.CONTRADICTION_PRESENT:
            return "contradiction_missed"
        else:
            return "contradiction_over_penalized"

    return "unclassified"


def run_single_case(case: EvalCase) -> CaseResult:
    """
    Evaluate a single benchmark case through the deterministic ECI engine.

    Uses ONLY the pre-built fixtures — no external API calls.
    """
    # Build VerificationResult from fixtures
    investigation_id = uuid4()
    verification_result = VerificationResult(
        investigation_id=investigation_id,
        items=case.verification_items,
        overall_contradictions=case.overall_contradictions,
        overall_uncertainties=case.overall_uncertainties,
        verified_at_timestamp="2026-09-01T00:00:00Z",
    )

    # Sync evidence_ids between evidence_items and verification_items
    # (fixtures use independent UUIDs; need to align for ECI domain lookup)
    evidence_items = case.evidence_items
    for i, (ev, vi) in enumerate(zip(evidence_items, case.verification_items)):
        vi_copy = vi.model_copy(update={"evidence_id": ev.evidence_id})
        verification_result.items[i] = vi_copy

    # Annotate evidence items with quality gates to detect claim groups (near-duplicate text)
    from app.services.evidence_quality import EvidenceQualityService
    annotated_items, _ = EvidenceQualityService.annotate_collection(
        evidence_items=evidence_items,
        merchant_name=case.merchant_name,
        merchant_domain=case.merchant_domain,
    )
    evidence_group_ids = {
        a.evidence.evidence_id: a.evidence_group_id
        for a in annotated_items
        if a.evidence_group_id
    }

    # Calculate ECI
    eci_result = ECIEngine.calculate_eci(
        verification_result=verification_result,
        evidence_items=evidence_items,
        evidence_group_ids=evidence_group_ids,
    )

    # Classify outputs
    predicted_corroboration = eci_to_corroboration_class(eci_result.eci_score)
    predicted_contradiction = (
        ContradictionState.CONTRADICTION_PRESENT
        if has_contradiction_detected(verification_result.overall_contradictions)
        else ContradictionState.CONTRADICTION_ABSENT
    )

    result = CaseResult(
        case_id=case.case_id,
        archetype=case.archetype,
        difficulty=case.difficulty.value,
        split=case.split.value,
        expected_corroboration=case.expected_corroboration,
        expected_contradiction=case.expected_contradiction,
        eci_score=eci_result.eci_score,
        eci_band=eci_result.band.value,
        predicted_corroboration=predicted_corroboration,
        predicted_contradiction=predicted_contradiction,
        detected_contradictions=verification_result.overall_contradictions,
        corroboration_correct=(predicted_corroboration == case.expected_corroboration),
        contradiction_correct=(predicted_contradiction == case.expected_contradiction),
    )

    result.failure_mode = _classify_failure_mode(case, result)
    return result


def run_benchmark(
    cases: list[EvalCase],
    split_name: str = "all",
) -> BenchmarkReport:
    """
    Run the complete benchmark on a set of evaluation cases.

    Args:
        cases: List of EvalCase instances to evaluate
        split_name: Label for the evaluated split (e.g., "development", "held_out", "all")

    Returns:
        BenchmarkReport with complete metrics, per-case results, separation analysis, and failure modes
    """
    case_results = [run_single_case(case) for case in cases]

    # Corroboration metrics
    true_corrob = [r.expected_corroboration for r in case_results]
    pred_corrob = [r.predicted_corroboration for r in case_results]
    corrob_result = compute_corroboration_metrics(true_corrob, pred_corrob)

    # Contradiction metrics
    true_contra = [r.expected_contradiction for r in case_results]
    pred_contra = [r.predicted_contradiction for r in case_results]
    contra_result = compute_contradiction_metrics(true_contra, pred_contra)

    # Score separation analysis
    from collections import defaultdict
    scores_by_class: dict[str, list[int]] = defaultdict(list)
    for r in case_results:
        scores_by_class[r.expected_corroboration.value].append(r.eci_score)

    separation = []
    for cls in ["no_corroboration", "weak_corroboration", "moderate_corroboration", "strong_corroboration"]:
        scores = sorted(scores_by_class.get(cls, []))
        if scores:
            mean_eci = sum(scores) / len(scores)
            median_eci = scores[len(scores) // 2]
            separation.append(ScoreSeparationAnalysis(
                class_name=cls,
                count=len(scores),
                mean_eci=round(mean_eci, 2),
                median_eci=median_eci,
                min_eci=min(scores),
                max_eci=max(scores),
                scores=scores,
            ))

    # Failure mode analysis
    failure_modes: dict[str, list[str]] = defaultdict(list)
    total_failures = 0
    for r in case_results:
        if r.failure_mode:
            failure_modes[r.failure_mode].append(r.case_id)
            total_failures += 1

    failure_report = FailureModeReport(
        failure_modes=dict(failure_modes),
        total_failures=total_failures,
    )

    return BenchmarkReport(
        split_evaluated=split_name,
        total_cases=len(cases),
        eci_version=ECIEngine.ECI_VERSION,
        corroboration_result=corrob_result,
        contradiction_result=contra_result,
        case_results=case_results,
        score_separation=separation,
        failure_report=failure_report,
    )


def format_benchmark_report(report: BenchmarkReport) -> str:
    """Format a BenchmarkReport as human-readable text."""
    lines = []
    lines.append("=" * 72)
    lines.append("RAZORPULSE EVALUATION BENCHMARK REPORT")
    lines.append("=" * 72)
    lines.append(f"Split: {report.split_evaluated}")
    lines.append(f"Total cases: {report.total_cases}")
    lines.append(f"ECI version: {report.eci_version}")
    lines.append(f"Benchmark type: {report.benchmark_type}")
    lines.append("")
    lines.append(f"[!] {report.disclaimer}")
    lines.append("")

    # Corroboration
    if report.corroboration_result:
        cr = report.corroboration_result
        lines.append("-" * 72)
        lines.append("DIMENSION A: CORROBORATION CLASSIFICATION (4-class)")
        lines.append("-" * 72)
        lines.append(f"Accuracy:         {cr.accuracy:.4f} ({cr.correct}/{cr.total_cases})")
        lines.append(f"Macro Precision:  {cr.macro_precision:.4f}")
        lines.append(f"Macro Recall:     {cr.macro_recall:.4f}")
        lines.append(f"Macro F1:         {cr.macro_f1:.4f}")
        lines.append("")
        lines.append("Per-class breakdown:")
        lines.append(f"  {'Class':<28} {'P':>6} {'R':>6} {'F1':>6} {'Support':>8} {'Note':>10}")
        for pc in cr.per_class:
            note = "UNSTABLE" if pc.is_unstable else ""
            lines.append(f"  {pc.class_name:<28} {pc.precision:>6.4f} {pc.recall:>6.4f} {pc.f1:>6.4f} {pc.support:>8} {note:>10}")
        lines.append("")
        lines.append("Confusion matrix:")
        lines.append("  Predicted ->")
        header = "  " + f"{'True v':<28}" + "".join(f"{c[:8]:>10}" for c in cr.confusion.classes)
        lines.append(header)
        for i, cls_name in enumerate(cr.confusion.classes):
            row = "  " + f"{cls_name:<28}" + "".join(f"{cr.confusion.matrix[i][j]:>10}" for j in range(len(cr.confusion.classes)))
            lines.append(row)

    # Contradiction
    if report.contradiction_result:
        ct = report.contradiction_result
        lines.append("")
        lines.append("-" * 72)
        lines.append("DIMENSION B: CONTRADICTION DETECTION (binary)")
        lines.append("-" * 72)
        lines.append(f"Precision:    {ct.precision:.4f}")
        lines.append(f"Recall:       {ct.recall:.4f}")
        lines.append(f"F1:           {ct.f1:.4f}")
        lines.append(f"TP: {ct.true_positives}  FP: {ct.false_positives}  TN: {ct.true_negatives}  FN: {ct.false_negatives}")
        lines.append(f"Support (PRESENT): {ct.support_present}  Support (ABSENT): {ct.support_absent}")
        if ct.is_unstable:
            lines.append("[!] Contradiction metrics are UNSTABLE due to small class support.")

    # Score separation
    if report.score_separation:
        lines.append("")
        lines.append("-" * 72)
        lines.append("SCORE SEPARATION ANALYSIS")
        lines.append("-" * 72)
        lines.append(f"  {'Class':<28} {'Count':>6} {'Mean':>8} {'Median':>8} {'Min':>6} {'Max':>6} {'Scores'}")
        for sep in report.score_separation:
            scores_str = str(sep.scores[:10]) + ("..." if len(sep.scores) > 10 else "")
            lines.append(f"  {sep.class_name:<28} {sep.count:>6} {sep.mean_eci:>8.1f} {sep.median_eci:>8} {sep.min_eci:>6} {sep.max_eci:>6} {scores_str}")

    # Failure modes
    if report.failure_report and report.failure_report.total_failures > 0:
        lines.append("")
        lines.append("-" * 72)
        lines.append(f"FAILURE MODE ANALYSIS ({report.failure_report.total_failures} failures)")
        lines.append("-" * 72)
        for mode, case_ids in sorted(report.failure_report.failure_modes.items()):
            lines.append(f"  {mode}: {', '.join(case_ids)}")

    # Per-case summary
    lines.append("")
    lines.append("-" * 72)
    lines.append("PER-CASE RESULTS")
    lines.append("-" * 72)
    lines.append(f"  {'Case ID':<40} {'ECI':>5} {'Expected':>18} {'Predicted':>18} {'Corrob':>7} {'Contra':>7}")
    for r in report.case_results:
        corrob_ok = "PASS" if r.corroboration_correct else "FAIL"
        contra_ok = "PASS" if r.contradiction_correct else "FAIL"
        lines.append(
            f"  {r.case_id:<40} {r.eci_score:>5} "
            f"{r.expected_corroboration.value[:16]:>18} "
            f"{r.predicted_corroboration.value[:16]:>18} "
            f"{corrob_ok:>7} {contra_ok:>7}"
        )

    lines.append("")
    lines.append("=" * 72)
    return "\n".join(lines)


if __name__ == "__main__":
    from evaluation.dataset import ALL_CASES
    report = run_benchmark(ALL_CASES, split_name="all")
    print(format_benchmark_report(report))

