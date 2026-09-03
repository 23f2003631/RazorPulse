"""
Evaluation Metrics for RazorPulse Benchmark.

Computes accuracy, precision, recall, F1, and confusion matrix for:
A. Corroboration classification (4-class: NO, WEAK, MODERATE, STRONG)
B. Contradiction detection (binary: PRESENT, ABSENT)

LIMITATIONS:
  - Metrics on the held-out set (7 cases) are NOT statistically representative.
  - Per-class metrics with 1–2 examples are UNSTABLE and must be flagged.
  - All results are on the SYNTHETIC benchmark, not production data.
"""

from dataclasses import dataclass, field
from typing import Optional

from evaluation.ground_truth import ContradictionState, CorroborationClass


CORROBORATION_CLASSES = [
    CorroborationClass.NO_CORROBORATION,
    CorroborationClass.WEAK_CORROBORATION,
    CorroborationClass.MODERATE_CORROBORATION,
    CorroborationClass.STRONG_CORROBORATION,
]


@dataclass
class ClassMetrics:
    """Metrics for a single class."""
    class_name: str
    support: int  # Number of examples
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    is_unstable: bool = False  # True if support <= 2


@dataclass
class ConfusionMatrix:
    """
    Confusion matrix for multi-class or binary classification.

    matrix[i][j] = count of cases where true label is classes[i]
    and predicted label is classes[j].
    """
    classes: list[str]
    matrix: list[list[int]]


@dataclass
class CorroborationEvalResult:
    """
    Complete evaluation result for corroboration classification.

    Reports metrics for the 4-class corroboration taxonomy with
    explicit support counts and instability flags.
    """
    total_cases: int
    correct: int
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    per_class: list[ClassMetrics]
    confusion: ConfusionMatrix
    disclaimer: str = (
        "This is a small synthetic engineering benchmark and is not "
        "statistically representative of production performance."
    )


@dataclass
class ContradictionEvalResult:
    """
    Complete evaluation result for binary contradiction detection.
    """
    total_cases: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float
    support_present: int  # Number of CONTRADICTION_PRESENT cases
    support_absent: int   # Number of CONTRADICTION_ABSENT cases
    is_unstable: bool = False
    disclaimer: str = (
        "This is a small synthetic engineering benchmark and is not "
        "statistically representative of production performance."
    )


def compute_corroboration_metrics(
    true_labels: list[CorroborationClass],
    predicted_labels: list[CorroborationClass],
) -> CorroborationEvalResult:
    """
    Compute 4-class corroboration classification metrics.

    Args:
        true_labels: Ground-truth corroboration classes
        predicted_labels: ECI-derived corroboration classes

    Returns:
        CorroborationEvalResult with accuracy, macro P/R/F1, per-class metrics, confusion matrix
    """
    assert len(true_labels) == len(predicted_labels), "Label lists must have same length"
    n = len(true_labels)

    if n == 0:
        return CorroborationEvalResult(
            total_cases=0, correct=0, accuracy=0.0,
            macro_precision=0.0, macro_recall=0.0, macro_f1=0.0,
            per_class=[], confusion=ConfusionMatrix(classes=[], matrix=[]),
        )

    # Build confusion matrix
    class_names = [c.value for c in CORROBORATION_CLASSES]
    class_idx = {c: i for i, c in enumerate(CORROBORATION_CLASSES)}
    cm = [[0] * len(CORROBORATION_CLASSES) for _ in CORROBORATION_CLASSES]

    correct = 0
    for true, pred in zip(true_labels, predicted_labels):
        i = class_idx[true]
        j = class_idx[pred]
        cm[i][j] += 1
        if true == pred:
            correct += 1

    # Per-class metrics
    per_class: list[ClassMetrics] = []
    for idx, cls in enumerate(CORROBORATION_CLASSES):
        tp = cm[idx][idx]
        fp = sum(cm[j][idx] for j in range(len(CORROBORATION_CLASSES))) - tp
        fn = sum(cm[idx][j] for j in range(len(CORROBORATION_CLASSES))) - tp
        support = sum(cm[idx])

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        per_class.append(ClassMetrics(
            class_name=cls.value,
            support=support,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            is_unstable=support <= 2,
        ))

    # Macro averages (all classes weighted equally)
    classes_with_support = [c for c in per_class if c.support > 0]
    if classes_with_support:
        macro_p = sum(c.precision for c in classes_with_support) / len(classes_with_support)
        macro_r = sum(c.recall for c in classes_with_support) / len(classes_with_support)
        macro_f1 = sum(c.f1 for c in classes_with_support) / len(classes_with_support)
    else:
        macro_p = macro_r = macro_f1 = 0.0

    return CorroborationEvalResult(
        total_cases=n,
        correct=correct,
        accuracy=round(correct / n, 4),
        macro_precision=round(macro_p, 4),
        macro_recall=round(macro_r, 4),
        macro_f1=round(macro_f1, 4),
        per_class=per_class,
        confusion=ConfusionMatrix(classes=class_names, matrix=cm),
    )


def compute_contradiction_metrics(
    true_states: list[ContradictionState],
    predicted_states: list[ContradictionState],
) -> ContradictionEvalResult:
    """
    Compute binary contradiction detection metrics.

    Positive = CONTRADICTION_PRESENT
    Negative = CONTRADICTION_ABSENT

    Args:
        true_states: Ground-truth contradiction states
        predicted_states: System-detected contradiction states

    Returns:
        ContradictionEvalResult with precision, recall, F1
    """
    assert len(true_states) == len(predicted_states), "State lists must have same length"
    n = len(true_states)

    tp = fp = tn = fn = 0
    for true, pred in zip(true_states, predicted_states):
        is_true_pos = true == ContradictionState.CONTRADICTION_PRESENT
        is_pred_pos = pred == ContradictionState.CONTRADICTION_PRESENT

        if is_true_pos and is_pred_pos:
            tp += 1
        elif not is_true_pos and is_pred_pos:
            fp += 1
        elif not is_true_pos and not is_pred_pos:
            tn += 1
        else:
            fn += 1

    support_present = sum(1 for s in true_states if s == ContradictionState.CONTRADICTION_PRESENT)
    support_absent = n - support_present

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return ContradictionEvalResult(
        total_cases=n,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        support_present=support_present,
        support_absent=support_absent,
        is_unstable=support_present <= 2 or support_absent <= 2,
    )
