# Technical Design Document

## Overview

This document describes the technical design for the DPDP Compliant Redactable Blockchain Based Healthcare and Pharmacy Management System. The platform enables patients to fully control their personal and health data through consent management, AES-256 encryption, blockchain verification, and Chameleon Hash-based authorized redaction — all compliant with India's Digital Personal Data Protection Act (2023).

The system uses a hybrid blockchain architecture where healthcare data is stored encrypted in MongoDB while only SHA-256 verification hashes are anchored on-chain via Ganache (local Ethereum). This separation satisfies the DPDP right to erasure (data can be redacted off-chain) while preserving blockchain immutability (hash proofs remain permanently verifiable).

**Technology Stack**: Flask (Python), React (TypeScript), MongoDB, Ethereum/Ganache, Web3.py, AES-256 Fernet encryption, Chameleon Hash simulation.

**Detailed design documents**: Architecture (`architecture.md`), Database (`database_design.md`), Blockchain (`blockchain_design.md`), Security (`security_design.md`), DPDP Compliance (`dpdp_compliance.md`), UI/UX (`ui_ux_design.md`), Roadmap (`implementation_roadmap.md`).

## Architecture

### System Layers

The system follows a 6-layer defense-in-depth architecture:

1. **Client Layer** — React SPA with TypeScript, Tailwind CSS, Shadcn UI. Role-based views for Patient, Doctor, Pharmacy, Admin, DPO.
2. **API Gateway Layer** — Rate limiter (token bucket), JWT validator (HS256/RS256), session manager (IP/UA binding), CORS/security headers.
3. **Application Layer** — Flask blueprints (auth, patients, consents, doctors, pharmacy, audit, blockchain, integrity, compliance). Service layer with 15+ services. Middleware pipeline: RequestID → RateLimit → JWT → Session → RBAC → AuditLog → Handler.
4. **Data Layer** — MongoDB 7.x (11 collections, field-level AES-256-GCM encryption, UUID identifiers). Separate key management store.
5. **Blockchain Layer** — Ganache node (local Ethereum, chain ID 1337). Raw transactions with SHA-256 hash payloads. No smart contracts in MVP (planned post-MVP).
6. **Security Layer** — Chameleon Hash Engine (simulation via proof-chain linking), AES-256 Fernet encryption, bcrypt password hashing, breach detection rules.

### Deployment Topology

All infrastructure deployed within Indian data centers (DPDP Act compliance). MongoDB 3-node replica set, Ganache primary + backup, separate key store, Docker Compose orchestration.

### Communication Patterns

| From → To | Protocol | Auth |
|-----------|----------|------|
| Client → Backend | HTTPS/TLS 1.3 | JWT Bearer |
| Backend → MongoDB | MongoDB Wire/TLS | X.509 |
| Backend → Ganache | JSON-RPC/HTTP | Signed transactions |
| Backend → Key Store | Internal | Certificate |

## Components and Interfaces

### Backend Services

| Service | Purpose | Key Methods |
|---------|---------|-------------|
| `AuthService` | Registration, login, JWT, RBAC, lockout | `register()`, `login()`, `verify_token()` |
| `PatientService` | Patient profile CRUD with encryption | `create_patient_profile()`, `get_patient_by_user_id()`, `update_patient_profile()` |
| `HealthcareRecordService` | Clinical record CRUD, ownership enforcement | `create_record()`, `get_record()`, `update_record()` |
| `ConsentService` | Consent lifecycle (grant/modify/withdraw/expiry) | `grant_consent()`, `withdraw_consent()`, `modify_consent()` |
| `AuditService` | Immutable audit logging with hash chain | `log_event()`, `log_data_access()`, `get_patient_timeline()` |
| `EncryptionService` | AES-256 Fernet field/document encryption | `encrypt_field()`, `decrypt_field()`, `encrypt_document()`, `decrypt_document()` |
| `BlockchainService` | Ganache hash anchoring, verification | `anchor_record()`, `verify_record()`, `compute_record_hash()` |
| `ChameleonHashSimulator` | Authorized redaction with proof chain | `create_redaction_request()`, `authorize_redaction()`, `execute_correction()`, `execute_erasure()`, `verify_record_integrity()` |
| `ComplianceService` | DPDP dashboard, scoring, rights tracking | `get_dashboard()`, `get_compliance_score()`, `get_rights_requests()` |

### API Blueprint Routes

| Blueprint | Prefix | Endpoints | Access |
|-----------|--------|-----------|--------|
| `auth` | `/api/v1/auth` | register, login, me, protected-test | Public + JWT |
| `patients` | `/api/v1/patients` | profile CRUD, records CRUD, correct, erase | Patient + Admin |
| `consents` | `/api/v1/consents` | grant, withdraw, modify, receipts, active-sharing | Patient |
| `audit` | `/api/v1/audit` | timeline, access-history, logs, stats | Patient + Admin |
| `integrity` | `/api/v1/integrity` | verify record, status, anchors | Patient + Admin |
| `blockchain` | `/api/v1/blockchain` | status, patient anchors | Admin + Patient |
| `compliance` | `/api/v1/compliance` | dashboard, stats, rights-requests, score | Admin |

### Middleware Pipeline

```
Request → RequestID → RateLimit → JWT Validation → Session Check → RBAC → Handler → Audit Log → Response
```

## Data Models

### MongoDB Collections (11 MVP)

| Collection | Purpose | Encrypted Fields |
|------------|---------|-----------------|
| `users` | Authentication, roles | email, mfa_secret, date_of_birth |
| `patients` | Patient profiles | full_name, phone_number, address, identity_number, blood_group, allergies, chronic_conditions |
| `healthcare_records` | Clinical records | title, description, diagnosis_codes, symptoms, treatment_notes |
| `prescriptions` | Medications | medications, diagnosis_summary, instructions |
| `consents` | Consent lifecycle | None (no PII) |
| `consent_receipts` | Consent proof docs | None |
| `audit_logs` | Immutable audit trail | None (hash-chained) |
| `blockchain_anchors` | On-chain tx references | None |
| `version_history` | Archived record versions | record_snapshot |
| `chameleon_hash_records` | Redaction proofs | original_randomness, new_randomness, collision_proof |
| `data_access_logs` | Patient timeline | None |

### Key Design Decisions

- **UUID v4** for all `_id` fields — no MongoDB ObjectId exposed
- **SHA-256 hash fields** for encrypted lookups (email_hash, identity_number_hash)
- **Append-only** audit_logs with previous_log_hash chain
- **NEVER_ENCRYPT_FIELDS** set preserves queryability (_id, patient_id, status, version, record_type, etc.)

## Correctness Properties

The system must satisfy the following formal properties:

### Property 1: Encryption Roundtrip

For any sensitive field value V, `decrypt(encrypt(V)) == V`. The AES-256 Fernet encryption guarantees authenticated encryption — decryption verifies both confidentiality and integrity.

### Property 2: Hash Determinism

For any record R, `compute_record_hash(R) == compute_record_hash(R)`. Canonical JSON serialization (sorted keys, no whitespace) ensures identical content always produces the same SHA-256 hash.

### Property 3: Consent Enforcement

If no active consent exists for (patient_id, consent_type), then any data access request for categories mapped to that consent type returns HTTP 403. The system NEVER returns data without valid consent.

### Property 4: Ownership Isolation

Patient A cannot read, modify, correct, or erase Patient B's records. Every data access operation verifies `record.patient_id == requesting_patient._id`.

### Property 5: Audit Completeness

Every state-changing operation (create, update, delete, consent_grant, consent_withdraw, consent_modify, login) produces exactly one entry in the `audit_logs` collection with actor, timestamp, resource, and action details.

### Property 6: Blockchain Anchoring

Every healthcare record create or update produces a `blockchain_anchors` entry containing the SHA-256 hash of the encrypted record state. If Ganache is connected, a real Ethereum transaction is submitted.

### Property 7: Verification Integrity

`verify_record(record) == VERIFIED` if and only if `compute_record_hash(current_record) == latest_blockchain_anchor.data_hash`. Any mismatch without a valid chameleon proof chain returns INTEGRITY_VIOLATION.

### Property 8: Chameleon Redaction Validity

After an authorized correction or erasure, the `chameleon_hash_records` collection contains a proof document with `status=executed`, linking `original_hash` to `modified_hash` with authorizer identity and legal basis. The `verify_record_integrity()` function recognizes this proof chain and returns VERIFIED_MODIFIED or VERIFIED_REDACTED.

### Property 9: Version Preservation

Every correction or erasure operation creates a `version_history` document containing the complete pre-modification record snapshot, modification type, reason, authorizer, and legal basis. No previous state is ever lost.

### Property 10: Consent Withdrawal Immediacy

After `withdraw_consent()` completes, the consent status is `withdrawn` and any subsequent data access request for that purpose is denied within the same HTTP request cycle (no eventual consistency delay).

## Error Handling

### Strategy

- All errors return JSON: `{"error": true, "message": "...", "status_code": N, "details": {}}`
- Custom exception hierarchy: `AppError` → `AuthenticationError` (401), `AuthorizationError` (403), `NotFoundError` (404), `ValidationError` (422), `ConsentRequiredError` (403), `RateLimitError` (429)
- Flask error handlers registered for 400, 404, 500 + all AppError subclasses
- Encryption failures return `[DECRYPTION_FAILED]` marker without crashing
- Blockchain anchoring is non-blocking — failures logged but don't prevent record operations
- Ganache connection uses 3-second timeout to prevent request hangs

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | Success | GET, PUT, POST (consent withdraw) |
| 201 | Created | POST (register, record create, consent grant) |
| 401 | Unauthorized | Missing/invalid/expired JWT |
| 403 | Forbidden | Wrong role, consent not granted, not owner |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Invalid input fields |
| 429 | Rate Limited | Request threshold exceeded |
| 500 | Server Error | Unhandled exception |

## Testing Strategy

### Test Suite (129+ automated tests)

| Test File | Count | Coverage |
|-----------|-------|----------|
| `test_auth.py` | 20 | Registration, login, JWT, RBAC, lockout |
| `test_healthcare_records.py` | 19 | CRUD, ownership, validation, versioning |
| `test_consents.py` | 24 | Grant, modify, withdraw, receipts, sharing |
| `test_audit.py` | 15 | Event logging, timeline, admin access |
| `test_encryption.py` | 16 | Field/doc encrypt, MongoDB ciphertext, API plaintext |
| `test_blockchain.py` | 16 | Hash computation, anchoring, verification |
| `test_chameleon_hash.py` | 19 | Simulation unit tests (5 behaviors) |
| `test_chameleon_integration.py` | 17 | Correction, erasure, audit, verification states |
| `test_compliance.py` | 12 | Dashboard, stats, rights, scoring |

### Testing Approach

- **Integration tests** using Flask test client + real MongoDB (test database)
- **Property tests** for encryption roundtrip and hash determinism
- **Negative tests** for authorization, ownership, validation boundaries
- **State machine tests** for consent lifecycle transitions

### Running Tests

```bash
cd backend
python -m pytest tests/ -v          # All tests
python -m pytest tests/ -q          # Quick summary
python -m pytest tests/test_auth.py # Single module
```
