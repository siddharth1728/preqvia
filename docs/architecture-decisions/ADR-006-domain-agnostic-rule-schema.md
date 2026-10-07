# ADR-006: Domain-Agnostic JSON-Logic Rule Specification

**Status**: ACCEPTED  
**Date**: 2026-10-07  
**Deciders**: Lead Software Architect  

---

## Context
PREQVIA's first domain focuses on college administrative services (scholarships, bonafide certificates, fee verification). However, the engine must remain 100% domain-agnostic so it can eventually evaluate banking, healthcare, government, or employment workflows without engine code refactoring.

If eligibility rules (such as income limits, caste categories, or credit scores) are hardcoded into Python `if/else` statements in the engine, the engine will quickly become bloated with domain-specific coupling.

## Decision
1. Rules governing requirement applicability and eligibility conditions are defined as **declarative data**, stored as structured JSON.
2. We adopt the **JSON-Logic** specification (standardized AST of logical operators `==`, `!=`, `>`, `<`, `in`, `and`, `or`, `!`).
3. The engine evaluates JSON-Logic predicates against the subject's `profile_data` without knowing domain semantics:
   - College: `{"<": [{"var": "income"}, 250000]}`
   - Healthcare: `{">=": [{"var": "patient_age"}, 60]}`
   - Banking: `{">": [{"var": "credit_score"}, 700]}`
4. The engine executes these predicates through a sandboxed, deterministic evaluator.

## Consequences
### Positive
- Zero domain code in the engine; new services and domains are configured via database records or JSON fixtures.
- Safe execution: no dynamic Python code evaluation (`eval()` is strictly forbidden).
- Easily serialized, versioned, and edited via admin interfaces.

### Negative / Trade-offs
- Complex multi-step business logic must be broken down into clean JSON-Logic expressions.
