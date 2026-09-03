"""
ECI Calibration Analysis Module.

Analyzes the calibration, score separation, and failure modes of the ECI engine
against the synthetic evaluation dataset.

Key analyses:
1. Score distribution and separation across ground-truth classes (mean, median, min, max, overlap)
2. Monotonicity across corroboration levels
3. Systematic failure mode classification (e.g. entity mismatch leakage, temporal leakage)
4. Calibration report generation for documentation and Day 4 improvement planning
"""

from dataclasses import dataclass
from typing import Optional

from evaluation.dataset import ALL_CASES, DEVELOPMENT_CASES, HELD_OUT_CASES
from evaluation.ground_truth import CorroborationClass
from evaluation.runner import BenchmarkReport, run_benchmark


@dataclass
class SeparationMetric:
    """Measures score separation between two adjacent classes."""
    lower_class: str
    upper_class: str
    lower_max: int
    upper_min: int
    separation_gap: int  # upper_min - lower_max (positive = clean separation, negative = overlap)
    is_overlapping: bool


@dataclass
class CalibrationAnalysis:
    """Comprehensive calibration analysis of the ECI engine."""
    eci_version: str
    split: str
    total_cases: int
    benchmark_report: BenchmarkReport
    adjacent_separations: list[SeparationMetric]
    monotonic_mean: bool
    monotonic_median: bool
    summary_findings: list[str]


def analyze_calibration(cases=None, split_name: str = "all") -> CalibrationAnalysis:
    """
    Perform deep calibration analysis on the ECI engine.

    Args:
        cases: Optional list of EvalCase instances (defaults to ALL_CASES)
        split_name: Label for split ("all", "development", "held_out")

    Returns:
        CalibrationAnalysis containing separation, monotonicity, and failure modes
    """
    if cases is None:
        cases = ALL_CASES

    report = run_benchmark(cases, split_name=split_name)

    # Analyze separation between adjacent classes
    order = [
        "no_corroboration",
        "weak_corroboration",
        "moderate_corroboration",
        "strong_corroboration",
    ]
    sep_by_class = {s.class_name: s for s in report.score_separation}

    adjacent_separations: list[SeparationMetric] = []
    for i in range(len(order) - 1):
        c1 = order[i]
        c2 = order[i + 1]
        s1 = sep_by_class.get(c1)
        s2 = sep_by_class.get(c2)
        if s1 and s2:
            gap = s2.min_eci - s1.max_eci
            adjacent_separations.append(SeparationMetric(
                lower_class=c1,
                upper_class=c2,
                lower_max=s1.max_eci,
                upper_min=s2.min_eci,
                separation_gap=gap,
                is_overlapping=gap <= 0,
            ))

    # Check monotonicity of central tendencies
    means = [s.mean_eci for s in report.score_separation]
    medians = [s.median_eci for s in report.score_separation]
    monotonic_mean = all(means[i] <= means[i + 1] for i in range(len(means) - 1)) if len(means) > 1 else True
    monotonic_median = all(medians[i] <= medians[i + 1] for i in range(len(medians) - 1)) if len(medians) > 1 else True

    # Identify key structural findings
    findings = []
    if monotonic_mean:
        findings.append(
            "Mean ECI increases monotonically across ground-truth classes: "
            + " < ".join(f"{s.class_name} ({s.mean_eci:.1f})" for s in report.score_separation)
        )
    else:
        findings.append("Warning: Mean ECI is not strictly monotonic across classes.")

    for sep in adjacent_separations:
        if sep.is_overlapping:
            findings.append(
                f"Score overlap observed between '{sep.lower_class}' (max {sep.lower_max}) "
                f"and '{sep.upper_class}' (min {sep.upper_min}), overlap gap: {sep.separation_gap} pts."
            )
        else:
            findings.append(
                f"Clean separation between '{sep.lower_class}' and '{sep.upper_class}': gap of +{sep.separation_gap} pts."
            )

    if report.failure_report and report.failure_report.total_failures > 0:
        findings.append(
            f"Total misclassifications under v1 heuristic: {report.failure_report.total_failures}/{report.total_cases} cases."
        )
        for mode, ids in report.failure_report.failure_modes.items():
            findings.append(f"  - Failure mode '{mode}': {len(ids)} case(s) ({', '.join(ids[:3])}{'...' if len(ids) > 3 else ''})")

    return CalibrationAnalysis(
        eci_version=report.eci_version,
        split=split_name,
        total_cases=len(cases),
        benchmark_report=report,
        adjacent_separations=adjacent_separations,
        monotonic_mean=monotonic_mean,
        monotonic_median=monotonic_median,
        summary_findings=findings,
    )


def format_calibration_report(analysis: CalibrationAnalysis) -> str:
    """Format calibration findings as a comprehensive string report."""
    lines = []
    lines.append("=" * 72)
    lines.append(f"ECI CALIBRATION & SEPARATION REPORT -- {analysis.eci_version}")
    lines.append("=" * 72)
    lines.append(f"Split: {analysis.split} ({analysis.total_cases} cases)")
    lines.append(f"Monotonic Mean ECI: {'YES' if analysis.monotonic_mean else 'NO'}")
    lines.append(f"Monotonic Median ECI: {'YES' if analysis.monotonic_median else 'NO'}")
    lines.append("")
    lines.append("Adjacent Class Separation:")
    for sep in analysis.adjacent_separations:
        status = "OVERLAP" if sep.is_overlapping else "SEPARATED"
        lines.append(
            f"  {sep.lower_class:<24} vs {sep.upper_class:<24} "
            f"[{status}] (max {sep.lower_max} vs min {sep.upper_min}, gap: {sep.separation_gap:+d})"
        )
    lines.append("")
    lines.append("Summary Findings:")
    for f in analysis.summary_findings:
        lines.append(f"  * {f}")
    lines.append("=" * 72)
    return "\n".join(lines)
