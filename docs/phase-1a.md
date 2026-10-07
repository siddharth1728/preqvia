# Phase 1A: Pure Domain Foundation Report

**Phase**: 1A (Pure Domain Foundation)  
**System**: PREQVIA (Real-World Task Completion Feasibility Engine)  
**Status**: COMPLETED & VERIFIED (Quality Gate Passed)  
**Date**: 2026-10-07  

---

## 1. What Was Implemented

In Phase 1A, we created the pure domain layer for PREQVIA with **zero database, network, HTTP, framework, or filesystem dependencies**. The domain layer is implemented in standard Python with complete type hints and is 100% executable and testable in memory.

### 1.1 Package Structure Created

```
backend/domain/
├── __init__.py                 # Public domain facade
├── errors/
│   ├── __init__.py
│   └── exceptions.py           # DomainException hierarchy
├── common/
│   ├── __init__.py
│   ├── state.py                # ReadinessState & Kleene 3-Valued Logic
│   ├── types.py                # Strongly typed value objects (RequirementCode, etc.)
│   └── timestamps.py           # Timezone validation & temporal range helpers
├── requirement/
│   ├── __init__.py
│   └── models.py               # RequirementSpecification, ValidationSpec, RequirementCategory
├── evidence/
│   ├── __init__.py
│   └── models.py               # EvidenceRecord, EvidenceVerificationRecord, Enums
├── dependency/
│   ├── __init__.py
│   └── models.py               # DependencyEdge, DependencyType
├── service/
│   ├── __init__.py
│   └── models.py               # Service, ServiceVersion, OperatingSchedule, ScheduleException
├── task/
│   ├── __init__.py
│   └── models.py               # UserTaskIntent
├── remediation/
│   ├── __init__.py
│   └── models.py               # ActionableRemediation, RemediationActionType
└── evaluation/
    ├── __init__.py
    └── models.py               # Evaluation, EvaluationNode, NodeVerdictStatus
```

A top-level alias `domain/` was also created at repository root so both `from backend.domain import ...` and `from domain import ...` are valid.

---

## 2. Core Domain Concepts Implemented

1. **`ReadinessState` (Tri-State Model)**:
   - Values: `READY` ($\mathbf{T}$), `BLOCKED` ($\mathbf{F}$), `UNKNOWN` ($\mathbf{U}$).
   - Algebraic operations:
     - Kleene conjunction (`conjunction` and `&` operator)
     - Kleene disjunction (`disjunction` and `|` operator)
     - Kleene negation (`negation` and `~` operator)
     - Aggregation helpers: `ReadinessState.all(iterable)` and `ReadinessState.any(iterable)`
   - **Crucial Invariant**: `UNKNOWN` is never silently converted or collapsed into `BLOCKED`.

2. **Value Objects (`backend.domain.common.types`)**:
   - `RequirementCode`: Validated alphanumeric identifier matching `^[A-Z][A-Z0-9_]{1,63}$`.
   - `EvidenceCode`: Validated identifier for evidence types.
   - `ServiceCode`: Validated identifier for service catalog offerings.
   - `OrganizationCode`: Validated identifier for institutional providers.
   - `LocationCode`: Validated identifier for administrative counters/offices.
   - `SubjectId`: Validated non-empty string identifier for students/citizens.

3. **Requirement Model (`backend.domain.requirement.models`)**:
   - `RequirementSpecification`: Immutable catalog template defining what a service requires.
   - `RequirementCategory`: `DOCUMENT`, `APPROVAL`, `ATTESTATION`, `ELIGIBILITY_CRITERION`, `SERVICE_AVAILABILITY`, `PREREQUISITE_TASK`.
   - `ValidationSpec`: Match criteria for evidence (max age in days, required verification status, acceptable evidence types).

4. **Evidence Model (`backend.domain.evidence.models`)**:
   - `EvidenceRecord`: Immutable record capturing what evidence exists for a subject, with `valid_from`, `valid_until`, `revoked_at`, and `revocation_reason`.
   - `is_valid_at(target_time)`: Temporal validity evaluation method.
   - `revoke(revocation_time, reason)`: Immutable revocation producing a new record copy.
   - `EvidenceVerificationRecord`: Decoupled attestation of authenticity (who verified it, when, and how).

5. **Dependency Model (`backend.domain.dependency.models`)**:
   - `DependencyEdge`: Represents a directed edge in the prerequisite DAG.
   - `DependencyType`: `HARD_PREREQUISITE`, `TEMPORAL_SEQUENCE`, `CONDITIONAL`.
   - Self-loop invariant: `upstream_code != downstream_code` strictly enforced.

6. **Service & Operating Calendar Model (`backend.domain.service.models`)**:
   - `Service` & `ServiceVersion`: Immutable release snapshot with version tags and temporal bounds.
   - `OperatingSchedule`: Weekly recurring counter hours (0=Monday to 6=Sunday), break intervals, and `is_operational_at(time)`.
   - `ScheduleException`: Date-specific overrides for holidays and special hours.

7. **Task Model (`backend.domain.task.models`)**:
   - `UserTaskIntent`: Captures the who, what, where, when, and context of a requested task attempt.

8. **Remediation Model (`backend.domain.remediation.models`)**:
   - `ActionableRemediation`: Pure domain structure representing sequential unblocking actions (`step_order`, `requirement_code`, `action_type`, `instruction`, `target_location`).

9. **Evaluation Model (`backend.domain.evaluation.models`)**:
   - `EvaluationNode`: Per-requirement verdict (`SATISFIED`, `UNSATISFIED`, `BLOCKED_BY_DEPENDENCY`, `UNKNOWN`, `NOT_APPLICABLE`) with causal `blocked_by_codes`.
   - `Evaluation`: Immutable snapshot of the overall determination.

---

## 3. Domain Invariants Implemented & Tested

| Invariant | Mechanism | Exception Raised |
| :--- | :--- | :--- |
| **Strict Timezone Awareness** | Naive datetimes rejected on all domain entities | `MissingTimezoneException` |
| **Temporal Range Order** | `valid_until` cannot precede `valid_from` | `InvalidTemporalRangeException` |
| **Revocation Invalidation** | Revoked evidence is permanently invalid regardless of timestamps | Evaluates to `False` in `is_valid_at` |
| **Revocation Reason Mandatory** | Revoking evidence requires non-empty reason | `InvariantViolationException` |
| **Double Revocation Guard** | Revoking already revoked evidence rejected | `RevokedEvidenceException` |
| **Acyclic Self-Loop Guard** | Self-referential dependency edges forbidden | `InvariantViolationException` |
| **Dependency Blocker Linkage** | Node marked `BLOCKED_BY_DEPENDENCY` must specify `blocked_by_codes` | `InvariantViolationException` |
| **Document Validation Spec** | Requirement of category `DOCUMENT` must specify a `ValidationSpec` | `InvariantViolationException` |
| **Non-negative Evidence Age** | `ValidationSpec.max_age_days` must be $\ge 0$ | `InvariantViolationException` |
| **Positive Remediation Steps** | `ActionableRemediation.step_order` must be $\ge 1$ | `InvariantViolationException` |
| **Code Syntax Integrity** | Code strings must match `^[A-Z][A-Z0-9_]{1,63}$` | `InvalidIdentifierException` |
| **Operating Hour Order** | Counter `open_time < close_time` and breaks enclosed | `InvariantViolationException` |

---

## 4. Test Coverage & Verification

The unit test suite runs completely in memory via pytest:
- **Total Test Cases**: 66 tests
- **Passing**: 66 (100%)
- **Failing**: 0
- **Duration**: ~0.35s
- **External Dependencies**: 0 (No database, No Docker, No HTTP server)

### Test Suite Breakdown:
- `tests/unit/test_tristate_logic.py`: 26 tests (all 9 conjunction pairs, all 9 disjunction pairs, negation, aggregates, `UNKNOWN` retention, string parsing).
- `tests/unit/test_value_objects.py`: 10 tests (valid codes, invalid patterns, empty string, length limits, type validation).
- `tests/unit/test_temporal_invariants.py`: 5 tests (timezone awareness, naive rejection, valid/invalid ranges, enclosure).
- `tests/unit/test_evidence_model.py`: 7 tests (construction, valid intervals, expired intervals, revocation, double revocation, verification records).
- `tests/unit/test_requirement_model.py`: 6 tests (validation specs, category requirements, title validation, advisory flags, immutable mappings).
- `tests/unit/test_dependency_model.py`: 3 tests (edge construction, self-loop rejection, type coercion).
- `tests/unit/test_service_schedule_model.py`: 4 tests (operational evaluation, breaks, closures, service versions).
- `tests/unit/test_evaluation_model.py`: 5 tests (evaluation nodes, dependency blocker requirement, remediation step orders, evaluation construction).

---

## 5. Architectural Decisions Made

1. **Immutable Frozen Dataclasses**: All domain models use `@dataclass(frozen=True)` with mapping proxies (`MappingProxyType`) to prevent accidental state mutation during evaluation runs.
2. **Value Objects as Validated String Subclasses**: `RequirementCode`, `EvidenceCode`, and other identifiers inherit from `_ValidatedCode(str)`, giving strong typing and runtime validation while retaining simple serialization.
3. **Decoupled Verification from Evidence**: Verification records (`EvidenceVerificationRecord`) are separate objects referencing an `evidence_id`, allowing multi-party verification and revocation audit trails without mutating the user's uploaded evidence artifact.
4. **Topological Causality on Evaluation Nodes**: Nodes explicitly track `blocked_by_codes` when status is `BLOCKED_BY_DEPENDENCY`, establishing a causal trace from symptoms back to root blockers.

---

## 6. Assumptions & Unresolved Questions

### Assumptions:
- Weekly operating schedules use Python's standard `datetime.weekday()` convention ($0 = \text{Monday}, \dots, 6 = \text{Sunday}$).
- Timestamps in evaluations, evidence records, and verifications must have explicit timezone offsets.
- Service definitions remain immutable per `version_tag`.

### Unresolved Questions for Future Phases:
1. When multiple pieces of evidence exist for the same `evidence_code` (e.g. an older expired certificate and a newer unverified one), which priority strategy should the Phase 1B evidence matcher use? (Recommendation: evaluate the newest non-revoked candidate first).
2. Should `ScheduleException` support recurring annual holidays (e.g., Independence Day every Aug 15) without explicit year specification? (Currently requires explicit `date`).

---

## 7. Recommended Phase 1B Scope

With the domain layer complete, the next logical milestone is **Phase 1B: Deterministic Readiness Engine Algorithm**.

### Scope of Phase 1B:
1. Implement the **Dependency DAG Solver** (Cycle detection via Kahn's algorithm and topological traversal).
2. Implement the **Evidence Matcher & Temporal Verifier** (Matching user evidence against `ValidationSpec` with age and verification checks).
3. Implement the **Operating Hours Availability Evaluator** (Evaluating `OperatingSchedule` and `ScheduleException` against `UserTaskIntent.target_time`).
4. Implement the **Root Cause Isolation & Remediation Generator** (Tracing `BLOCKED_BY_DEPENDENCY` back to leaf `UNSATISFIED` nodes and synthesizing `ActionableRemediation` chains).
5. Implement and pass the **10 Canonical Test Cases** defined in [docs/implementation-plan.md](file:///c:/PREQVIA/docs/implementation-plan.md#4-the-10-canonical-engine-test-scenarios-phase-1-gate).
