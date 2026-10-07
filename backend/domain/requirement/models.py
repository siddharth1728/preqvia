"""Requirement domain models and specifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from backend.domain.common.types import EvidenceCode, RequirementCode
from backend.domain.errors.exceptions import InvariantViolationException


class RequirementCategory(str, Enum):
    """Categorization of requirements demanded by a service."""

    DOCUMENT = "DOCUMENT"
    APPROVAL = "APPROVAL"
    ATTESTATION = "ATTESTATION"
    ELIGIBILITY_CRITERION = "ELIGIBILITY_CRITERION"
    SERVICE_AVAILABILITY = "SERVICE_AVAILABILITY"
    PREREQUISITE_TASK = "PREREQUISITE_TASK"


@dataclass(frozen=True)
class ValidationSpec:
    """Specification of what evidence qualifies to satisfy a requirement."""

    evidence_code: EvidenceCode
    acceptable_types: tuple[str, ...] = ("DOCUMENT",)
    max_age_days: int | None = None
    required_verification_status: str = "VERIFIED"
    match_attributes: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_code, EvidenceCode):
            object.__setattr__(self, "evidence_code", EvidenceCode(self.evidence_code))
        if self.max_age_days is not None and self.max_age_days < 0:
            raise InvariantViolationException(
                f"max_age_days cannot be negative (received: {self.max_age_days})."
            )
        if isinstance(self.match_attributes, dict):
            object.__setattr__(
                self, "match_attributes", MappingProxyType(dict(self.match_attributes))
            )


@dataclass(frozen=True)
class RequirementSpecification:
    """Immutable catalog requirement demanded by a service.
    
    A RequirementSpecification defines WHAT is demanded. It does not store
    what a user has submitted (which is modeled separately as EvidenceRecord).
    """

    code: RequirementCode
    category: RequirementCategory
    title: str
    description: str = ""
    is_mandatory: bool = True
    applicability_rule: Mapping[str, Any] | None = None
    validation_spec: ValidationSpec | None = None
    source_reference: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, RequirementCode):
            object.__setattr__(self, "code", RequirementCode(self.code))
        if not isinstance(self.category, RequirementCategory):
            try:
                object.__setattr__(self, "category", RequirementCategory(self.category))
            except ValueError:
                raise InvariantViolationException(
                    f"Invalid requirement category '{self.category}'."
                )
        if not self.title or not self.title.strip():
            raise InvariantViolationException("RequirementSpecification title cannot be empty.")
        if self.applicability_rule is not None and isinstance(self.applicability_rule, dict):
            object.__setattr__(
                self, "applicability_rule", MappingProxyType(dict(self.applicability_rule))
            )
        if self.category == RequirementCategory.DOCUMENT and self.validation_spec is None:
            raise InvariantViolationException(
                f"Document requirement '{self.code}' must define a validation_spec."
            )

    @property
    def is_advisory(self) -> bool:
        """Returns True if the requirement is advisory/optional rather than mandatory."""
        return not self.is_mandatory
