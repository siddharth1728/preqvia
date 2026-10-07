"""Tests for Evaluation, EvaluationNode, and ActionableRemediation models."""

from datetime import datetime, timezone
import pytest

from backend.domain.common.state import ReadinessState
from backend.domain.common.types import (
    LocationCode,
    RequirementCode,
    ServiceCode,
    SubjectId,
)
from backend.domain.errors.exceptions import (
    InvariantViolationException,
    MissingTimezoneException,
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


class TestEvaluationModel:
    """Verifies construction, immutability, and invariants of evaluation results."""

    def test_evaluation_node_construction(self) -> None:
        """EvaluationNode with satisfied or blocked states passes validation."""
        satisfied_node = EvaluationNode(
            requirement_code=RequirementCode("REQ_BONAFIDE_CERT"),
            status=NodeVerdictStatus.SATISFIED,
            matched_evidence_id="EV_001",
        )
        assert satisfied_node.status == NodeVerdictStatus.SATISFIED
        assert satisfied_node.matched_evidence_id == "EV_001"

        blocked_dep_node = EvaluationNode(
            requirement_code=RequirementCode("REQ_PRINCIPAL_SIGN"),
            status=NodeVerdictStatus.BLOCKED_BY_DEPENDENCY,
            blocker_reason="Prerequisite HOD signature is missing",
            blocked_by_codes=(RequirementCode("REQ_HOD_SIGN"),),
        )
        assert blocked_dep_node.status == NodeVerdictStatus.BLOCKED_BY_DEPENDENCY
        assert blocked_dep_node.blocked_by_codes == (RequirementCode("REQ_HOD_SIGN"),)

    def test_blocked_by_dependency_without_codes_raises(self) -> None:
        """BLOCKED_BY_DEPENDENCY status without blocked_by_codes raises InvariantViolationException."""
        with pytest.raises(InvariantViolationException) as exc_info:
            EvaluationNode(
                requirement_code=RequirementCode("REQ_PRINCIPAL_SIGN"),
                status=NodeVerdictStatus.BLOCKED_BY_DEPENDENCY,
                blocked_by_codes=(),  # Missing!
            )
        assert "must specify at least one blocked_by code" in str(exc_info.value)

    def test_actionable_remediation_construction(self) -> None:
        """Remediation steps require positive step_order and valid instructions."""
        rem = ActionableRemediation(
            step_order=1,
            requirement_code=RequirementCode("REQ_HOD_SIGN"),
            action_type=RemediationActionType.OBTAIN_SIGNATURE,
            title="Obtain HOD Endorsement",
            instruction="Visit CS Dept Room 201 to obtain signature.",
            target_location=LocationCode("ROOM_201"),
        )
        assert rem.step_order == 1
        assert rem.action_type == RemediationActionType.OBTAIN_SIGNATURE

        # step_order < 1 raises InvariantViolationException
        with pytest.raises(InvariantViolationException):
            ActionableRemediation(
                step_order=0,
                requirement_code=RequirementCode("REQ_HOD_SIGN"),
                action_type=RemediationActionType.OBTAIN_SIGNATURE,
                title="Title",
                instruction="Instruction",
            )

    def test_evaluation_construction(self) -> None:
        """Full Evaluation determination record is created and immutable."""
        target_time = datetime(2026, 10, 8, 11, 0, tzinfo=timezone.utc)
        eval_time = datetime(2026, 10, 7, 20, 0, tzinfo=timezone.utc)

        node = EvaluationNode(
            requirement_code=RequirementCode("REQ_DOC"),
            status=NodeVerdictStatus.SATISFIED,
        )
        rem = ActionableRemediation(
            step_order=1,
            requirement_code=RequirementCode("REQ_DOC"),
            action_type=RemediationActionType.OBTAIN_DOCUMENT,
            title="Title",
            instruction="Instruction",
        )

        evaluation = Evaluation(
            evaluation_id="EVAL_2026_001",
            subject_id=SubjectId("STU_1001"),
            service_code=ServiceCode("SCHOLARSHIP_SUBMISSION"),
            location_code=LocationCode("COUNTER_03"),
            target_time=target_time,
            overall_state=ReadinessState.READY,
            summary_reason="All prerequisites and operating hours satisfied.",
            nodes=(node,),
            remediations=(rem,),
            evaluated_at=eval_time,
        )

        assert evaluation.is_ready is True
        assert evaluation.is_blocked is False
        assert evaluation.is_unknown is False
        assert len(evaluation.nodes) == 1
        assert len(evaluation.remediations) == 1

    def test_evaluation_naive_datetime_raises(self) -> None:
        """Naive target_time raises MissingTimezoneException."""
        with pytest.raises(MissingTimezoneException):
            Evaluation(
                evaluation_id="EVAL_002",
                subject_id=SubjectId("STU_1001"),
                service_code=ServiceCode("SCHOLARSHIP_SUBMISSION"),
                location_code=LocationCode("COUNTER_03"),
                target_time=datetime(2026, 10, 8, 11, 0),  # Naive!
                overall_state=ReadinessState.READY,
                summary_reason="Summary",
            )
