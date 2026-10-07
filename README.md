# PREQVIA — Real-World Task Completion Feasibility Engine

> **"Given this person, this task, this service, this location, and this time, can this task actually be completed?"**

PREQVIA is a deterministic, explainable, and domain-agnostic decision engine that determines whether real-world administrative tasks can be completed before travelling or starting.

Feasibility outcomes resolve strictly to one of three states:
- **`READY`**: All requirements, approvals, evidence, dependencies, and operational hours are proven to be satisfied.
- **`BLOCKED`**: One or more conditions are definitively unsatisfied, with root causes and upstream dependency chains isolated.
- **`UNKNOWN`**: Critical information is missing or unverified, preventing a definitive answer without guessing.

---

## 🏛️ Architecture & Documentation

- [Architecture Overview](docs/architecture.md) — Modular monolith structure, component boundaries, and clean-architecture layers.
- [Domain Model Specification](docs/domain-model.md) — Entities, value objects, immutability rules, and ER diagrams.
- [Readiness Decision Engine](docs/readiness-engine.md) — Kleene 3-valued logic, 8-phase evaluation pipeline, and DAG traversal algorithms.
- [Database Schema](docs/database-schema.md) — PostgreSQL schema, constraints, indexes, and JSONB validation specifications.
- [RESTful API Specification](docs/api-spec.md) — OpenAPI-aligned REST endpoints and RFC 7807 error responses.
- [Implementation Plan](docs/implementation-plan.md) — Phased delivery roadmap and 10 canonical test cases.
- [Phase 1A Delivery Report](docs/phase-1a.md) — Pure domain foundation, invariants, and test verification.
- [Architecture Decision Records (ADRs)](docs/architecture-decisions/)
  - [ADR-001: Modular Monolith Architecture Pattern](docs/architecture-decisions/ADR-001-modular-monolith.md)
  - [ADR-002: Deterministic Tri-State Logic (Kleene 3-Valued Algebra)](docs/architecture-decisions/ADR-002-deterministic-tri-state-readiness-engine.md)
  - [ADR-003: Strict Separation of Requirement Specifications and Evidence](docs/architecture-decisions/ADR-003-separation-of-requirements-and-evidence.md)
  - [ADR-004: Directed Acyclic Graph (DAG) for Prerequisite Dependencies](docs/architecture-decisions/ADR-004-directed-acyclic-graph-dependency-modeling.md)
  - [ADR-005: Provenance Tracking and Temporal Validity Modeling](docs/architecture-decisions/ADR-005-provenance-and-temporal-validity.md)
  - [ADR-006: Domain-Agnostic JSON-Logic Rule Specification](docs/architecture-decisions/ADR-006-domain-agnostic-rule-schema.md)

---

## 🛣️ Phased Roadmap

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 0** | Engineering Foundation, Architecture Baselining & Documentation | **COMPLETED** |
| **Phase 1A** | Pure Domain Foundation (Zero I/O, In-Memory Models & Kleene Logic) | **COMPLETED** |
| **Phase 1B** | Deterministic Readiness Engine Algorithm & 10 Canonical Scenarios | Queued |
| **Phase 2** | Relational Persistence Layer (PostgreSQL, SQLAlchemy, Alembic) | Queued |
| **Phase 3** | Application Services & FastAPI REST Layer | Queued |
| **Phase 4** | Modern Web Client (Next.js App Router, Visual DAG Explorer) | Queued |
| **Phase 5** | Security Hardening, Audit Trails & Provenance Tracing | Queued |

