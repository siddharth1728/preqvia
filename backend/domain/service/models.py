"""Service catalog domain models, versioning, and operating schedules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Sequence

from backend.domain.common.timestamps import (
    ensure_timezone_aware,
    validate_temporal_range,
)
from backend.domain.common.types import (
    OrganizationCode,
    RequirementCode,
    ServiceCode,
)
from backend.domain.dependency.models import DependencyEdge
from backend.domain.errors.exceptions import InvariantViolationException
from backend.domain.requirement.models import RequirementSpecification


@dataclass(frozen=True)
class OperatingSchedule:
    """Recurring weekly schedule for an administrative service counter.
    
    day_of_week follows ISO / Python datetime.weekday convention:
    0 = Monday, 1 = Tuesday, ..., 6 = Sunday.
    """

    day_of_week: int
    open_time: time
    close_time: time
    break_start: time | None = None
    break_end: time | None = None

    def __post_init__(self) -> None:
        if not (0 <= self.day_of_week <= 6):
            raise InvariantViolationException(
                f"day_of_week must be between 0 (Monday) and 6 (Sunday), received: {self.day_of_week}."
            )
        if self.open_time >= self.close_time:
            raise InvariantViolationException(
                f"open_time ({self.open_time}) must precede close_time ({self.close_time})."
            )
        if (self.break_start is None) != (self.break_end is None):
            raise InvariantViolationException(
                "Both break_start and break_end must be provided if either is set."
            )
        if self.break_start and self.break_end:
            if not (self.open_time <= self.break_start < self.break_end <= self.close_time):
                raise InvariantViolationException(
                    f"Break interval ({self.break_start}-{self.break_end}) must be strictly within operating hours ({self.open_time}-{self.close_time})."
                )

    def is_operational_at(self, target_time: time) -> bool:
        """Evaluates whether the counter is currently open and not on break."""
        if not (self.open_time <= target_time <= self.close_time):
            return False
        if self.break_start and self.break_end:
            if self.break_start <= target_time < self.break_end:
                return False
        return True


@dataclass(frozen=True)
class ScheduleException:
    """Specific calendar date override (holiday, exam session, or special hours)."""

    exception_date: date
    is_closed: bool = False
    override_open: time | None = None
    override_close: time | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.reason or not self.reason.strip():
            raise InvariantViolationException("ScheduleException reason cannot be empty.")
        if not self.is_closed:
            if self.override_open is None or self.override_close is None:
                raise InvariantViolationException(
                    "Non-closed ScheduleException must specify override_open and override_close."
                )
            if self.override_open >= self.override_close:
                raise InvariantViolationException(
                    f"override_open ({self.override_open}) must precede override_close ({self.override_close})."
                )

    def is_operational_at(self, target_time: time) -> bool:
        """Evaluates whether the counter is open under this date exception."""
        if self.is_closed:
            return False
        assert self.override_open and self.override_close
        return self.override_open <= target_time <= self.override_close


@dataclass(frozen=True)
class Service:
    """Service catalog capability provided by an organization."""

    code: ServiceCode
    organization_code: OrganizationCode
    title: str
    description: str = ""
    is_active: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.code, ServiceCode):
            object.__setattr__(self, "code", ServiceCode(self.code))
        if not isinstance(self.organization_code, OrganizationCode):
            object.__setattr__(self, "organization_code", OrganizationCode(self.organization_code))
        if not self.title or not self.title.strip():
            raise InvariantViolationException("Service title cannot be empty.")


@dataclass(frozen=True)
class ServiceVersion:
    """Immutable release of requirements and dependencies for a service."""

    service_code: ServiceCode
    version_tag: str
    effective_from: datetime
    effective_until: datetime | None = None
    requirements: tuple[RequirementSpecification, ...] = ()
    dependencies: tuple[DependencyEdge, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.service_code, ServiceCode):
            object.__setattr__(self, "service_code", ServiceCode(self.service_code))
        if not self.version_tag or not self.version_tag.strip():
            raise InvariantViolationException("version_tag cannot be empty.")
        ensure_timezone_aware(self.effective_from, "effective_from")
        validate_temporal_range(self.effective_from, self.effective_until, "service version validity")

        # Convert sequences to immutable tuples
        if not isinstance(self.requirements, tuple):
            object.__setattr__(self, "requirements", tuple(self.requirements))
        if not isinstance(self.dependencies, tuple):
            object.__setattr__(self, "dependencies", tuple(self.dependencies))

    def get_requirement(self, code: RequirementCode) -> RequirementSpecification | None:
        """Finds a requirement specification by its code."""
        for req in self.requirements:
            if req.code == code:
                return req
        return None
