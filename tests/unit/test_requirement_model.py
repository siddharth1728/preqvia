"""Tests for RequirementSpecification and ValidationSpec domain models."""

import pytest
from backend.domain.common.types import EvidenceCode, RequirementCode
from backend.domain.errors.exceptions import InvariantViolationException
from backend.domain.requirement.models import (
    RequirementCategory,
    RequirementSpecification,
    ValidationSpec,
)


class TestRequirementModel:
    """Verifies declarative requirement specifications and validation criteria."""

    def test_document_requirement_construction(self) -> None:
        """Document requirement with validation spec is created properly."""
        val_spec = ValidationSpec(
            evidence_code=EvidenceCode("BONAFIDE_CERTIFICATE"),
            acceptable_types=("DOCUMENT",),
            max_age_days=180,
            required_verification_status="VERIFIED",
        )

        req = RequirementSpecification(
            code=RequirementCode("REQ_BONAFIDE_CERT"),
            category=RequirementCategory.DOCUMENT,
            title="Valid Bonafide Certificate",
            description="Issued by registrar within last 6 months",
            is_mandatory=True,
            validation_spec=val_spec,
            source_reference="University Circular 42/2026 Section 4",
        )

        assert req.code == "REQ_BONAFIDE_CERT"
        assert req.category == RequirementCategory.DOCUMENT
        assert req.is_mandatory is True
        assert req.is_advisory is False
        assert req.validation_spec is not None
        assert req.validation_spec.evidence_code == "BONAFIDE_CERTIFICATE"
        assert req.validation_spec.max_age_days == 180

    def test_document_category_without_validation_spec_raises(self) -> None:
        """Document category requirements MUST define a validation_spec."""
        with pytest.raises(InvariantViolationException) as exc_info:
            RequirementSpecification(
                code=RequirementCode("REQ_INCOME_CERT"),
                category=RequirementCategory.DOCUMENT,
                title="Income Certificate",
                validation_spec=None,  # Missing!
            )
        assert "must define a validation_spec" in str(exc_info.value)

    def test_validation_spec_negative_max_age_raises(self) -> None:
        """max_age_days cannot be negative."""
        with pytest.raises(InvariantViolationException):
            ValidationSpec(
                evidence_code=EvidenceCode("INCOME_CERTIFICATE"),
                max_age_days=-1,
            )

    def test_empty_title_raises(self) -> None:
        """Requirement title cannot be empty or blank whitespace."""
        with pytest.raises(InvariantViolationException):
            RequirementSpecification(
                code=RequirementCode("REQ_APPROVAL"),
                category=RequirementCategory.APPROVAL,
                title="   ",
            )

    def test_advisory_requirement(self) -> None:
        """Advisory requirement has is_mandatory=False and is_advisory=True."""
        req = RequirementSpecification(
            code=RequirementCode("REQ_SPORTS_CERT"),
            category=RequirementCategory.ATTESTATION,
            title="Optional Sports Participation Certificate",
            is_mandatory=False,
        )
        assert req.is_mandatory is False
        assert req.is_advisory is True

    def test_immutable_applicability_rule(self) -> None:
        """Applicability rule mapping is frozen as read-only proxy."""
        rule_dict = {"==": [{"var": "caste"}, "SC"]}
        req = RequirementSpecification(
            code=RequirementCode("REQ_COMMUNITY_FEE_WAIVER"),
            category=RequirementCategory.ELIGIBILITY_CRITERION,
            title="Fee Waiver Eligibility",
            applicability_rule=rule_dict,
        )

        assert req.applicability_rule is not None
        assert req.applicability_rule["=="] == [{"var": "caste"}, "SC"]

        # Modifying original dict does not affect requirement specification
        rule_dict["=="] = ["altered"]
        assert req.applicability_rule["=="] == [{"var": "caste"}, "SC"]
