"""Strongly typed Tri-State Readiness Model based on Kleene 3-Valued Logic."""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from backend.domain.errors.exceptions import InvariantViolationException


class ReadinessState(str, Enum):
    """Tri-state feasibility evaluation outcome.
    
    Kleene 3-Valued Logic algebra:
    - READY (T): All conditions definitively proven to be satisfied.
    - BLOCKED (F): One or more conditions definitively proven to be unsatisfied.
    - UNKNOWN (U): Information is missing, incomplete, or unverified.
    
    CRITICAL: UNKNOWN must NEVER be silently collapsed into BLOCKED.
    """

    READY = "READY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"

    @property
    def is_ready(self) -> bool:
        """Returns True if state is READY."""
        return self == ReadinessState.READY

    @property
    def is_blocked(self) -> bool:
        """Returns True if state is BLOCKED."""
        return self == ReadinessState.BLOCKED

    @property
    def is_unknown(self) -> bool:
        """Returns True if state is UNKNOWN."""
        return self == ReadinessState.UNKNOWN

    def conjunction(self, other: ReadinessState) -> ReadinessState:
        """Kleene logical conjunction (AND).
        
        Truth Table:
        READY AND READY = READY
        READY AND UNKNOWN = UNKNOWN
        READY AND BLOCKED = BLOCKED
        UNKNOWN AND READY = UNKNOWN
        UNKNOWN AND UNKNOWN = UNKNOWN
        UNKNOWN AND BLOCKED = BLOCKED
        BLOCKED AND READY = BLOCKED
        BLOCKED AND UNKNOWN = BLOCKED
        BLOCKED AND BLOCKED = BLOCKED
        """
        if not isinstance(other, ReadinessState):
            raise InvariantViolationException(
                f"Cannot evaluate conjunction with non-ReadinessState: {type(other).__name__}"
            )

        if self == ReadinessState.BLOCKED or other == ReadinessState.BLOCKED:
            return ReadinessState.BLOCKED
        if self == ReadinessState.UNKNOWN or other == ReadinessState.UNKNOWN:
            return ReadinessState.UNKNOWN
        return ReadinessState.READY

    def disjunction(self, other: ReadinessState) -> ReadinessState:
        """Kleene logical disjunction (OR).
        
        Truth Table:
        READY OR READY = READY
        READY OR UNKNOWN = READY
        READY OR BLOCKED = READY
        UNKNOWN OR READY = READY
        UNKNOWN OR UNKNOWN = UNKNOWN
        UNKNOWN OR BLOCKED = UNKNOWN
        BLOCKED OR READY = READY
        BLOCKED OR UNKNOWN = UNKNOWN
        BLOCKED OR BLOCKED = BLOCKED
        """
        if not isinstance(other, ReadinessState):
            raise InvariantViolationException(
                f"Cannot evaluate disjunction with non-ReadinessState: {type(other).__name__}"
            )

        if self == ReadinessState.READY or other == ReadinessState.READY:
            return ReadinessState.READY
        if self == ReadinessState.UNKNOWN or other == ReadinessState.UNKNOWN:
            return ReadinessState.UNKNOWN
        return ReadinessState.BLOCKED

    def negation(self) -> ReadinessState:
        """Kleene logical negation (NOT).
        
        Truth Table:
        NOT READY = BLOCKED
        NOT BLOCKED = READY
        NOT UNKNOWN = UNKNOWN
        """
        if self == ReadinessState.READY:
            return ReadinessState.BLOCKED
        if self == ReadinessState.BLOCKED:
            return ReadinessState.READY
        return ReadinessState.UNKNOWN

    def __and__(self, other: ReadinessState) -> ReadinessState:
        """Syntactic operator for conjunction (&)."""
        return self.conjunction(other)

    def __or__(self, other: ReadinessState) -> ReadinessState:
        """Syntactic operator for disjunction (|)."""
        return self.disjunction(other)

    def __invert__(self) -> ReadinessState:
        """Syntactic operator for negation (~)."""
        return self.negation()

    @classmethod
    def all(cls, states: Iterable[ReadinessState]) -> ReadinessState:
        """Folds conjunction over an iterable of states.
        
        The identity element for conjunction is READY (an empty set of requirements is READY).
        """
        result = cls.READY
        for state in states:
            result = result.conjunction(state)
            if result == cls.BLOCKED:
                # Short-circuit on BLOCKED
                break
        return result

    @classmethod
    def any(cls, states: Iterable[ReadinessState]) -> ReadinessState:
        """Folds disjunction over an iterable of states.
        
        The identity element for disjunction is BLOCKED (an empty set of alternatives is BLOCKED).
        """
        result = cls.BLOCKED
        for state in states:
            result = result.disjunction(state)
            if result == cls.READY:
                # Short-circuit on READY
                break
        return result

    @classmethod
    def from_str(cls, value: str) -> ReadinessState:
        """Parses a string into a ReadinessState, raising a domain exception on error."""
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError:
            raise InvariantViolationException(
                f"Invalid readiness state '{value}'. Must be one of {[s.value for s in cls]}."
            )
