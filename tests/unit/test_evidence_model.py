"""Tests for EvidenceRecord and EvidenceVerificationRecord models."""

from datetime import datetime, timezone
import pytest

from backend.domain.common.types import EvidenceCode, SubjectId
from backend.domain.errors.exceptions import (
    InvalidTemporalRangeException,
    InvariantViolationException,
    MissingTimezoneException,
    RevokedEvidenceException,
)
from backend.domain.evidence.models import (
    EvidenceRecord,
    EvidenceType,
    EvidenceVerificationRecord,
    VerificationStatus,
    VerifierType,
)


class TestEvidenceModel:
    """Verifies evidence lifecycle, validity intervals, revocation, and verification separation."""

    def test_evidence_construction_success(self) -> None:
        """Valid EvidenceRecord is created and immutable."""
        valid_from = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        valid_until = datetime(2026, 6, 30, 23, 59, tzinfo=timezone.utc)

        ev = EvidenceRecord(
            evidence_id="EV_001",
            subject_id=SubjectId("STU_1001"),
            evidence_code=EvidenceCode("BONAFIDE_CERTIFICATE"),
            evidence_type=EvidenceType.DOCUMENT,
            payload_data={"certificate_num": "BON-1234"},
            valid_from=valid_from,
            valid_until=valid_until,
        )

        assert ev.evidence_id == "EV_001"
        assert ev.subject_id == "STU_1001"
        assert ev.evidence_code == "BONAFIDE_CERTIFICATE"
        assert ev.evidence_type == EvidenceType.DOCUMENT
        assert ev.payload_data["certificate_num"] == "BON-1234"
        assert ev.is_revoked is False

    def test_evidence_temporal_validity_evaluation(self) -> None:
        """is_valid_at checks timestamps properly."""
        valid_from = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        valid_until = datetime(2026, 6, 30, 23, 59, tzinfo=timezone.utc)

        ev = EvidenceRecord(
            evidence_id="EV_001",
            subject_id=SubjectId("STU_1001"),
            evidence_code=EvidenceCode("BONAFIDE_CERTIFICATE"),
            evidence_type=EvidenceType.DOCUMENT,
            valid_from=valid_from,
            valid_until=valid_until,
        )

        within = datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc)
        before = datetime(2025, 12, 31, 23, 59, tzinfo=timezone.utc)
        expired = datetime(2026, 7, 1, 0, 0, tzinfo=timezone.utc)

        assert ev.is_valid_at(within) is True
        assert ev.is_valid_at(before) is False
        assert ev.is_valid_at(expired) is False

    def test_invalid_temporal_range_raises_exception(self) -> None:
        """valid_until before valid_from raises InvalidTemporalRangeException."""
        valid_from = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)
        valid_until = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)

        with pytest.raises(InvalidTemporalRangeException):
            EvidenceRecord(
                evidence_id="EV_002",
                subject_id=SubjectId("STU_1001"),
                evidence_code=EvidenceCode("INCOME_CERTIFICATE"),
                evidence_type=EvidenceType.DOCUMENT,
                valid_from=valid_from,
                valid_until=valid_until,
            )

    def test_revoked_evidence_is_never_valid(self) -> None:
        """Revoked evidence returns False for is_valid_at even within valid range."""
        valid_from = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        valid_until = datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc)
        revoked_time = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)

        ev = EvidenceRecord(
            evidence_id="EV_003",
            subject_id=SubjectId("STU_1001"),
            evidence_code=EvidenceCode("INCOME_CERTIFICATE"),
            evidence_type=EvidenceType.DOCUMENT,
            valid_from=valid_from,
            valid_until=valid_until,
            revoked_at=revoked_time,
            revocation_reason="Fraudulent certificate detected by college office",
        )

        assert ev.is_revoked is True
        within = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
        assert ev.is_valid_at(within) is False

    def test_revocation_method_returns_new_immutable_instance(self) -> None:
        """Calling ev.revoke() returns a new instance and leaves original unchanged."""
        valid_from = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        ev = EvidenceRecord(
            evidence_id="EV_004",
            subject_id=SubjectId("STU_1001"),
            evidence_code=EvidenceCode("BONAFIDE_CERTIFICATE"),
            evidence_type=EvidenceType.DOCUMENT,
            valid_from=valid_from,
        )

        rev_time = datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc)
        revoked_ev = ev.revoke(rev_time, "Issued in error")

        assert ev.is_revoked is False
        assert revoked_ev.is_revoked is True
        assert revoked_ev.revocation_reason == "Issued in error"
        assert revoked_ev.revoked_at == rev_time

        # Revoking already revoked record raises RevokedEvidenceException
        with pytest.raises(RevokedEvidenceException):
            revoked_ev.revoke(rev_time, "Duplicate revocation attempt")

    def test_revocation_without_reason_raises(self) -> None:
        """Revoking without reason raises InvariantViolationException."""
        valid_from = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
        ev = EvidenceRecord(
            evidence_id="EV_005",
            subject_id=SubjectId("STU_1001"),
            evidence_code=EvidenceCode("BONAFIDE_CERTIFICATE"),
            evidence_type=EvidenceType.DOCUMENT,
            valid_from=valid_from,
        )

        with pytest.raises(InvariantViolationException):
            ev.revoke(datetime.now(timezone.utc), "")

    def test_evidence_verification_record_decoupling(self) -> None:
        """Verification is a separate domain object from evidence."""
        ver_time = datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc)
        ver = EvidenceVerificationRecord(
            verification_id="VER_001",
            evidence_id="EV_001",
            verifier_type=VerifierType.MANUAL_ADMIN,
            verifier_identity="admin_clerk_sharma",
            status=VerificationStatus.VERIFIED,
            verified_at=ver_time,
            notes="Physical stamp matched against registry",
        )

        assert ver.is_verified is True
        assert ver.verifier_type == VerifierType.MANUAL_ADMIN
        assert ver.verified_at == ver_time

        # Rejected verification
        ver_rejected = EvidenceVerificationRecord(
            verification_id="VER_002",
            evidence_id="EV_001",
            verifier_type=VerifierType.SYSTEM_AUTOMATED,
            verifier_identity="auto_ocr_bot",
            status=VerificationStatus.REJECTED,
            verified_at=ver_time,
        )
        assert ver_rejected.is_verified is False
