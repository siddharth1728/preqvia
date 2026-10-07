# Database Schema Specification: PREQVIA

**System**: PREQVIA  
**Document**: Relational Database Schema & Data Modeling  
**Target Engine**: PostgreSQL 16+  
**ORM Target**: SQLAlchemy 2.0 (Declarative Base, Async)  
**Migration Tool**: Alembic  
**Status**: APPROVED / ARCHITECTURAL BASELINE  
**Version**: 1.0.0  
**Date**: 2026-10-07  

---

## 1. Schema Design Principles

1. **Strict Referential Integrity**: Foreign keys enforce exact lineage across organizations, services, and evaluations.
2. **Temporal Correctness**: All temporal ranges enforce integrity through SQL check constraints (`valid_until IS NULL OR valid_until >= valid_from`).
3. **Immutability of Audit Trails and Evaluations**: Evaluation records and node snapshots are append-only. No `UPDATE` operations are permitted on evaluation tables.
4. **JSONB for Extensible Validation Rules**: Domain-agnostic predicates (rules) and evidence metadata use PostgreSQL `JSONB` columns with structured schema definitions, indexed via GIN where necessary.

---

## 2. Table Definitions & DDL Specifications

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. ORGANIZATIONS & LOCATIONS
-- ==========================================

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    org_type VARCHAR(64) NOT NULL, -- COLLEGE, GOVT_OFFICE, BANK, HEALTHCARE
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    code VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    room_or_counter VARCHAR(128),
    building VARCHAR(128),
    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_location_org_code UNIQUE (organization_id, code)
);

CREATE TABLE location_operating_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Sunday, 6=Saturday
    open_time TIME NOT NULL,
    close_time TIME NOT NULL,
    break_start TIME,
    break_end TIME,
    CONSTRAINT chk_open_before_close CHECK (open_time < close_time),
    CONSTRAINT chk_break_order CHECK (break_start IS NULL OR (break_start < break_end AND break_start >= open_time AND break_end <= close_time)),
    CONSTRAINT uq_location_day UNIQUE (location_id, day_of_week)
);

CREATE TABLE location_schedule_exceptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    exception_date DATE NOT NULL,
    is_closed BOOLEAN NOT NULL DEFAULT FALSE,
    override_open_time TIME,
    override_close_time TIME,
    reason VARCHAR(255) NOT NULL,
    CONSTRAINT uq_location_exception_date UNIQUE (location_id, exception_date)
);

-- ==========================================
-- 2. PROVENANCE & SOURCES
-- ==========================================

CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    code VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    source_type VARCHAR(64) NOT NULL, -- OFFICIAL_CIRCULAR, PORTAL_GUIDELINE, STATUTE
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE source_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    citation_reference VARCHAR(255) NOT NULL,
    source_uri TEXT,
    content_hash VARCHAR(64), -- SHA-256 digest of original circular
    published_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_source_citation UNIQUE (source_id, citation_reference)
);

-- ==========================================
-- 3. SERVICES & REQUIREMENTS CATALOG
-- ==========================================

CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    code VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_service_org_code UNIQUE (organization_id, code)
);

CREATE TABLE service_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    version_tag VARCHAR(32) NOT NULL, -- e.g. "2026.1"
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT', -- DRAFT, ACTIVE, DEPRECATED
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_service_version UNIQUE (service_id, version_tag)
);

CREATE TABLE requirement_specifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_version_id UUID NOT NULL REFERENCES service_versions(id) ON DELETE CASCADE,
    source_version_id UUID REFERENCES source_versions(id) ON DELETE SET NULL,
    code VARCHAR(64) NOT NULL, -- e.g. REQ_BONAFIDE_CERT, REQ_PRINCIPAL_SIGN
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(64) NOT NULL, -- DOCUMENT, APPROVAL, ATTESTATION, CRITERION, LOCATION_PRESENCE
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    applicability_rule JSONB, -- JSONLogic condition under which this requirement applies
    validation_spec JSONB NOT NULL, -- Match criteria: evidence_type, max_age_days, verifiers
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_req_service_code UNIQUE (service_version_id, code)
);

CREATE TABLE dependency_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_version_id UUID NOT NULL REFERENCES service_versions(id) ON DELETE CASCADE,
    upstream_req_code VARCHAR(64) NOT NULL,
    downstream_req_code VARCHAR(64) NOT NULL,
    dependency_type VARCHAR(32) NOT NULL DEFAULT 'HARD_PREREQUISITE', -- HARD_PREREQUISITE, TEMPORAL
    CONSTRAINT chk_no_self_dependency CHECK (upstream_req_code <> downstream_req_code),
    CONSTRAINT uq_dependency_edge UNIQUE (service_version_id, upstream_req_code, downstream_req_code)
);

-- ==========================================
-- 4. USERS & EVIDENCE VAULT
-- ==========================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(128) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'USER', -- USER, ADMIN, VERIFIER
    profile_data JSONB NOT NULL DEFAULT '{}'::jsonb, -- e.g. student_id, caste_category, annual_income
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE evidence_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    evidence_type VARCHAR(64) NOT NULL, -- DOCUMENT, APPROVAL, ATTESTATION, ATTRIBUTE
    evidence_code VARCHAR(64) NOT NULL, -- e.g. INCOME_CERTIFICATE, BONAFIDE_CERTIFICATE
    document_storage_uri TEXT,
    payload_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revocation_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_evidence_temporal_order CHECK (valid_until IS NULL OR valid_until >= valid_from)
);

CREATE TABLE evidence_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evidence_id UUID NOT NULL REFERENCES evidence_records(id) ON DELETE CASCADE,
    verifier_type VARCHAR(64) NOT NULL, -- SYSTEM_AUTOMATED, MANUAL_ADMIN, THIRD_PARTY_API
    verifier_identity VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL, -- VERIFIED, REJECTED, UNVERIFIABLE
    notes TEXT,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 5. EVALUATIONS & AUDIT LOGS
-- ==========================================

CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
    service_version_id UUID NOT NULL REFERENCES service_versions(id) ON DELETE RESTRICT,
    location_id UUID REFERENCES locations(id) ON DELETE RESTRICT,
    target_time TIMESTAMPTZ NOT NULL,
    overall_status VARCHAR(32) NOT NULL CHECK (overall_status IN ('READY', 'BLOCKED', 'UNKNOWN')),
    summary_reason TEXT NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE evaluation_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    requirement_code VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('SATISFIED', 'UNSATISFIED', 'BLOCKED_BY_DEPENDENCY', 'UNKNOWN', 'NOT_APPLICABLE')),
    matched_evidence_id UUID REFERENCES evidence_records(id) ON DELETE SET NULL,
    blocker_reason TEXT,
    blocked_by_codes VARCHAR(64)[] NOT NULL DEFAULT '{}'
);

CREATE TABLE evaluation_remediations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    step_order SMALLINT NOT NULL,
    requirement_code VARCHAR(64) NOT NULL,
    action_type VARCHAR(64) NOT NULL, -- OBTAIN_DOCUMENT, OBTAIN_SIGNATURE, RESCHEDULE_TIME, VERIFY_EVIDENCE
    instruction TEXT NOT NULL
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(64) NOT NULL,
    entity_name VARCHAR(64) NOT NULL,
    entity_id UUID NOT NULL,
    changes JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==========================================
-- 6. PERFORMANCE INDEXES
-- ==========================================

CREATE INDEX idx_locations_org ON locations(organization_id);
CREATE INDEX idx_services_org ON services(organization_id);
CREATE INDEX idx_service_versions_active ON service_versions(service_id, status);
CREATE INDEX idx_reqs_service_ver ON requirement_specifications(service_version_id);
CREATE INDEX idx_deps_service_ver ON dependency_edges(service_version_id);
CREATE INDEX idx_evidence_user_code ON evidence_records(user_id, evidence_code);
CREATE INDEX idx_evidence_validity ON evidence_records(user_id, valid_from, valid_until);
CREATE INDEX idx_evaluations_user ON evaluations(user_id);
CREATE INDEX idx_evaluation_nodes_eval ON evaluation_nodes(evaluation_id);
CREATE INDEX idx_audit_entity ON audit_logs(entity_name, entity_id);
```

---

## 3. JSONB Structures and Schemas

### 3.1 `requirement_specifications.validation_spec`
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["evidence_code", "acceptable_types"],
  "properties": {
    "evidence_code": { "type": "string", "example": "BONAFIDE_CERTIFICATE" },
    "acceptable_types": { "type": "array", "items": { "type": "string" }, "example": ["DOCUMENT"] },
    "max_age_days": { "type": "integer", "example": 180 },
    "required_verification_status": { "type": "string", "enum": ["VERIFIED", "ANY"], "default": "VERIFIED" },
    "match_attributes": {
      "type": "object",
      "example": { "academic_year": "2026-2027" }
    }
  }
}
```

### 3.2 `requirement_specifications.applicability_rule`
Structured as domain-agnostic JSON-Logic:
```json
{
  "and": [
    { "==": [{ "var": "subject.college_enrolled" }, true] },
    { "<": [{ "var": "subject.annual_income" }, 250000] }
  ]
}
```
If `applicability_rule` evaluates to `false`, the requirement is marked `NOT_APPLICABLE` and does not block the evaluation.
