# Implementation Plan: PREQVIA

**System**: PREQVIA  
**Document**: Engineering Implementation Plan & Delivery Roadmap  
**Status**: APPROVED / ARCHITECTURAL BASELINE  
**Version**: 1.0.0  
**Date**: 2026-10-07  

---

## 1. Guiding Engineering Philosophy

To avoid premature complexity, architectural rot, and slow feedback loops, PREQVIA adheres to a strict outside-in / inside-out discipline:

1. **Phase 0 First**: Solidify boundaries, domain taxonomy, algorithms, and technical contracts *before* running any scaffolding code.
2. **Pure Domain & Engine Core Before I/O**: The readiness engine is a pure algorithmic solver. It can and must be 100% verified with unit tests without needing a database, network connection, or Docker daemon running.
3. **Additive Persistence**: Database models implement domain interfaces; domain logic does not depend on database or ORM constructs.
4. **Deterministic Verification Gates**: Each phase must pass a defined set of canonical automated tests before progressing to the next.

---

## 2. Phased Roadmap

```
Phase 0: Engineering Foundation & Architecture Baselining (COMPLETED)
   │
   ▼
Phase 1: Pure Domain Model & Deterministic Readiness Engine (In-Memory Core)
   │
   ▼
Phase 2: Relational Persistence Layer (PostgreSQL + SQLAlchemy + Alembic)
   │
   ▼
Phase 3: Application Services & FastAPI REST Layer (With College Fixtures)
   │
   ▼
Phase 4: Modern Web Client (Next.js App Router + Visual Dependency Graphs)
   │
   ▼
Phase 5: Security Hardening, Auditability & Production Deployment
```

---

## 3. Phase Breakdown & Deliverables

### Phase 0: Engineering Foundation & Architecture Baselining
- **Objective**: Establish domain model, algorithm specification, schema contracts, and API contracts.
- **Deliverables**:
  - `docs/architecture.md`: Modular monolith layout and clean architecture boundaries.
  - `docs/domain-model.md`: Domain entity specifications, immutability rules, and ER diagrams.
  - `docs/readiness-engine.md`: Kleene 3-valued logic algebra, 8-phase evaluation pipeline, cycle detection.
  - `docs/database-schema.md`: PostgreSQL schema, indexes, temporal constraints, and JSONB schemas.
  - `docs/api-spec.md`: REST API specification with OpenAPI-aligned request/response models.
  - `docs/architecture-decisions/`: ADR-001 through ADR-006.
- **Exit Criteria**: Architecture approved, contracts frozen.

---

### Phase 1: Pure Domain Model & Deterministic Readiness Engine Core
- **Objective**: Implement the domain entities, value objects, and the 8-phase decision engine in pure Python.
- **Deliverables**:
  - `preqvia-engine/` package (pure Python domain logic).
  - Domain models (`Service`, `RequirementSpec`, `Evidence`, `Dependency`, `LocationSchedule`).
  - Graph solver (`DependencyDAG` with Kahn's topological sort and cycle detection).
  - Kleene tri-state algebraic reducer (`READY`, `BLOCKED`, `UNKNOWN`).
  - Explainer module (Root cause isolation and remediation chain generator).
  - Canonical Unit Test Suite (10 Core Scenarios from Section 14).
- **Exit Criteria**: All 10 canonical test scenarios pass with 100% determinism and 0% I/O dependency.

---

### Phase 2: Relational Persistence Layer
- **Objective**: Implement PostgreSQL persistence, SQLAlchemy async mappings, and Alembic migrations.
- **Deliverables**:
  - `docker-compose.yml` defining PostgreSQL 16 service.
  - SQLAlchemy 2.0 async models matching `docs/database-schema.md`.
  - Alembic migration environment and initial schema migration (`001_initial_schema.py`).
  - Repository layer:
    - `ServiceCatalogRepository`
    - `LocationRepository`
    - `EvidenceVaultRepository`
    - `EvaluationSnapshotRepository`
  - Integration test suite running against test database (via testcontainers or localized Postgres).
- **Exit Criteria**: All repository CRUD and temporal queries validated; Alembic migration passes cleanly in both upgrade and downgrade directions.

---

### Phase 3: Application Services & REST API (FastAPI)
- **Objective**: Expose the readiness engine and catalog via clean RESTful APIs.
- **Deliverables**:
  - FastAPI application structure (`app/api/v1/...`).
  - Evaluation orchestrator application service.
  - Seed fixtures for College Administrative Services:
    - Post-Matric Merit Scholarship Application.
    - Bonafide Certificate Issuance.
    - Fee Clearance Certificate.
  - OpenAPI 3.1 documentation generation (`/docs`, `/redoc`).
  - API integration tests (`test_evaluations_api.py`, `test_evidence_api.py`).
- **Exit Criteria**: HTTP requests to `POST /api/v1/evaluations` return valid tri-state responses and root-cause dependency trees.

---

### Phase 4: Modern Web Client (Next.js App Router)
- **Objective**: Deliver a premium, responsive web interface for students and administrators.
- **Deliverables**:
  - Next.js 14+ App Router project (`frontend/`).
  - Task Feasibility Check Wizard (Service selector, Location selector, Date/Time picker).
  - Interactive Feasibility Card (`READY` in green, `BLOCKED` in amber/red, `UNKNOWN` in blue/purple).
  - Visual Dependency Tree (interactive DAG visualization illustrating root blockers vs secondary symptoms).
  - Evidence Vault Manager (document upload, status indicator, expiration warning badges).
- **Exit Criteria**: User can perform an end-to-end feasibility evaluation in under 3 clicks and immediately view their next action.

---

### Phase 5: Production Hardening, Auditability & Provenance
- **Objective**: Ensure production readiness, security, and administrative provenance.
- **Deliverables**:
  - Append-only audit logger capturing all evaluations and evidence mutations.
  - Provenance citation viewer in the UI linking requirements back to official circulars.
  - Role-Based Access Control (RBAC) separating Students, Clerks, and Administrators.
  - End-to-end automated test suite spanning UI to Backend.
- **Exit Criteria**: Security audit passed; zero data leakage across user evidence vaults; 100% audit compliance.

---

## 4. The 10 Canonical Engine Test Scenarios (Phase 1 Gate)

The core engine cannot be declared complete until it demonstrably passes these 10 automated test cases:

| Test ID | Scenario | Expected Outcome | Critical Verification |
| :--- | :--- | :--- | :--- |
| **TEST-01** | All requirements satisfied, location open | `READY` | Zero blockers, empty remediation list. |
| **TEST-02** | One mandatory document missing | `BLOCKED` | Root blocker identified as missing document. |
| **TEST-03** | Upstream dependency missing (HOD sign missing $\rightarrow$ Principal sign blocked) | `BLOCKED` | Explains dependency chain; points to HOD sign as root blocker. |
| **TEST-04** | User fails eligibility rule (income exceeds threshold) | `BLOCKED` | Eligibility rule blocker flagged with threshold comparison. |
| **TEST-05** | Target time falls outside counter operating hours | `BLOCKED` | Location availability blocker; informs next open time. |
| **TEST-06** | Required document is uploaded but unverified | `UNKNOWN` | Status is strictly `UNKNOWN`; remediation requests verification. |
| **TEST-07** | Document expired 2 days before target date | `BLOCKED` | Temporal validation failure; informs document expiry date. |
| **TEST-08** | Multiple independent blockers (missing doc + closed counter) | `BLOCKED` | Explains all independent root blockers clearly. |
| **TEST-09** | Circular dependency introduced in catalog | `CONFIG_ERROR` | Engine rejects graph with `CyclicDependencyError` before evaluation. |
| **TEST-10** | Multiple distinct services evaluated on same engine | `READY` / `BLOCKED` | Verifies domain agnosticism (same engine runs Scholarship, Bonafide, Fee). |
