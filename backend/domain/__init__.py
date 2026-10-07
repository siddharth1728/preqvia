"""PREQVIA Pure Domain Layer.

Zero database, HTTP, framework, or filesystem dependencies.
100% deterministic and in-memory executable.
"""

from backend.domain.common.state import ReadinessState
from backend.domain.common.timestamps import (
    ensure_timezone_aware,
    is_timestamp_within_range,
    validate_temporal_range,
)
from backend.domain.common.types import (
    EvidenceCode,
    LocationCode,
    OrganizationCode,
    RequirementCode,
    ServiceCode,
    SubjectId,
)
from backend.domain.dependency.models import DependencyEdge, DependencyType
from backend.domain.errors.exceptions import (
    CyclicDependencyException,
    DomainException,
    InvalidIdentifierException,
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
from backend.domain.evaluation.models import (
    Evaluation,
    EvaluationNode,
    NodeVerdictStatus,
)
from backend.domain.remediation.models import (
    ActionableRemediation,
    RemediationActionType,
)
from backend.domain.requirement.models import (
    RequirementCategory,
    RequirementSpecification,
    ValidationSpec,
)
from backend.domain.service.models import (
    OperatingSchedule,
    ScheduleException,
    Service,
    ServiceVersion,
)
from backend.domain.task.models import UserTaskIntent

__all__ = [
    # State & Logic
    "ReadinessState",
    # Codes & Identifiers
    "RequirementCode",
    "EvidenceCode",
    "ServiceCode",
    "OrganizationCode",
    "LocationCode",
    "SubjectId",
    # Temporal utilities
    "ensure_timezone_aware",
    "validate_temporal_range",
    "is_timestamp_within_range",
    # Requirement Models
    "RequirementCategory",
    "ValidationSpec",
    "RequirementSpecification",
    # Evidence Models
    "EvidenceType",
    "VerificationStatus",
    "VerifierType",
    "EvidenceVerificationRecord",
    "EvidenceRecord",
    # Dependency Models
    "DependencyType",
    "DependencyEdge",
    # Service & Schedule Models
    "OperatingSchedule",
    "ScheduleException",
    "Service",
    "ServiceVersion",
    # Task Models
    "UserTaskIntent",
    # Remediation Models
    "RemediationActionType",
    "ActionableRemediation",
    # Evaluation Models
    "NodeVerdictStatus",
    "EvaluationNode",
    "Evaluation",
    # Errors
    "DomainException",
    "InvariantViolationException",
    "InvalidIdentifierException",
    "MissingTimezoneException",
    "InvalidTemporalRangeException",
    "RevokedEvidenceException",
    "CyclicDependencyException",
]
