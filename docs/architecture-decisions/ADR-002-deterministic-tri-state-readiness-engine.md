# ADR-002: Deterministic Tri-State Logic (Kleene 3-Valued Algebra)

**Status**: ACCEPTED  
**Date**: 2026-10-07  
**Deciders**: Lead Software Architect  

---

## Context
Standard business software relies on two-valued Boolean logic (`True` vs `False`). Under this paradigm, unverified or missing information is typically coerced to `False` (`BLOCKED`).

In real-world administrative tasks, coercing missing or unverified data to `BLOCKED` produces dangerous false negatives:
- A student who uploaded a valid certificate that has not yet been audited by an admin clerk is told: "You are blocked / not eligible", causing panic.
- A user whose income threshold was never entered into their profile is told: "You are not eligible", when the real status is "We need your income to decide".

Conversely, treating unknown as `READY` creates catastrophic false positives (travelling to a counter only to be turned away).

## Decision
PREQVIA will strictly enforce **Kleene 3-Valued Logic ($K_3$)**:
1. All evaluation nodes and composite outcomes resolve to one of:
   - `READY` ($\mathbf{T}$)
   - `BLOCKED` ($\mathbf{F}$)
   - `UNKNOWN` ($\mathbf{U}$)
2. Under Kleene algebraic conjunction:
   - $\mathbf{T} \land \mathbf{T} = \mathbf{T}$ (`READY`)
   - $\mathbf{T} \land \mathbf{U} = \mathbf{U}$ (`UNKNOWN`)
   - $\mathbf{U} \land \mathbf{U} = \mathbf{U}$ (`UNKNOWN`)
   - $\mathbf{F} \land \text{Anything} = \mathbf{F}$ (`BLOCKED`)
3. `UNKNOWN` is never collapsed into `BLOCKED`.
4. The system produces explicit `UnknownFactor` records explaining why the state is unknown and how the user or admin can resolve the uncertainty.

## Consequences
### Positive
- Truthful, transparent outcomes for users.
- Clear separation between definitive failure and incomplete information.
- Prevents wasted travel while preserving trust.

### Negative / Trade-offs
- UI and client applications must support tri-state presentation logic rather than a simple binary pass/fail badge.
