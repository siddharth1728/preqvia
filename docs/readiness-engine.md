# Readiness Decision Engine: PREQVIA

**System**: PREQVIA  
**Document**: Readiness Decision Engine Specification & Algorithm  
**Status**: APPROVED / ARCHITECTURAL BASELINE  
**Version**: 1.0.0  
**Date**: 2026-10-07  

---

## 1. Engine Mission & Mathematical Foundations

The PREQVIA Readiness Engine computes the feasibility of task completion given:
$$C = \langle \text{Subject } U, \text{Service } S, \text{Location } L, \text{Target Time } T \rangle$$

The output is an immutable evaluation verdict:
$$\Phi(C) \in \{\mathbf{READY}, \mathbf{BLOCKED}, \mathbf{UNKNOWN}\}$$

Along with an explicit causal graph explaining the status:
$$\text{Explanation} = \langle \text{Summary}, \text{RootBlockers}, \text{BlockedChains}, \text{UnknownFactors}, \text{NextActions} \rangle$$

---

## 2. Tri-State Logic: Kleene 3-Valued Logic Algebra

In classical boolean logic, an unverified condition is often coercively cast to `FALSE`. In real life, that creates severe operational bugs (e.g. telling a student they cannot submit a scholarship when in fact their record simply hasn't been fetched yet).

PREQVIA strictly adopts **Kleene 3-Valued Logic ($K_3$)**:
- **$\mathbf{T}$ (SATISFIED / READY)**: Proven to be true.
- **$\mathbf{F}$ (UNSATISFIED / BLOCKED)**: Proven to be false.
- **$\mathbf{U}$ (UNKNOWN)**: Insufficient or unverified evidence.

### 2.1 Truth Tables for Logic Gates

#### Logical Conjunction (AND - all requirements must be met)
| $A$ | $B$ | $A \land B$ |
| :---: | :---: | :---: |
| $\mathbf{T}$ | $\mathbf{T}$ | $\mathbf{T}$ |
| $\mathbf{T}$ | $\mathbf{U}$ | $\mathbf{U}$ |
| $\mathbf{T}$ | $\mathbf{F}$ | $\mathbf{F}$ |
| $\mathbf{U}$ | $\mathbf{U}$ | $\mathbf{U}$ |
| $\mathbf{U}$ | $\mathbf{F}$ | $\mathbf{F}$ |
| $\mathbf{F}$ | $\mathbf{F}$ | $\mathbf{F}$ |

> **Key Invariant**: If even ONE condition is proven $\mathbf{F}$, the conjunction is $\mathbf{F}$ (`BLOCKED`), regardless of whether other elements are $\mathbf{U}$. But if no conditions are $\mathbf{F}$ and at least one is $\mathbf{U}$, the result MUST BE $\mathbf{U}$ (`UNKNOWN`), NEVER $\mathbf{T}$ (`READY`).

#### Logical Disjunction (OR - alternative ways to satisfy requirement)
| $A$ | $B$ | $A \lor B$ |
| :---: | :---: | :---: |
| $\mathbf{T}$ | $\mathbf{T}$ | $\mathbf{T}$ |
| $\mathbf{T}$ | $\mathbf{U}$ | $\mathbf{T}$ |
| $\mathbf{T}$ | $\mathbf{F}$ | $\mathbf{T}$ |
| $\mathbf{U}$ | $\mathbf{U}$ | $\mathbf{U}$ |
| $\mathbf{U}$ | $\mathbf{F}$ | $\mathbf{U}$ |
| $\mathbf{F}$ | $\mathbf{F}$ | $\mathbf{F}$ |

---

## 3. The 8-Phase Evaluation Pipeline

The evaluation pipeline is an executed deterministic sequence of 8 distinct phases:

```
[Phase 1: Context Resolution]
       │
       ▼
[Phase 2: Temporal & Location Availability Verification]
       │
       ▼
[Phase 3: Applicability & Eligibility Rule Filtering]
       │
       ▼
[Phase 4: Dependency Graph Construction & Validation (DAG)]
       │
       ▼
[Phase 5: Evidence Matching & Temporal Verification]
       │
       ▼
[Phase 6: Topological Traversal & State Propagation]
       │
       ▼
[Phase 7: Root Cause Isolation & Blocker Tree Extraction]
       │
       ▼
[Phase 8: Actionable Next-Step Remediation Synthesis]
```

---

## 4. Detailed Algorithmic Steps

### Phase 1: Context Resolution
Verify that the `User`, `Service` (and active `ServiceVersion`), and `Location` exist and are active. Parse `target_time` with timezone awareness.

### Phase 2: Temporal & Location Availability Verification
Evaluate whether the service desk or portal at `Location` is operational at `target_time`.

```python
def evaluate_temporal_availability(location, target_time) -> NodeVerdict:
    day_of_week = target_time.weekday() # 0 = Monday, 6 = Sunday
    target_date = target_time.date()
    target_clock = target_time.time()
    
    # 1. Check specific holiday/exception overrides
    exception = location.get_exception_for_date(target_date)
    if exception:
        if exception.is_closed:
            return NodeVerdict(
                status=BLOCKED, 
                reason=f"Location {location.name} is closed on {target_date} ({exception.reason})"
            )
        if not (exception.override_start <= target_clock <= exception.override_end):
            return NodeVerdict(
                status=BLOCKED,
                reason=f"Target time {target_clock} outside special operating hours {exception.override_start}-{exception.override_end}"
            )
            
    # 2. Check regular weekly operating schedule
    schedule = location.get_schedule_for_day(day_of_week)
    if not schedule:
        return NodeVerdict(
            status=BLOCKED,
            reason=f"Service location is closed on {target_time.strftime('%A')}s"
        )
        
    if not (schedule.start_time <= target_clock <= schedule.end_time):
        return NodeVerdict(
            status=BLOCKED,
            reason=f"Counter opens at {schedule.start_time} and closes at {schedule.end_time}."
        )
        
    if schedule.break_start and (schedule.break_start <= target_clock <= schedule.break_end):
        return NodeVerdict(
            status=BLOCKED,
            reason=f"Target time falls during counter break ({schedule.break_start}-{schedule.break_end})"
        )
        
    return NodeVerdict(status=SATISFIED, reason="Location and service counter operational.")
```

### Phase 3: Applicability & Eligibility Rule Filtering
Filter the catalog requirements. Some requirements only apply if specific conditions are met (e.g., student quota or income threshold).

```python
def filter_applicable_requirements(service_version, subject_profile) -> list[RequirementSpec]:
    applicable = []
    for req in service_version.requirements:
        if req.applicability_rule is None:
            applicable.append(req)
        else:
            is_applicable = json_logic_evaluate(req.applicability_rule, subject_profile)
            if is_applicable is True:
                applicable.append(req)
    return applicable
```

### Phase 4: Dependency Graph Construction & Validation (DAG)
Build the Directed Acyclic Graph $G = (V, E)$ where vertices $V$ are the applicable requirement codes and edges $E$ are prerequisite dependencies:
$$E = \{ (u, v) \mid u \text{ must be satisfied BEFORE } v \text{ can be satisfied} \}$$

**Cycle Detection**: Run Kahn's Algorithm. If any cycle is detected, fail immediately with an architectural error (`CyclicDependencyError`).

### Phase 5: Evidence Matching & Temporal Verification
For each requirement $R \in V$:
1. Search user evidence pool for items matching $R$'s `evidence_code`.
2. For each candidate evidence:
   - Check revocation: `revoked_at` must be null.
   - Check temporal validity: `valid_from <= target_time <= (valid_until or inf)`.
   - Check verification record: Has an authorized officer/system verified this?
     - If verified: Candidate is Valid.
     - If pending verification: Flag as `UNVERIFIED_EVIDENCE`.
     - If rejected: Candidate is Invalid.
3. Node Verdict assignment:
   - If valid verified evidence found: `status = SATISFIED`.
   - If evidence exists but verification is pending: `status = UNKNOWN` (Reason: "Evidence submitted but awaiting verification").
   - If valid evidence not found: `status = UNSATISFIED`.

### Phase 6: Topological Traversal & State Propagation
Traverse the DAG in **topological order** (from upstream prerequisite leaves up to the root service submission node).

For each node $N$:
1. Check all direct upstream dependencies $P \in \text{Parents}(N)$.
2. If ANY $P$ is `UNSATISFIED` or `BLOCKED_BY_DEPENDENCY`:
   - $N$ cannot proceed.
   - $N.\text{status} = \mathbf{BLOCKED\_BY\_DEPENDENCY}$.
   - $N.\text{blocked\_by} = \{ P \} \cup \text{RootBlockers}(P)$.
3. Else if ANY $P$ is $\mathbf{UNKNOWN}$ and no parent is blocked:
   - $N.\text{status} = \mathbf{UNKNOWN}$.
   - $N.\text{reason} = \text{"Cannot evaluate because prerequisite } P \text{ is unknown."}$
4. Else (all parents are $\mathbf{SATISFIED}$):
   - $N$'s direct evidence status from Phase 5 is retained.

```python
def propagate_graph_state(dag, node_verdicts) -> dict[str, NodeVerdict]:
    for req_code in dag.topological_sort():
        upstream_nodes = dag.get_prerequisites(req_code)
        
        # Check if upstream is blocked
        blocked_prereqs = [p for p in upstream_nodes if node_verdicts[p].status in (UNSATISFIED, BLOCKED_BY_DEPENDENCY)]
        if blocked_prereqs:
            node_verdicts[req_code].status = BLOCKED_BY_DEPENDENCY
            node_verdicts[req_code].blocked_by = blocked_prereqs
            continue
            
        # Check if upstream is unknown
        unknown_prereqs = [p for p in upstream_nodes if node_verdicts[p].status == UNKNOWN]
        if unknown_prereqs:
            node_verdicts[req_code].status = UNKNOWN
            node_verdicts[req_code].reason = f"Prerequisite {unknown_prereqs[0]} has unknown verification status."
            continue
            
        # If all prerequisites are satisfied, keep local node_verdict status
    return node_verdicts
```

### Phase 7: Root Cause Isolation & Blocker Tree Extraction
To prevent overwhelming the user with duplicate symptoms, the engine distinguishes **Root Blockers** from **Secondary Blocked Symptoms**.

- **Root Blocker**: A requirement that is directly `UNSATISFIED` (evidence missing, expired, or rejected) while all of its own prerequisites (if any) are satisfied.
- **Secondary Symptom**: A requirement that is `BLOCKED_BY_DEPENDENCY` purely because an upstream requirement failed.

The explainer isolates the exact dependency chain from Root Blocker to the target task:
$$\text{Chain: } \text{Application Form (UNSATISFIED)} \rightarrow \text{Dept Approval} \rightarrow \text{Principal Signature} \rightarrow \text{Submission}$$

### Phase 8: Actionable Next-Step Remediation Synthesis
Order remediations by topological depth:
1. Fix upstream root blockers first.
2. If root blockers require physical presence, synthesize counter instructions.
3. If information is unknown, instruct user on verification upload.

---

## 5. Comprehensive Test Scenario Trace

### Scenario: College Scholarship Submission
- Target Task: Submit Merit Scholarship at Administrative Counter 3 tomorrow at 11:00 AM.
- Prerequisites:
  - `REQ_APPLICATION`: Application form filled.
  - `REQ_BONAFIDE`: Bonafide Certificate (valid < 6 months).
  - `REQ_HOD_SIGN`: HOD Signature (depends on `REQ_APPLICATION` + `REQ_BONAFIDE`).
  - `REQ_PRINCIPAL_SIGN`: Principal Signature (depends on `REQ_HOD_SIGN`).
  - `REQ_SUBMISSION`: Final Counter Handover (depends on `REQ_PRINCIPAL_SIGN` + Location Open).

**Test Case: Missing Bonafide Certificate**
- Phase 2: Location is open tomorrow at 11:00 AM $\rightarrow \mathbf{SATISFIED}$.
- Phase 5:
  - `REQ_APPLICATION`: User has valid form $\rightarrow \mathbf{SATISFIED}$.
  - `REQ_BONAFIDE`: No certificate found in vault $\rightarrow \mathbf{UNSATISFIED}$.
- Phase 6 Propagation:
  - `REQ_HOD_SIGN`: Blocked by `REQ_BONAFIDE` $\rightarrow \mathbf{BLOCKED\_BY\_DEPENDENCY}$.
  - `REQ_PRINCIPAL_SIGN`: Blocked by `REQ_HOD_SIGN` $\rightarrow \mathbf{BLOCKED\_BY\_DEPENDENCY}$.
  - `REQ_SUBMISSION`: Blocked by `REQ_PRINCIPAL_SIGN` $\rightarrow \mathbf{BLOCKED\_BY\_DEPENDENCY}$.
- Decision:
  - `overall_status`: $\mathbf{BLOCKED}$
  - `root_blockers`: `["REQ_BONAFIDE"]`
  - `dependency_chain`: `["REQ_BONAFIDE" -> "REQ_HOD_SIGN" -> "REQ_PRINCIPAL_SIGN" -> "REQ_SUBMISSION"]`
  - `next_action`: `"Obtain and upload Bonafide Certificate before seeking HOD signature."`
