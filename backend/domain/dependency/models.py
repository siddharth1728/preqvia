"""Dependency models governing prerequisite relationships between requirements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.domain.common.types import RequirementCode
from backend.domain.errors.exceptions import InvariantViolationException


class DependencyType(str, Enum):
    """Semantic type of relationship between prerequisite requirements."""

    HARD_PREREQUISITE = "HARD_PREREQUISITE"
    TEMPORAL_SEQUENCE = "TEMPORAL_SEQUENCE"
    CONDITIONAL = "CONDITIONAL"


@dataclass(frozen=True)
class DependencyEdge:
    """Directed edge in the requirement dependency DAG.
    
    Indicates that upstream_code MUST be satisfied before downstream_code can proceed.
    """

    upstream_code: RequirementCode
    downstream_code: RequirementCode
    dependency_type: DependencyType = DependencyType.HARD_PREREQUISITE

    def __post_init__(self) -> None:
        if not isinstance(self.upstream_code, RequirementCode):
            object.__setattr__(self, "upstream_code", RequirementCode(self.upstream_code))
        if not isinstance(self.downstream_code, RequirementCode):
            object.__setattr__(self, "downstream_code", RequirementCode(self.downstream_code))
        if not isinstance(self.dependency_type, DependencyType):
            object.__setattr__(self, "dependency_type", DependencyType(self.dependency_type))
        if self.upstream_code == self.downstream_code:
            raise InvariantViolationException(
                f"Self-referential dependency is forbidden: '{self.upstream_code}' cannot depend on itself."
            )
