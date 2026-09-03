"""
Unit tests for evaluation metrics and benchmark runner.

Validates:
- Multi-class corroboration accuracy, precision, recall, F1
- Confusion matrix dimensions and accuracy
- Binary contradiction metrics (TP, FP, TN, FN)
- Edge cases: perfect accuracy, zero accuracy, empty inputs
- Instability flags for small sample sizes
"""

import pytest

from evaluation.ground_truth import (
    ContradictionState,
    CorroborationClass,
    eci_to_corroboration_class,
    has_contradiction_detected,
)
from evaluation.metrics import (
    compute_contradiction_metrics,
    compute_corroboration_metrics,
)


class TestEvaluationMetrics:
    """Tests for statistical evaluation metrics computation."""

    def test_corroboration_perfect_predictions(self):
        """Should calculate 1.0 accuracy and F1 when all predictions match ground truth."""
        labels = [
            CorroborationClass.STRONG_CORROBORATION,
            CorroborationClass.MODERATE_CORROBORATION,
            CorroborationClass.WEAK_CORROBORATION,
            CorroborationClass.NO_CORROBORATION,
        ]
        res = compute_corroboration_metrics(labels, labels)

        assert res.total_cases == 4
        assert res.correct == 4
        assert res.accuracy == 1.0
        assert res.macro_precision == 1.0
        assert res.macro_recall == 1.0
        assert res.macro_f1 == 1.0

        # Confusion matrix diagonal
        for i in range(4):
            assert res.confusion.matrix[i][i] == 1

    def test_corroboration_all_wrong_predictions(self):
        """Should calculate 0.0 accuracy when no predictions match ground truth."""
        true = [CorroborationClass.STRONG_CORROBORATION, CorroborationClass.STRONG_CORROBORATION]
        pred = [CorroborationClass.NO_CORROBORATION, CorroborationClass.NO_CORROBORATION]

        res = compute_corroboration_metrics(true, pred)
        assert res.accuracy == 0.0
        assert res.correct == 0

    def test_corroboration_unstable_class_flagging(self):
        """Classes with support <= 2 must be flagged as unstable."""
        true = [
            CorroborationClass.STRONG_CORROBORATION,
            CorroborationClass.STRONG_CORROBORATION,  # support = 2
            CorroborationClass.NO_CORROBORATION,
            CorroborationClass.NO_CORROBORATION,
            CorroborationClass.NO_CORROBORATION,      # support = 3
        ]
        pred = list(true)
        res = compute_corroboration_metrics(true, pred)

        strong_class = next(c for c in res.per_class if c.class_name == "strong_corroboration")
        no_class = next(c for c in res.per_class if c.class_name == "no_corroboration")

        assert strong_class.is_unstable is True
        assert no_class.is_unstable is False

    def test_contradiction_metrics_binary(self):
        """Should compute TP, FP, TN, FN correctly for contradiction detection."""
        true = [
            ContradictionState.CONTRADICTION_PRESENT,  # TP
            ContradictionState.CONTRADICTION_PRESENT,  # FN
            ContradictionState.CONTRADICTION_ABSENT,   # TN
            ContradictionState.CONTRADICTION_ABSENT,   # FP
        ]
        pred = [
            ContradictionState.CONTRADICTION_PRESENT,
            ContradictionState.CONTRADICTION_ABSENT,
            ContradictionState.CONTRADICTION_ABSENT,
            ContradictionState.CONTRADICTION_PRESENT,
        ]

        res = compute_contradiction_metrics(true, pred)
        assert res.true_positives == 1
        assert res.false_negatives == 1
        assert res.true_negatives == 1
        assert res.false_positives == 1
        assert res.precision == 0.5
        assert res.recall == 0.5
        assert res.f1 == 0.5

    def test_empty_metrics_handling(self):
        """Empty inputs should return zeroed results gracefully without division errors."""
        res_corrob = compute_corroboration_metrics([], [])
        assert res_corrob.total_cases == 0
        assert res_corrob.accuracy == 0.0

        res_contra = compute_contradiction_metrics([], [])
        assert res_contra.total_cases == 0
        assert res_contra.f1 == 0.0

    def test_eci_to_corroboration_class_policy(self):
        """Tests the documented classification policy mapping ECI integers to classes."""
        assert eci_to_corroboration_class(0) == CorroborationClass.NO_CORROBORATION
        assert eci_to_corroboration_class(1) == CorroborationClass.WEAK_CORROBORATION
        assert eci_to_corroboration_class(29) == CorroborationClass.WEAK_CORROBORATION
        assert eci_to_corroboration_class(30) == CorroborationClass.MODERATE_CORROBORATION
        assert eci_to_corroboration_class(59) == CorroborationClass.MODERATE_CORROBORATION
        assert eci_to_corroboration_class(60) == CorroborationClass.STRONG_CORROBORATION
        assert eci_to_corroboration_class(100) == CorroborationClass.STRONG_CORROBORATION

    def test_has_contradiction_detected(self):
        """Tests contradiction detection flag helper."""
        assert has_contradiction_detected(["Conflict between A and B"]) is True
        assert has_contradiction_detected([]) is False
