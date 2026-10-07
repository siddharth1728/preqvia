# ADR-001: Modular Monolith Architecture Pattern

**Status**: ACCEPTED  
**Date**: 2026-10-07  
**Deciders**: Lead Software Architect  

---

## Context
PREQVIA is designed as a task feasibility engine requiring high determinism, strict relational consistency, and rapid iteration. Initial proposals often suggest microservices (e.g. separating Evidence Service, Catalog Service, Evaluation Service, and Auth Service) or event streaming (Kafka).

However, microservices introduce:
- Distributed transactions and eventual consistency issues.
- Network latency across services during a single evaluation run.
- Complex orchestration and deployment overhead.
- High operational cost for an initial platform.

## Decision
PREQVIA will be implemented as a **Modular Monolith** in Python (FastAPI + SQLAlchemy) with a decoupled Next.js frontend:
- All domain modules (`catalog`, `evidence`, `engine`, `evaluations`, `auth`) reside within the same codebase and process space.
- Boundaries between modules are enforced strictly through internal domain interfaces and application services.
- The Core Readiness Engine has ZERO database or framework dependencies, functioning as a pure domain calculation module.

## Consequences
### Positive
- Zero network latency when traversing requirements and evidence trees.
- ACID transactions for atomic evaluation snapshots and audit logs.
- Single command local development using Docker Compose.
- Highly testable in-memory without mock network endpoints.

### Negative / Trade-offs
- Scaling the engine independently of the API requires running more monolith instances, rather than isolated microservices. (Acceptable, as Python async FastAPI instances scale horizontally with minimal footprint).
