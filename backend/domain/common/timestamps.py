"""Temporal value checks and timezone awareness utilities for PREQVIA domain."""

from datetime import datetime

from backend.domain.errors.exceptions import (
    InvalidTemporalRangeException,
    MissingTimezoneException,
)


def ensure_timezone_aware(dt: datetime, param_name: str = "timestamp") -> datetime:
    """Validates that a datetime object has an explicit timezone attached.
    
    Raises:
        MissingTimezoneException: If dt is naive (tzinfo is None or offset is None).
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise MissingTimezoneException(
            f"Datetime parameter '{param_name}' must be timezone-aware (received naive datetime: {dt.isoformat()})."
        )
    return dt


def validate_temporal_range(
    valid_from: datetime,
    valid_until: datetime | None,
    range_name: str = "temporal range",
) -> None:
    """Validates that valid_from and valid_until form a chronologically coherent range.
    
    Raises:
        MissingTimezoneException: If either timestamp is naive.
        InvalidTemporalRangeException: If valid_until precedes valid_from.
    """
    ensure_timezone_aware(valid_from, f"{range_name}.valid_from")
    if valid_until is not None:
        ensure_timezone_aware(valid_until, f"{range_name}.valid_until")
        if valid_until < valid_from:
            raise InvalidTemporalRangeException(
                f"Invalid {range_name}: valid_until ({valid_until.isoformat()}) "
                f"cannot precede valid_from ({valid_from.isoformat()})."
            )


def is_timestamp_within_range(
    target_time: datetime,
    valid_from: datetime,
    valid_until: datetime | None,
) -> bool:
    """Checks whether target_time is temporally enclosed within [valid_from, valid_until]."""
    ensure_timezone_aware(target_time, "target_time")
    ensure_timezone_aware(valid_from, "valid_from")
    if valid_until is not None:
        ensure_timezone_aware(valid_until, "valid_until")
        return valid_from <= target_time <= valid_until
    return valid_from <= target_time
