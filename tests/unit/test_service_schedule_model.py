"""Tests for Service, ServiceVersion, OperatingSchedule, and ScheduleException."""

from datetime import date, datetime, time, timezone
import pytest

from backend.domain.common.types import (
    OrganizationCode,
    RequirementCode,
    ServiceCode,
)
from backend.domain.dependency.models import DependencyEdge
from backend.domain.errors.exceptions import (
    InvalidTemporalRangeException,
    InvariantViolationException,
)
from backend.domain.requirement.models import (
    RequirementCategory,
    RequirementSpecification,
)
from backend.domain.service.models import (
    OperatingSchedule,
    ScheduleException,
    Service,
    ServiceVersion,
)


class TestServiceAndScheduleModels:
    """Verifies service definitions, operating hours, and holiday schedules."""

    def test_operating_schedule_operational_evaluation(self) -> None:
        """OperatingSchedule accurately evaluates open hours and lunch breaks."""
        sched = OperatingSchedule(
            day_of_week=0,  # Monday
            open_time=time(9, 30),
            close_time=time(16, 30),
            break_start=time(13, 0),
            break_end=time(14, 0),
        )

        assert sched.is_operational_at(time(10, 0)) is True  # Open morning
        assert sched.is_operational_at(time(15, 0)) is True  # Open afternoon
        assert sched.is_operational_at(time(8, 0)) is False  # Before open
        assert sched.is_operational_at(time(17, 0)) is False  # After close
        assert sched.is_operational_at(time(13, 30)) is False  # During lunch break

    def test_invalid_operating_schedule_invariants(self) -> None:
        """Invalid times or weekdays raise InvariantViolationException."""
        # Invalid weekday
        with pytest.raises(InvariantViolationException):
            OperatingSchedule(day_of_week=7, open_time=time(9, 0), close_time=time(17, 0))

        # Close before open
        with pytest.raises(InvariantViolationException):
            OperatingSchedule(day_of_week=1, open_time=time(17, 0), close_time=time(9, 0))

        # Break outside operating hours
        with pytest.raises(InvariantViolationException):
            OperatingSchedule(
                day_of_week=1,
                open_time=time(9, 0),
                close_time=time(17, 0),
                break_start=time(18, 0),
                break_end=time(19, 0),
            )

    def test_schedule_exception_closure_vs_override(self) -> None:
        """ScheduleException handles full closure or custom operating hours."""
        closed_holiday = ScheduleException(
            exception_date=date(2026, 10, 2),
            is_closed=True,
            reason="Gandhi Jayanti Public Holiday",
        )
        assert closed_holiday.is_operational_at(time(11, 0)) is False

        special_half_day = ScheduleException(
            exception_date=date(2026, 12, 24),
            is_closed=False,
            override_open=time(9, 0),
            override_close=time(13, 0),
            reason="Christmas Eve Half Day",
        )
        assert special_half_day.is_operational_at(time(10, 0)) is True
        assert special_half_day.is_operational_at(time(14, 0)) is False

    def test_service_and_version_construction(self) -> None:
        """Service and immutable ServiceVersion are created properly."""
        service = Service(
            code=ServiceCode("SCHOLARSHIP_SUBMISSION"),
            organization_code=OrganizationCode("COLLEGE_NIE"),
            title="Merit Scholarship Application",
        )
        assert service.code == "SCHOLARSHIP_SUBMISSION"
        assert service.is_active is True

        req = RequirementSpecification(
            code=RequirementCode("REQ_HOD_APPROVAL"),
            category=RequirementCategory.APPROVAL,
            title="HOD Endorsement",
        )
        dep = DependencyEdge(
            upstream_code=RequirementCode("REQ_HOD_APPROVAL"),
            downstream_code=RequirementCode("REQ_FINAL_SUBMIT"),
        )

        version = ServiceVersion(
            service_code=ServiceCode("SCHOLARSHIP_SUBMISSION"),
            version_tag="2026.1",
            effective_from=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
            requirements=(req,),
            dependencies=(dep,),
        )

        assert version.version_tag == "2026.1"
        assert len(version.requirements) == 1
        assert version.get_requirement(RequirementCode("REQ_HOD_APPROVAL")) == req
        assert version.get_requirement(RequirementCode("REQ_NON_EXISTENT")) is None
