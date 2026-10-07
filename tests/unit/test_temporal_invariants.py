"""Tests for Timezone Awareness and Temporal Range Invariants."""

from datetime import datetime, timezone
import pytest

from backend.domain.common.timestamps import (
    ensure_timezone_aware,
    is_timestamp_within_range,
    validate_temporal_range,
)
from backend.domain.errors.exceptions import (
    InvalidTemporalRangeException,
    MissingTimezoneException,
)


class TestTemporalInvariants:
    """Verifies strict timezone enforcement and chronological validity intervals."""

    def test_timezone_aware_datetime_accepted(self) -> None:
        """UTC and timezone-aware datetimes pass validation."""
        aware_utc = datetime(2026, 10, 8, 11, 0, tzinfo=timezone.utc)
        assert ensure_timezone_aware(aware_utc) == aware_utc

    def test_naive_datetime_raises_missing_timezone(self) -> None:
        """Naive datetimes strictly raise MissingTimezoneException."""
        naive_dt = datetime(2026, 10, 8, 11, 0)
        with pytest.raises(MissingTimezoneException) as exc_info:
            ensure_timezone_aware(naive_dt, "test_param")
        assert "must be timezone-aware" in str(exc_info.value)
        assert "test_param" in str(exc_info.value)

    def test_valid_temporal_range(self) -> None:
        """valid_until >= valid_from is valid."""
        start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc)
        validate_temporal_range(start, end)
        # Infinite end is also valid
        validate_temporal_range(start, None)

    def test_invalid_temporal_range_raises(self) -> None:
        """valid_until < valid_from raises InvalidTemporalRangeException."""
        start = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
        end = datetime(2026, 10, 8, 11, 0, tzinfo=timezone.utc)  # 1 hour earlier
        with pytest.raises(InvalidTemporalRangeException) as exc_info:
            validate_temporal_range(start, end)
        assert "cannot precede valid_from" in str(exc_info.value)

    def test_is_timestamp_within_range(self) -> None:
        """Checks temporal enclosure."""
        start = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc)

        before = datetime(2026, 5, 31, 23, 59, tzinfo=timezone.utc)
        during = datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc)
        after = datetime(2026, 12, 2, 0, 0, tzinfo=timezone.utc)

        assert is_timestamp_within_range(during, start, end) is True
        assert is_timestamp_within_range(before, start, end) is False
        assert is_timestamp_within_range(after, start, end) is False

        # Open-ended validity
        assert is_timestamp_within_range(during, start, None) is True
        assert is_timestamp_within_range(after, start, None) is True
        assert is_timestamp_within_range(before, start, None) is False
