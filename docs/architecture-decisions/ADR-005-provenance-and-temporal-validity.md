# ADR-005: Provenance Tracking and Temporal Validity Modeling

**Status**: ACCEPTED  
**Date**: 2026-10-07  
**Deciders**: Lead Software Architect  

---

## Context
When a user is told "You are BLOCKED because you need Document X", their natural reaction is:
> *"Who says so? Where is that written?"*

Furthermore, real-world requirements and evidence expire:
- A bonafide certificate may be valid for only 6 months.
- An institutional circular may be superseded by a new notification.
- An office counter may have special operating hours on a specific day.

Without provenance and temporal validity, the system quickly loses credibility and produces stale, misleading advice.

## Decision
1. **Mandatory Provenance**:
   - Every `RequirementSpecification` must trace back to a `SourceVersion`.
   - `SourceVersion` stores citation references (e.g. "Section 3.2 of Academic Circular 2026"), source URLs, publication dates, and a cryptographic SHA-256 content hash of the official document.
2. **Temporal Validity Windows**:
   - Every `EvidenceRecord` defines `valid_from` and `valid_until`.
   - Evaluations evaluate feasibility against a specific `target_time` (e.g., "Tomorrow at 11:00 AM").
   - Evidence is valid if and only if $\text{valid\_from} \le \text{target\_time} \le \text{valid\_until}$.
3. **Temporal Counter Calendars**:
   - Location availability checks evaluate against the specific calendar day and clock time of `target_time`, cross-checking both weekly recurring hours and date-specific exception overrides.

## Consequences
### Positive
- Fully answerable: "Why does PREQVIA claim this requirement exists?"
- Reliable temporal accuracy (e.g. catches documents expiring tomorrow, detects weekend or holiday counter closures).
- Eliminates ambiguous administrative disputes.

### Negative / Trade-offs
- Timezone handling must be rigorous; all internal evaluation math uses timezone-aware timestamps normalized to UTC or the location's designated timezone.
