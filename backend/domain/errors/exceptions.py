"""PREQVIA Domain Exceptions.

All domain exceptions inherit from DomainException to ensure clean separation
from standard library or infrastructure exceptions.
"""

from typing import Any


class DomainException(Exception):
    """Base exception for all PREQVIA domain errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvariantViolationException(DomainException):
    """Raised when an entity or value object violates a domain invariant."""
    pass


class InvalidIdentifierException(InvariantViolationException):
    """Raised when an identifier, code, or key fails format constraints."""
    pass


class MissingTimezoneException(InvariantViolationException):
    """Raised when a naive datetime is supplied where timezone awareness is required."""
    pass


class InvalidTemporalRangeException(InvariantViolationException):
    """Raised when a time interval has an end timestamp prior to its start timestamp."""
    pass


class RevokedEvidenceException(DomainException):
    """Raised when attempting to use or validate revoked evidence."""
    pass


class CyclicDependencyException(DomainException):
    """Raised when a requirement dependency cycle is detected in a catalog graph."""
    pass
