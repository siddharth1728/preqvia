"""Tests for DependencyEdge and DependencyType domain models."""

import pytest
from backend.domain.common.types import RequirementCode
from backend.domain.dependency.models import DependencyEdge, DependencyType
from backend.domain.errors.exceptions import InvariantViolationException


class TestDependencyModel:
    """Verifies dependency edges, types, and self-loop detection."""

    def test_valid_dependency_edge_construction(self) -> None:
        """Valid prerequisite edge is constructed properly."""
        edge = DependencyEdge(
            upstream_code=RequirementCode("REQ_HOD_SIGNATURE"),
            downstream_code=RequirementCode("REQ_PRINCIPAL_SIGNATURE"),
            dependency_type=DependencyType.HARD_PREREQUISITE,
        )

        assert edge.upstream_code == "REQ_HOD_SIGNATURE"
        assert edge.downstream_code == "REQ_PRINCIPAL_SIGNATURE"
        assert edge.dependency_type == DependencyType.HARD_PREREQUISITE

    def test_self_loop_dependency_raises_invariant_violation(self) -> None:
        """Self-referential dependencies are strictly forbidden."""
        with pytest.raises(InvariantViolationException) as exc_info:
            DependencyEdge(
                upstream_code=RequirementCode("REQ_SELF_LOOP"),
                downstream_code=RequirementCode("REQ_SELF_LOOP"),
            )
        assert "Self-referential dependency is forbidden" in str(exc_info.value)

    def test_string_coercion_to_requirement_code(self) -> None:
        """Raw strings matching code pattern are automatically coerced to RequirementCode."""
        edge = DependencyEdge(
            upstream_code="REQ_STEP_ONE",  # type: ignore
            downstream_code="REQ_STEP_TWO",  # type: ignore
        )
        assert isinstance(edge.upstream_code, RequirementCode)
        assert isinstance(edge.downstream_code, RequirementCode)
