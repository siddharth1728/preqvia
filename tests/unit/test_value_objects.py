"""Tests for Strongly Typed Value Objects and Identifiers."""

import pytest
from backend.domain.common.types import (
    EvidenceCode,
    LocationCode,
    OrganizationCode,
    RequirementCode,
    ServiceCode,
    SubjectId,
)
from backend.domain.errors.exceptions import InvalidIdentifierException


class TestValueObjects:
    """Verifies identifier patterns, immutability, and validation rules."""

    def test_valid_codes(self) -> None:
        """Valid codes are instantiated and comparable as strings."""
        req_code = RequirementCode("REQ_BONAFIDE_CERT")
        assert req_code == "REQ_BONAFIDE_CERT"
        assert repr(req_code) == "RequirementCode('REQ_BONAFIDE_CERT')"

        ev_code = EvidenceCode("BONAFIDE_CERTIFICATE")
        assert ev_code == "BONAFIDE_CERTIFICATE"

        srv_code = ServiceCode("SCHOLARSHIP_SUBMISSION")
        assert srv_code == "SCHOLARSHIP_SUBMISSION"

        org_code = OrganizationCode("COLLEGE_NIE_MYSORE")
        assert org_code == "COLLEGE_NIE_MYSORE"

        loc_code = LocationCode("COUNTER_ADMIN_03")
        assert loc_code == "COUNTER_ADMIN_03"

    @pytest.mark.parametrize(
        "invalid_code",
        [
            "",  # empty
            "   ",  # whitespace
            "req_lowercase",  # lowercase forbidden
            "123_STARTS_WITH_DIGIT",  # must start with uppercase letter
            "REQ-WITH-HYPHENS",  # hyphens forbidden (must be underscores)
            "REQ WITH SPACES",  # spaces forbidden
            "A" * 65,  # exceeds max length 64
        ],
    )
    def test_invalid_code_patterns_raise(self, invalid_code: str) -> None:
        """Malformed code strings raise InvalidIdentifierException."""
        with pytest.raises(InvalidIdentifierException):
            RequirementCode(invalid_code)

        with pytest.raises(InvalidIdentifierException):
            EvidenceCode(invalid_code)

    def test_subject_id_validation(self) -> None:
        """SubjectId must be a non-empty string within 128 characters."""
        subject = SubjectId("STU_2026_9941")
        assert subject == "STU_2026_9941"
        assert repr(subject) == "SubjectId('STU_2026_9941')"

        uuid_sub = SubjectId("3fa85f64-5717-4562-b3fc-2c963f66afa6")
        assert uuid_sub == "3fa85f64-5717-4562-b3fc-2c963f66afa6"

        with pytest.raises(InvalidIdentifierException):
            SubjectId("")

        with pytest.raises(InvalidIdentifierException):
            SubjectId("   ")

        with pytest.raises(InvalidIdentifierException):
            SubjectId("A" * 129)

    def test_non_string_types_raise(self) -> None:
        """Passing non-strings raises InvalidIdentifierException."""
        with pytest.raises(InvalidIdentifierException):
            RequirementCode(12345)  # type: ignore

        with pytest.raises(InvalidIdentifierException):
            SubjectId(None)  # type: ignore
