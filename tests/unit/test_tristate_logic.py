"""Tests for Tri-State Readiness Model and Kleene 3-Valued Logic."""

import pytest
from backend.domain.common.state import ReadinessState
from backend.domain.errors.exceptions import InvariantViolationException


class TestTriStateKleeneLogic:
    """Unit tests verifying all mathematical properties of Kleene 3-valued algebra."""

    @pytest.mark.parametrize(
        "left,right,expected",
        [
            # Conjunction (AND) truth table
            (ReadinessState.READY, ReadinessState.READY, ReadinessState.READY),
            (ReadinessState.READY, ReadinessState.UNKNOWN, ReadinessState.UNKNOWN),
            (ReadinessState.READY, ReadinessState.BLOCKED, ReadinessState.BLOCKED),
            (ReadinessState.UNKNOWN, ReadinessState.READY, ReadinessState.UNKNOWN),
            (ReadinessState.UNKNOWN, ReadinessState.UNKNOWN, ReadinessState.UNKNOWN),
            (ReadinessState.UNKNOWN, ReadinessState.BLOCKED, ReadinessState.BLOCKED),
            (ReadinessState.BLOCKED, ReadinessState.READY, ReadinessState.BLOCKED),
            (ReadinessState.BLOCKED, ReadinessState.UNKNOWN, ReadinessState.BLOCKED),
            (ReadinessState.BLOCKED, ReadinessState.BLOCKED, ReadinessState.BLOCKED),
        ],
    )
    def test_conjunction_truth_table(
        self, left: ReadinessState, right: ReadinessState, expected: ReadinessState
    ) -> None:
        """Every combination of Kleene AND must match the specification."""
        assert left.conjunction(right) == expected
        # Test operator overload &
        assert (left & right) == expected

    @pytest.mark.parametrize(
        "left,right,expected",
        [
            # Disjunction (OR) truth table
            (ReadinessState.READY, ReadinessState.READY, ReadinessState.READY),
            (ReadinessState.READY, ReadinessState.UNKNOWN, ReadinessState.READY),
            (ReadinessState.READY, ReadinessState.BLOCKED, ReadinessState.READY),
            (ReadinessState.UNKNOWN, ReadinessState.READY, ReadinessState.READY),
            (ReadinessState.UNKNOWN, ReadinessState.UNKNOWN, ReadinessState.UNKNOWN),
            (ReadinessState.UNKNOWN, ReadinessState.BLOCKED, ReadinessState.UNKNOWN),
            (ReadinessState.BLOCKED, ReadinessState.READY, ReadinessState.READY),
            (ReadinessState.BLOCKED, ReadinessState.UNKNOWN, ReadinessState.UNKNOWN),
            (ReadinessState.BLOCKED, ReadinessState.BLOCKED, ReadinessState.BLOCKED),
        ],
    )
    def test_disjunction_truth_table(
        self, left: ReadinessState, right: ReadinessState, expected: ReadinessState
    ) -> None:
        """Every combination of Kleene OR must match the specification."""
        assert left.disjunction(right) == expected
        # Test operator overload |
        assert (left | right) == expected

    @pytest.mark.parametrize(
        "state,expected",
        [
            (ReadinessState.READY, ReadinessState.BLOCKED),
            (ReadinessState.BLOCKED, ReadinessState.READY),
            (ReadinessState.UNKNOWN, ReadinessState.UNKNOWN),
        ],
    )
    def test_negation_truth_table(self, state: ReadinessState, expected: ReadinessState) -> None:
        """Kleene negation NOT must invert READY/BLOCKED and keep UNKNOWN as UNKNOWN."""
        assert state.negation() == expected
        assert (~state) == expected

    def test_unknown_never_silently_converted_to_blocked(self) -> None:
        """CRITICAL INVARIANT: UNKNOWN is distinct and must never collapse to BLOCKED."""
        state = ReadinessState.UNKNOWN
        assert state != ReadinessState.BLOCKED
        assert state.is_unknown is True
        assert state.is_blocked is False
        assert state.is_ready is False

        # In conjunction with READY, UNKNOWN remains UNKNOWN, NOT BLOCKED
        result = ReadinessState.READY & ReadinessState.UNKNOWN
        assert result == ReadinessState.UNKNOWN
        assert result != ReadinessState.BLOCKED

    def test_aggregate_all_conjunction(self) -> None:
        """ReadinessState.all folds conjunction across an iterable."""
        assert ReadinessState.all([]) == ReadinessState.READY
        assert ReadinessState.all([ReadinessState.READY, ReadinessState.READY]) == ReadinessState.READY
        assert ReadinessState.all([ReadinessState.READY, ReadinessState.UNKNOWN]) == ReadinessState.UNKNOWN
        assert ReadinessState.all([ReadinessState.READY, ReadinessState.UNKNOWN, ReadinessState.BLOCKED]) == ReadinessState.BLOCKED

    def test_aggregate_any_disjunction(self) -> None:
        """ReadinessState.any folds disjunction across an iterable."""
        assert ReadinessState.any([]) == ReadinessState.BLOCKED
        assert ReadinessState.any([ReadinessState.BLOCKED, ReadinessState.BLOCKED]) == ReadinessState.BLOCKED
        assert ReadinessState.any([ReadinessState.BLOCKED, ReadinessState.UNKNOWN]) == ReadinessState.UNKNOWN
        assert ReadinessState.any([ReadinessState.BLOCKED, ReadinessState.READY]) == ReadinessState.READY

    def test_invalid_type_conjunction_disjunction_raises(self) -> None:
        """Attempting algebraic operation with non-ReadinessState raises domain exception."""
        with pytest.raises(InvariantViolationException):
            ReadinessState.READY.conjunction("TRUE")  # type: ignore

        with pytest.raises(InvariantViolationException):
            ReadinessState.READY.disjunction(123)  # type: ignore

    def test_from_str_parsing(self) -> None:
        """Valid string parsing with case normalization, invalid raises exception."""
        assert ReadinessState.from_str("ready") == ReadinessState.READY
        assert ReadinessState.from_str("BLOCKED") == ReadinessState.BLOCKED
        assert ReadinessState.from_str("  unknown ") == ReadinessState.UNKNOWN

        with pytest.raises(InvariantViolationException):
            ReadinessState.from_str("INVALID_STATE")
