# ADR-004: Directed Acyclic Graph (DAG) for Prerequisite Dependencies

**Status**: ACCEPTED  
**Date**: 2026-10-07  
**Deciders**: Lead Software Architect  

---

## Context
Real-world workflows are rarely flat checklists. Instead, they exhibit complex prerequisite chains:
- You cannot obtain a Principal's Signature without prior Head of Department (HOD) Endorsement.
- You cannot obtain HOD Endorsement without a completed Application Form and verified Fee Clearance.
- You cannot submit at the counter without the Principal's Signature.

If a student's Fee Clearance is missing, showing them:
> "You are blocked because Principal Signature is missing, HOD Signature is missing, and Fee Clearance is missing."

overwhelms them and hides the true culprit. The student cannot directly fix the Principal's signature. The actual root cause is the Fee Clearance.

## Decision
1. Model all service prerequisites as a formal **Directed Acyclic Graph (DAG)**:
   - Vertices: `RequirementSpecification` codes.
   - Directed Edges: $(u, v)$ indicating $u$ must be satisfied before $v$ can proceed.
2. Enforce cycle detection at catalog ingestion time using **Kahn's Algorithm**. Any cycle causes an immediate validation failure (`CyclicDependencyError`).
3. Evaluate the DAG in **topological order**.
4. Distinguish between:
   - **Root Blockers**: Nodes whose evidence is missing/invalid while their own prerequisites are satisfied.
   - **Secondary Symptoms**: Nodes blocked purely because upstream prerequisites are blocked.
5. Synthesize explicit **Dependency Chains** and order **Next Actions** topologically starting from root blockers.

## Consequences
### Positive
- Deep, accurate diagnostic explainability.
- Actionable guidance: Tells the user the exact sequential path to unlock the task.
- Prevents wasted trips to downstream authorities (e.g. going to the Principal when HOD has not signed).

### Negative / Trade-offs
- Graph traversal adds algorithmic structure to the engine (mitigated by using efficient in-memory adjacency lists and topological sorting).
