"""Actionable remediation domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.domain.common.types import LocationCode, RequirementCode
from backend.domain.errors.exceptions import InvariantViolationException


class RemediationActionType(str, Enum):
    """Categorization of actionable next steps for a blocked or unknown state."""

    OBTAIN_DOCUMENT = "OBTAIN_DOCUMENT"
    OBTAIN_SIGNATURE = "OBTAIN_SIGNATURE"
    RESCHEDULE_TIME = "RESCHEDULE_TIME"
    VERIFY_EVIDENCE = "VERIFY_EVIDENCE"
    UPDATE_PROFILE = "UPDATE_PROFILE"
    RESOLVE_PREREQUISITE = "RESOLVE_PREREQUISITE"


@dataclass(frozen=True)
class ActionableRemediation:
    """Deterministic step-by-step guidance instructing the user how to unblock their task.
    
    Contains pure domain data: what is wrong, what must be done, and in what order.
    """

    step_order: int
    requirement_code: RequirementCode
    action_type: RemediationActionType
    title: str
    instruction: str
    target_location: LocationCode | None = None

    def __post_init__(self) -> None:
        if self.step_order < 1:
            raise InvariantViolationException(
                f"step_order must be a positive integer >= 1 (received: {self.step_order})."
            )
        if not isinstance(self.requirement_code, RequirementCode):
            object.__setattr__(self, "requirement_code", RequirementCode(self.requirement_code))
        if not isinstance(self.action_type, RemediationActionType):
            object.__setattr__(self, "action_type", RemediationActionType(self.action_type))
        if not self.title or not self.title.strip():
            raise InvariantViolationException("ActionableRemediation title cannot be empty.")
        if not self.instruction or not self.instruction.strip():
            raise InvariantViolationException("ActionableRemediation instruction cannot be empty.")
        if self.target_location is not None and not isinstance(self.target_location, LocationCode):
            object.__setattr__(self, "target_location", LocationCode(self.target_location))
