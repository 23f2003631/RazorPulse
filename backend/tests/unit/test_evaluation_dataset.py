"""
Unit tests for the synthetic evaluation dataset.

Validates:
- Exactly 25 cases
- Partition into 18 development and 7 held-out cases
- Coverage of all 12 archetypes (A through L)
- Uniqueness of case IDs
- Independence of ground truth labels
"""

import pytest

from evaluation.dataset import ALL_CASES, DEVELOPMENT_CASES, HELD_OUT_CASES
from evaluation.ground_truth import (
    ContradictionState,
    CorroborationClass,
    DatasetSplit,
    DifficultyLevel,
    EvalCase,
)


class TestEvaluationDataset:
    """Tests for dataset integrity and schema compliance."""

    def test_dataset_size_and_partitions(self):
        """Dataset must have exactly 25 cases with 18 dev / 7 held-out split."""
        assert len(ALL_CASES) == 25
        assert len(DEVELOPMENT_CASES) == 18
        assert len(HELD_OUT_CASES) == 7
        assert len(DEVELOPMENT_CASES) + len(HELD_OUT_CASES) == len(ALL_CASES)

    def test_case_ids_unique(self):
        """Every case must have a unique identifier."""
        case_ids = [c.case_id for c in ALL_CASES]
        assert len(case_ids) == len(set(case_ids)), "Duplicate case_id found in dataset"

    def test_all_12_archetypes_covered(self):
        """All 12 scenario archetypes (A through L) must be present."""
        expected_archetypes = {"A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"}
        found_archetypes = {c.archetype for c in ALL_CASES}
        missing = expected_archetypes - found_archetypes
        assert not missing, f"Missing archetypes: {missing}"

    def test_case_attributes_complete(self):
        """Every case must have complete merchant, anomaly, and ground truth attributes."""
        for case in ALL_CASES:
            assert isinstance(case, EvalCase)
            assert case.case_id, "case_id cannot be empty"
            assert case.merchant_name, f"Case {case.case_id} missing merchant_name"
            assert case.merchant_domain, f"Case {case.case_id} missing merchant_domain"
            assert case.occurred_at, f"Case {case.case_id} missing occurred_at"
            assert isinstance(case.expected_corroboration, CorroborationClass)
            assert isinstance(case.expected_contradiction, ContradictionState)
            assert isinstance(case.difficulty, DifficultyLevel)
            assert isinstance(case.split, DatasetSplit)

    def test_adversarial_cases_present(self):
        """Dataset must intentionally include difficult adversarial archetypes."""
        wrong_entity_cases = [c for c in ALL_CASES if c.archetype == "E"]
        wrong_date_cases = [c for c in ALL_CASES if c.archetype == "F"]
        post_anomaly_cases = [c for c in ALL_CASES if c.archetype == "G"]
        contradiction_cases = [c for c in ALL_CASES if c.archetype == "H"]
        duplicate_cases = [c for c in ALL_CASES if c.archetype == "I"]

        assert len(wrong_entity_cases) >= 2
        assert len(wrong_date_cases) >= 2
        assert len(post_anomaly_cases) >= 2
        assert len(contradiction_cases) >= 2
        assert len(duplicate_cases) >= 1

    def test_held_out_has_diverse_difficulty(self):
        """Held-out partition must not contain only trivial cases."""
        held_out_diffs = {c.difficulty for c in HELD_OUT_CASES}
        assert DifficultyLevel.HARD in held_out_diffs or DifficultyLevel.MEDIUM in held_out_diffs
