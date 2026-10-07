# ADR-003: Strict Separation of Requirement Specifications and Evidence

**Status**: ACCEPTED  
**Date**: 2026-10-07  
**Deciders**: Lead Software Architect  

---

## Context
A common anti-pattern in workflow engines is conflating *what a service requires* with *what a user has submitted*. For example, adding fields directly on a "DocumentRequirement" table like `uploaded_file_path`, `is_uploaded`, or `verified_by`.

This conflation fails in real-world environments because:
1. One piece of evidence (e.g. a Government ID or Bonafide Certificate) can satisfy requirements across multiple independent services.
2. Requirements are defined by institutions (catalog authors), whereas evidence is submitted by users and verified by third parties.
3. Evidence has its own lifecycle (issuance date, expiry date, verification events, revocation).

## Decision
PREQVIA strictly decouples:
- **`RequirementSpecification`**: Catalog-level template defining *what is demanded* (e.g. category `DOCUMENT`, type `INCOME_CERTIFICATE`, maximum age 180 days, required verification level).
- **`EvidenceRecord`**: User-level assertion defining *what exists* (document URI, raw metadata payload, issue date, expiration date, revocation state).
- **`EvidenceVerificationRecord`**: Attestation of authenticity (who verified it, how, when).

A deterministic **Evidence Matcher** within the engine evaluates whether an active `EvidenceRecord` fulfills a `RequirementSpecification`.

## Consequences
### Positive
- Evidence is reusable across multiple tasks and services without duplicate uploads.
- Clear separation of concerns between catalog management and user data.
- Supports independent revocation of evidence without altering service definitions.

### Negative / Trade-offs
- Requires an explicit matching and qualification phase during evaluation rather than simple foreign key lookups.
