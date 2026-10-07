"""User task intent domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

from backend.domain.common.timestamps import ensure_timezone_aware
from backend.domain.common.types import (
    LocationCode,
    ServiceCode,
    SubjectId,
)


@dataclass(frozen=True)
class UserTaskIntent:
    """The user's specific real-world task attempt.
    
    Encapsulates: Who (subject_id), What (service_code), Where (location_code),
    When (target_time), and any user-supplied contextual attributes (context_data).
    """

    subject_id: SubjectId
    service_code: ServiceCode
    location_code: LocationCode
    target_time: datetime
    context_data: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.subject_id, SubjectId):
            object.__setattr__(self, "subject_id", SubjectId(self.subject_id))
        if not isinstance(self.service_code, ServiceCode):
            object.__setattr__(self, "service_code", ServiceCode(self.service_code))
        if not isinstance(self.location_code, LocationCode):
            object.__setattr__(self, "location_code", LocationCode(self.location_code))
        ensure_timezone_aware(self.target_time, "UserTaskIntent.target_time")
        if isinstance(self.context_data, dict):
            object.__setattr__(self, "context_data", MappingProxyType(dict(self.context_data)))
