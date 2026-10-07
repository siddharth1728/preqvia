"""Strongly typed Domain Value Objects for Identifiers and Codes.

Prevents primitive obsession while remaining lightweight, immutable,
and cleanly comparable.
"""

from __future__ import annotations

import re
from typing import Any

from backend.domain.errors.exceptions import InvalidIdentifierException

# Standard pattern: uppercase letters, digits, underscores. Must start with letter.
_CODE_REGEX = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")


class _ValidatedCode(str):
    """Base immutable string code with identifier pattern validation."""

    def __new__(cls, value: Any) -> _ValidatedCode:
        if not isinstance(value, str):
            raise InvalidIdentifierException(
                f"{cls.__name__} must be a string, received {type(value).__name__}."
            )
        cleaned = value.strip()
        if not _CODE_REGEX.match(cleaned):
            raise InvalidIdentifierException(
                f"Invalid {cls.__name__} '{value}'. Must match uppercase alphanumeric format "
                f"^[A-Z][A-Z0-9_]{{1,63}}$."
            )
        return super().__new__(cls, cleaned)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self}')"


class RequirementCode(_ValidatedCode):
    """Machine-readable code identifying a requirement specification (e.g., 'REQ_BONAFIDE_CERT')."""
    pass


class EvidenceCode(_ValidatedCode):
    """Machine-readable code identifying an evidence type (e.g., 'INCOME_CERTIFICATE')."""
    pass


class ServiceCode(_ValidatedCode):
    """Machine-readable code identifying a service catalog capability (e.g., 'SCHOLARSHIP_SUBMISSION')."""
    pass


class OrganizationCode(_ValidatedCode):
    """Machine-readable code identifying an institution or authority (e.g., 'COLLEGE_NIE')."""
    pass


class LocationCode(_ValidatedCode):
    """Machine-readable code identifying an administrative counter or office (e.g., 'COUNTER_ADMIN_03')."""
    pass


class SubjectId(str):
    """Unique identifier for a subject/user applicant."""

    def __new__(cls, value: Any) -> SubjectId:
        if not isinstance(value, str):
            raise InvalidIdentifierException(
                f"SubjectId must be a string, received {type(value).__name__}."
            )
        cleaned = value.strip()
        if not cleaned or len(cleaned) > 128:
            raise InvalidIdentifierException(
                f"SubjectId cannot be empty or exceed 128 characters (received: '{value}')."
            )
        return super().__new__(cls, cleaned)

    def __repr__(self) -> str:
        return f"SubjectId('{self}')"
