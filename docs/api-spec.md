# API Specification: PREQVIA RESTful Service

**System**: PREQVIA  
**Document**: RESTful HTTP API Specification (OpenAPI 3.1 Aligned)  
**Base Path**: `/api/v1`  
**Status**: APPROVED / ARCHITECTURAL BASELINE  
**Version**: 1.0.0  
**Date**: 2026-10-07  

---

## 1. Design Conventions & Standards

- **Standard REST Verbs**: `GET`, `POST`, `PUT`, `DELETE`.
- **Payload Format**: `application/json; charset=utf-8`.
- **Error Format**: RFC 7807 Problem Details (`application/problem+json`).
- **Date/Time Representation**: ISO 8601 with explicit UTC offsets (`YYYY-MM-DDTHH:MM:SSZ` or `+05:30`).
- **Idempotency**: Evaluation creation is safe to call repeatedly with the same payload; each call produces an immutable evaluation ID.

---

## 2. Core Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness and database connectivity check. |
| `GET` | `/services` | List active services with organization details. |
| `GET` | `/services/{id}/requirements` | Get active requirement specification graph & provenance. |
| `GET` | `/locations/{id}/schedule` | Get weekly hours and exception schedule for a location. |
| `POST` | `/users/{id}/evidence` | Upload / register an evidence item into user's vault. |
| `GET` | `/users/{id}/evidence` | List all current evidence items for a user. |
| `POST` | `/evidence/{id}/verify` | Submit an administrative verification record for evidence. |
| **`POST`** | **`/evaluations`** | **Execute task feasibility decision engine (Core Endpoint).** |
| `GET` | `/evaluations/{id}` | Retrieve historical evaluation result, DAG nodes, & remediations. |

---

## 3. Flagship Endpoint: Feasibility Evaluation

### `POST /api/v1/evaluations`
Executes the deterministic readiness engine against the requested subject, service, location, and target time.

#### Request Body
```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "service_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "location_id": "e2a1b94d-4c8d-4fad-8b11-5d9c7a2b9f1a",
  "target_time": "2026-10-08T11:00:00+05:30"
}
```

#### Response: `200 OK` (Example: Status BLOCKED by Upstream Dependency)
```json
{
  "evaluation_id": "c1f72a9e-862d-4547-b248-132dcb39498a",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "service_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "service_code": "COLLEGE_SCHOLARSHIP_SUBMISSION",
  "service_title": "Post-Matric Merit Scholarship Application",
  "service_version": "2026.1",
  "location_name": "Administrative Counter 3 (Room 104)",
  "target_time": "2026-10-08T11:00:00+05:30",
  "evaluated_at": "2026-10-07T20:50:00Z",
  "overall_status": "BLOCKED",
  "summary_reason": "Task cannot be completed because Principal Signature is missing, which is blocked by missing Department Approval.",
  "metrics": {
    "total_requirements": 5,
    "satisfied": 2,
    "unsatisfied": 1,
    "blocked_by_dependency": 2,
    "unknown": 0
  },
  "root_blockers": [
    {
      "requirement_code": "REQ_DEPT_APPROVAL",
      "title": "Head of Department (HOD) Endorsement",
      "category": "APPROVAL",
      "reason": "No valid HOD endorsement record found in user vault."
    }
  ],
  "dependency_chains": [
    {
      "root_blocker": "REQ_DEPT_APPROVAL",
      "chain": [
        "REQ_DEPT_APPROVAL",
        "REQ_PRINCIPAL_SIGNATURE",
        "REQ_FINAL_SUBMISSION"
      ]
    }
  ],
  "nodes": [
    {
      "requirement_code": "REQ_LOCATION_AVAILABILITY",
      "title": "Counter Operating Hours",
      "category": "SERVICE_AVAILABILITY",
      "status": "SATISFIED",
      "reason": "Administrative Counter 3 is open on Thursday from 09:30 to 16:30.",
      "blocked_by": []
    },
    {
      "requirement_code": "REQ_BONAFIDE_CERTIFICATE",
      "title": "Current Academic Year Bonafide Certificate",
      "category": "DOCUMENT",
      "status": "SATISFIED",
      "matched_evidence_id": "77f82b1c-99a1-46df-9d31-411a7a40b92e",
      "reason": "Valid certificate verified by College Office on 2026-09-15.",
      "blocked_by": []
    },
    {
      "requirement_code": "REQ_DEPT_APPROVAL",
      "title": "Head of Department (HOD) Endorsement",
      "category": "APPROVAL",
      "status": "UNSATISFIED",
      "reason": "Missing required HOD signature.",
      "blocked_by": []
    },
    {
      "requirement_code": "REQ_PRINCIPAL_SIGNATURE",
      "title": "College Principal Final Endorsement",
      "category": "APPROVAL",
      "status": "BLOCKED_BY_DEPENDENCY",
      "reason": "Cannot obtain Principal Signature until HOD Endorsement is satisfied.",
      "blocked_by": ["REQ_DEPT_APPROVAL"]
    },
    {
      "requirement_code": "REQ_FINAL_SUBMISSION",
      "title": "Physical Counter Submission",
      "category": "PREREQUISITE_TASK",
      "status": "BLOCKED_BY_DEPENDENCY",
      "reason": "Blocked because Principal Endorsement is incomplete.",
      "blocked_by": ["REQ_PRINCIPAL_SIGNATURE"]
    }
  ],
  "next_actions": [
    {
      "step_order": 1,
      "requirement_code": "REQ_DEPT_APPROVAL",
      "action_type": "OBTAIN_SIGNATURE",
      "instruction": "Visit Computer Science Department Office (Room 201) to obtain HOD signature on application form."
    },
    {
      "step_order": 2,
      "requirement_code": "REQ_PRINCIPAL_SIGNATURE",
      "action_type": "OBTAIN_SIGNATURE",
      "instruction": "Submit HOD-signed form to Principal Office Secretary (Room 101) for final endorsement."
    }
  ]
}
```

#### Response: `200 OK` (Example: Status UNKNOWN)
```json
{
  "evaluation_id": "d82a174c-4e89-4b1f-a392-710c4974f289",
  "overall_status": "UNKNOWN",
  "summary_reason": "Feasibility cannot be determined: Income certificate was uploaded but verification status is pending at the revenue office.",
  "unknown_factors": [
    {
      "requirement_code": "REQ_INCOME_CERTIFICATE",
      "title": "Revenue Authority Income Certificate",
      "reason": "Document uploaded on 2026-10-06 is awaiting administrative verification.",
      "evidence_id": "b91c2847-19a4-4a57-8fc4-937d110f4671"
    }
  ],
  "next_actions": [
    {
      "step_order": 1,
      "requirement_code": "REQ_INCOME_CERTIFICATE",
      "action_type": "VERIFY_EVIDENCE",
      "instruction": "Contact Student Affairs Clerk at Counter 1 to expedite pending document verification."
    }
  ]
}
```

---

## 4. Evidence Management Endpoints

### `POST /api/v1/users/{user_id}/evidence`
Adds a document or credential attestation to the user's evidence vault.

#### Request Body
```json
{
  "evidence_type": "DOCUMENT",
  "evidence_code": "BONAFIDE_CERTIFICATE",
  "document_storage_uri": "s3://preqvia-docs/students/2026/bonafide_001.pdf",
  "payload_data": {
    "issue_date": "2026-09-15",
    "academic_year": "2026-2027",
    "certificate_number": "BON-2026-9921"
  },
  "valid_from": "2026-09-15T00:00:00Z",
  "valid_until": "2027-03-15T23:59:59Z"
}
```

#### Response: `201 Created`
```json
{
  "evidence_id": "77f82b1c-99a1-46df-9d31-411a7a40b92e",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "evidence_code": "BONAFIDE_CERTIFICATE",
  "status": "UNVERIFIED",
  "created_at": "2026-10-07T20:50:00Z"
}
```

### `POST /api/v1/evidence/{evidence_id}/verify`
Enables an administrator or authorized service to verify an evidence record.

#### Request Body
```json
{
  "verifier_type": "MANUAL_ADMIN",
  "verifier_identity": "admin_clerk_sharma",
  "status": "VERIFIED",
  "notes": "Original stamp verified against college register."
}
```

---

## 5. Service Catalog & Provenance Endpoints

### `GET /api/v1/services/{service_id}/requirements`
Returns the active requirement graph for a service, including provenance citations.

#### Response: `200 OK`
```json
{
  "service_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "version": "2026.1",
  "requirements": [
    {
      "code": "REQ_BONAFIDE_CERTIFICATE",
      "title": "Current Academic Year Bonafide Certificate",
      "category": "DOCUMENT",
      "is_mandatory": true,
      "provenance": {
        "source_title": "University Scholarship Handbook 2026",
        "citation_reference": "Section 4.1 (Mandatory Documents)",
        "source_uri": "https://university.edu/guidelines/scholarships-2026.pdf",
        "digest_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      }
    }
  ],
  "dependencies": [
    {
      "upstream": "REQ_DEPT_APPROVAL",
      "downstream": "REQ_PRINCIPAL_SIGNATURE",
      "type": "HARD_PREREQUISITE"
    }
  ]
}
```

---

## 6. Error Handling Standards (RFC 7807)

```json
{
  "type": "https://preqvia.org/errors/cyclical-dependency",
  "title": "Cyclical Dependency Detected in Service Catalog",
  "status": 409,
  "detail": "Requirement 'REQ_A' depends on 'REQ_B', which indirectly depends on 'REQ_A'.",
  "instance": "/api/v1/services/9b1deb4d/validate"
}
```
