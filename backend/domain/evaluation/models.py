"""Evaluation and EvaluationNode domain models representing feasibility determinations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Sequence

from backend.domain.common.state import ReadinessState
from backend.domain.common.timestamps import ensure_timezone_aware
from backend.domain.common.types import (
    LocationCode,
    RequirementCode,
    ServiceCode,
    SubjectId,
)
from backend.domain.errors.exceptions import InvariantViolationException
from backend.domain.remediation.models import ActionableRemediation


class NodeVerdictStatus(str, Enum):
    """Feasibility outcome for an individual requirement node."""

    SATISFIED = "SATISFIED"
    UNSATISFIED = "UNSATISFIED"
    BLOCKED_BY_DEPENDENCY = "BLOCKED_BY_DEPENDENCY"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class EvaluationNode:
    """Individual requirement verdict within the dependency graph.
    
    Distinguishes whether an unsatisfied state is a direct failure (UNSATISFIED)
    or caused by an upstream prerequisite failure (BLOCKED_BY_DEPENDENCY).
    """

    requirement_code: RequirementCode
    status: NodeVerdictStatus
    matched_evidence_id: str | None = None
    blocker_reason: str | None = None
    blocked_by_codes: tuple[RequirementCode, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.requirement_code, RequirementCode):
            object.__setattr__(self, "requirement_code", RequirementCode(self.requirement_code))
        if not isinstance(self.status, NodeVerdictStatus):
            object.__setattr__(self, "status", NodeVerdictStatus(self.status))
        if not isinstance(self.blocked_by_codes, tuple):
            object.__setattr__(
                self,
                "blocked_by_codes",
                tuple(
                    c if isinstance(c, RequirementCode) else RequirementCode(c)
                    for c in self.blocked_by_codes
                ),
            )
        if self.status == NodeVerdictStatus.BLOCKED_BY_DEPENDENCY and not self.blocked_by_codes:
            raise InvariantViolationException(
                f"Node '{self.requirement_code}' marked BLOCKED_BY_DEPENDENCY must specify at least one blocked_by code."
            )


@dataclass(frozen=True)
class Evaluation:
    """Immutable determination record of task feasibility.
    
    Contains the overall tri-state outcome, summary reason, per-requirement
    verdict nodes, and sequential remediation actions.
    """

    evaluation_id: str
    subject_id: SubjectId
    service_code: ServiceCode
    location_code: LocationCode
    target_time: datetime
    overall_state: ReadinessState
    summary_reason: str
    nodes: tuple[EvaluationNode, ...] = ()
    remediations: tuple[ActionableRemediation, ...] = ()
    evaluated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not self.evaluation_id or not self.evaluation_id.strip():
            raise InvariantViolationException("evaluation_id cannot be empty.")
        if not isinstance(self.subject_id, SubjectId):
            object.__setattr__(self, "subject_id", SubjectId(self.subject_id))
        if not isinstance(self.service_code, ServiceCode):
            object.__setattr__(self, "service_code", ServiceCode(self.service_code))
        if not isinstance(self.location_code, LocationCode):
            object.__setattr__(self, "location_code", LocationCode(self.location_code))
        if not isinstance(self.overall_state, ReadinessState):
            object.__setattr__(self, "overall_state", ReadinessState.from_str(str(self.overall_state)))
        if not self.summary_reason or not self.summary_reason.strip():
            raise InvariantViolationException("summary_reason cannot be empty.")

        ensure_timezone_aware(self.target_time, "target_time")
        ensure_timezone_aware(self.evaluated_at, "evaluated_at")

        if not isinstance(self.nodes, tuple):
            object.__setattr__(self, "nodes", tuple(self.nodes))
        if not isinstance(self.remediations, tuple):
            object.__setattr__(self, "remediations", tuple(self.remediations))

    @property
    def is_ready(self) -> bool:
        """Returns True if the task is completely ready to be performed."""
        return self.overall_state == ReadinessState.READY

    @property
    def is_blocked(self) -> bool:
        """Returns True if the task is blocked by one or more conditions."""
        return self.overall_state == ReadinessState.BLOCKED

    @property
    def is_unknown(self) -> bool:
        """Returns True if the feasibility outcome is unknown."""
        return self.overall_state == ReadinessState.UNKNOWN
