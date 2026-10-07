"""Evidence domain models and verification records."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from backend.domain.common.timestamps import (
    ensure_timezone_aware,
    is_timestamp_within_range,
    validate_temporal_range,
)
from backend.domain.common.types import EvidenceCode, SubjectId
from backend.domain.errors.exceptions import (
    InvariantViolationException,
    RevokedEvidenceException,
)


class EvidenceType(str, Enum):
    """Categorization of evidence provided by or for a subject."""

    DOCUMENT = "DOCUMENT"
    APPROVAL = "APPROVAL"
    ATTESTATION = "ATTESTATION"
    ATTRIBUTE = "ATTRIBUTE"


class VerificationStatus(str, Enum):
    """Status of an administrative or system verification."""

    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    UNVERIFIABLE = "UNVERIFIABLE"
    PENDING = "PENDING"


class VerifierType(str, Enum):
    """Type of entity performing evidence verification."""

    SYSTEM_AUTOMATED = "SYSTEM_AUTOMATED"
    MANUAL_ADMIN = "MANUAL_ADMIN"
    THIRD_PARTY_API = "THIRD_PARTY_API"


@dataclass(frozen=True)
class EvidenceVerificationRecord:
    """Immutable attestation of authenticity for an evidence item.
    
    Decoupled strictly from EvidenceRecord to preserve separation of concerns.
    """

    verification_id: str
    evidence_id: str
    verifier_type: VerifierType
    verifier_identity: str
    status: VerificationStatus
    verified_at: datetime
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.verification_id or not self.verification_id.strip():
            raise InvariantViolationException("verification_id cannot be empty.")
        if not self.evidence_id or not self.evidence_id.strip():
            raise InvariantViolationException("evidence_id cannot be empty.")
        if not self.verifier_identity or not self.verifier_identity.strip():
            raise InvariantViolationException("verifier_identity cannot be empty.")
        if not isinstance(self.verifier_type, VerifierType):
            object.__setattr__(self, "verifier_type", VerifierType(self.verifier_type))
        if not isinstance(self.status, VerificationStatus):
            object.__setattr__(self, "status", VerificationStatus(self.status))
        ensure_timezone_aware(self.verified_at, "verified_at")

    @property
    def is_verified(self) -> bool:
        """Returns True if this verification record confirms validity."""
        return self.status == VerificationStatus.VERIFIED


@dataclass(frozen=True)
class EvidenceRecord:
    """Immutable assertion of evidence held by or for a subject.
    
    Evidence captures WHAT IS HELD, its validity window, and revocation status.
    It does not specify what a service demands (which is RequirementSpecification).
    """

    evidence_id: str
    subject_id: SubjectId
    evidence_code: EvidenceCode
    evidence_type: EvidenceType
    payload_data: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    valid_from: datetime = field(default_factory=lambda: datetime.min)
    valid_until: datetime | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id or not self.evidence_id.strip():
            raise InvariantViolationException("evidence_id cannot be empty.")
        if not isinstance(self.subject_id, SubjectId):
            object.__setattr__(self, "subject_id", SubjectId(self.subject_id))
        if not isinstance(self.evidence_code, EvidenceCode):
            object.__setattr__(self, "evidence_code", EvidenceCode(self.evidence_code))
        if not isinstance(self.evidence_type, EvidenceType):
            object.__setattr__(self, "evidence_type", EvidenceType(self.evidence_type))
        if isinstance(self.payload_data, dict):
            object.__setattr__(self, "payload_data", MappingProxyType(dict(self.payload_data)))

        # Validate temporal coherence
        validate_temporal_range(self.valid_from, self.valid_until, "evidence validity range")

        if self.revoked_at is not None:
            ensure_timezone_aware(self.revoked_at, "revoked_at")
            if not self.revocation_reason or not self.revocation_reason.strip():
                raise InvariantViolationException(
                    "Revoked evidence must have an explicit non-empty revocation_reason."
                )

    @property
    def is_revoked(self) -> bool:
        """Returns True if the evidence has been explicitly revoked."""
        return self.revoked_at is not None

    def is_valid_at(self, target_time: datetime) -> bool:
        """Determines whether this evidence is chronologically valid at target_time.
        
        Revoked evidence is ALWAYS invalid regardless of target_time.
        """
        ensure_timezone_aware(target_time, "target_time")
        if self.is_revoked:
            return False
        return is_timestamp_within_range(target_time, self.valid_from, self.valid_until)

    def revoke(self, revocation_time: datetime, reason: str) -> EvidenceRecord:
        """Creates a new immutable EvidenceRecord instance marked as revoked."""
        ensure_timezone_aware(revocation_time, "revocation_time")
        if not reason or not reason.strip():
            raise InvariantViolationException("Revocation reason cannot be empty.")
        if self.is_revoked:
            raise RevokedEvidenceException(
                f"Evidence '{self.evidence_id}' is already revoked at {self.revoked_at}."
            )
        return replace(
            self,
            revoked_at=revocation_time,
            revocation_reason=reason.strip(),
        )
