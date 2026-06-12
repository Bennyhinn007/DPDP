# Database Design Document

## DPDP Compliant Redactable Blockchain Based Healthcare and Pharmacy Management System

---

## 1. Database Overview

### 1.1 Database Engine

- **Engine**: MongoDB 7.x
- **Deployment**: 3-node Replica Set (Primary + 2 Secondary)
- **Location**: India-region data centers only (DPDP Act compliance)
- **Database Name**: `dpdp_healthcare_db`

### 1.2 Design Principles

| Principle | Implementation |
|-----------|---------------|
| UUID-First | All collections use UUID v4 as `_id` field. No MongoDB ObjectId exposed to users |
| Encryption-at-Field-Level | Sensitive fields encrypted with AES-256-GCM before storage |
| Audit-by-Default | Every document carries `created_at`, `updated_at`, `created_by`, `updated_by` |
| Soft-Delete + Redaction | Deleted data is redacted (replaced with `[REDACTED]`), never hard-deleted |
| Version Tracking | All mutable documents reference `version_history` collection |
| Blockchain Anchoring | State-changing operations produce entries in `blockchain_anchors` |
| Data Residency | All documents carry `data_residency` metadata field |

### 1.3 UUID Strategy

```
Format: UUID v4 (RFC 4122)
Example: "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

Storage: String type in MongoDB (_id field)
Generation: Server-side using Python uuid.uuid4()
Exposure: Only UUID exposed in API responses, never ObjectId
Cross-Reference: All foreign keys use UUID strings
```

### 1.4 Encryption Field Notation

Fields marked with 🔐 are encrypted at rest using AES-256-GCM before storage. The stored value is a JSON object:

```json
{
  "ciphertext": "base64-encoded-encrypted-data",
  "iv": "base64-encoded-initialization-vector",
  "tag": "base64-encoded-gcm-auth-tag",
  "key_id": "uuid-of-encryption-key-used"
}
```

---

## 2. Entity Relationship Design

### 2.1 Core Relationships

```
organizations (1) ──────── (N) users
users (1) ─────────────── (1) patients | doctors | pharmacy_staff
patients (1) ──────────── (N) healthcare_records
patients (1) ──────────── (N) prescriptions
patients (1) ──────────── (N) lab_reports
patients (1) ──────────── (N) consents
consents (1) ──────────── (N) consent_receipts
patients (1) ──────────── (N) grievance_requests
patients (1) ──────────── (N) notifications
users (1) ─────────────── (N) audit_logs (as actor)
patients (1) ──────────── (N) data_access_logs (as subject)
patients (1) ──────────── (N) integrity_verifications
All state changes ─────── (N) blockchain_anchors
All mutable docs ──────── (N) version_history
```

### 2.2 Guardian Relationship (Minors)

```
users [Guardian] (1) ──── (N) patients [Minor, age < 18]
  └── guardian_id field in patients collection
  └── Guardian has full management access until minor turns 18
```

### 2.3 Processor Relationships

```
organizations (1) ──────── (N) data_processors
data_processors (1) ───── (N) data_access_logs
data_processors (1) ───── (N) consents (as processing_entity)
```

---

## 3. Collection Schemas

---

### 3.1 `users`

**Purpose**: Central authentication and identity collection for all user roles.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `email` | String | Yes | 🔐 | Login email (unique, encrypted) |
| `email_hash` | String | Yes | No | SHA-256 hash of email for lookup |
| `password_hash` | String | Yes | No | bcrypt hash (cost factor 12) |
| `role` | String (Enum) | Yes | No | `patient`, `doctor`, `pharmacy_staff`, `admin`, `dpo` |
| `status` | String (Enum) | Yes | No | `active`, `locked`, `suspended`, `pending_verification` |
| `mfa_enabled` | Boolean | Yes | No | Multi-factor auth status |
| `mfa_secret` | String | No | 🔐 | TOTP secret key |
| `failed_login_attempts` | Integer | Yes | No | Counter for lockout logic |
| `locked_until` | DateTime | No | No | Account lockout expiry |
| `last_login` | DateTime | No | No | Last successful authentication |
| `organization_id` | String (UUID) | Yes | No | FK → organizations._id |
| `is_minor` | Boolean | Yes | No | Age < 18 flag |
| `date_of_birth` | String | Yes | 🔐 | DOB for age verification |
| `date_of_birth_hash` | String | Yes | No | SHA-256 hash for age computation |
| `guardian_id` | String (UUID) | No | No | FK → users._id (for minors) |
| `data_residency` | Object | Yes | No | `{ region: "IN", verified_at: DateTime }` |
| `created_at` | DateTime | Yes | No | Registration timestamp |
| `updated_at` | DateTime | Yes | No | Last modification |
| `created_by` | String (UUID) | Yes | No | Creator (self for registration) |
| `updated_by` | String (UUID) | Yes | No | Last modifier |

**Indexes**:
```
{ "email_hash": 1 }                    -- unique, login lookup
{ "role": 1, "status": 1 }            -- role-based queries
{ "organization_id": 1 }              -- org filtering
{ "guardian_id": 1 }                   -- guardian lookups
{ "status": 1, "locked_until": 1 }    -- lockout management
```

**Example Document**:
```json
{
  "_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "email": {
    "ciphertext": "U2FsdGVkX1+abc123...",
    "iv": "randomIV123...",
    "tag": "authTag456...",
    "key_id": "key-001-patient-a1b2"
  },
  "email_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
  "password_hash": "$2b$12$LJ3m4ks9fjKLs8dfj...",
  "role": "patient",
  "status": "active",
  "mfa_enabled": true,
  "mfa_secret": {
    "ciphertext": "encrypted_totp_secret...",
    "iv": "...",
    "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "failed_login_attempts": 0,
  "locked_until": null,
  "last_login": "2025-06-10T14:30:00Z",
  "organization_id": "org-0001-abcd-efgh-ijkl-mnop",
  "is_minor": false,
  "date_of_birth": {
    "ciphertext": "encrypted_dob...",
    "iv": "...",
    "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "date_of_birth_hash": "hash_of_1990-05-15",
  "guardian_id": null,
  "data_residency": {
    "region": "IN",
    "verified_at": "2025-06-01T00:00:00Z"
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-06-10T14:30:00Z",
  "created_by": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "updated_by": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
}
```

---

### 3.2 `patients`

**Purpose**: Extended patient profile with personal and health summary data linked to a user account.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `user_id` | String (UUID) | Yes | No | FK → users._id (1:1) |
| `full_name` | String | Yes | 🔐 | Patient full name |
| `phone_number` | String | Yes | 🔐 | Contact number |
| `address` | Object | Yes | 🔐 | Structured address |
| `identity_type` | String | Yes | No | `aadhaar`, `pan`, `passport`, `voter_id` |
| `identity_number` | String | Yes | 🔐 | Government ID number |
| `identity_number_hash` | String | Yes | No | SHA-256 for dedup |
| `blood_group` | String | No | 🔐 | Blood type |
| `emergency_contact` | Object | No | 🔐 | Name + phone of emergency contact |
| `allergies` | Array[Object] | No | 🔐 | List of known allergies |
| `chronic_conditions` | Array[String] | No | 🔐 | Ongoing conditions |
| `privacy_score` | Integer | Yes | No | Computed 0-100 score |
| `consent_defaults` | Object | Yes | No | Default consent preferences |
| `data_categories_stored` | Array[String] | Yes | No | List of stored categories |
| `retention_policy` | Object | Yes | No | Per-category retention dates |
| `redacted` | Boolean | Yes | No | Whether record is redacted |
| `redacted_at` | DateTime | No | No | Redaction timestamp |
| `redacted_by` | String (UUID) | No | No | Who authorized redaction |
| `redaction_reason` | String | No | No | Legal basis for redaction |
| `blockchain_ref` | String (UUID) | No | No | FK → blockchain_anchors._id |
| `data_residency` | Object | Yes | No | `{ region: "IN", verified_at: DateTime }` |
| `created_at` | DateTime | Yes | No | Record creation |
| `updated_at` | DateTime | Yes | No | Last update |
| `created_by` | String (UUID) | Yes | No | Creator |
| `updated_by` | String (UUID) | Yes | No | Last modifier |

**Indexes**:
```
{ "user_id": 1 }                       -- unique, user lookup
{ "identity_number_hash": 1 }          -- unique, dedup check
{ "redacted": 1 }                      -- filter active records
{ "organization_id": 1 }              -- org scoping (via user join)
{ "created_at": -1 }                   -- recent patients
```

**Example Document**:
```json
{
  "_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "user_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "full_name": {
    "ciphertext": "enc_Rajesh_Kumar...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "phone_number": {
    "ciphertext": "enc_+91-9876543210...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "address": {
    "ciphertext": "enc_address_object...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "identity_type": "aadhaar",
  "identity_number": {
    "ciphertext": "enc_aadhaar_number...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "identity_number_hash": "sha256_of_aadhaar",
  "blood_group": {
    "ciphertext": "enc_O+...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "emergency_contact": {
    "ciphertext": "enc_contact...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "allergies": {
    "ciphertext": "enc_allergies_array...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "chronic_conditions": {
    "ciphertext": "enc_conditions...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "privacy_score": 78,
  "consent_defaults": {
    "healthcare_treatment": "deny",
    "pharmacy_access": "deny",
    "research_access": "deny",
    "insurance_access": "deny",
    "analytics_access": "deny",
    "marketing_access": "deny"
  },
  "data_categories_stored": [
    "personal_info", "contact_info", "identity_info",
    "medical_history", "allergies", "prescriptions"
  ],
  "retention_policy": {
    "personal_info": "2033-01-15T00:00:00Z",
    "medical_history": "2033-01-15T00:00:00Z",
    "prescriptions": "2033-01-15T00:00:00Z"
  },
  "redacted": false,
  "redacted_at": null,
  "redacted_by": null,
  "redaction_reason": null,
  "blockchain_ref": "blk-9999-wxyz-1234",
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-06-10T14:30:00Z",
  "created_by": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "updated_by": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
}
```

---

### 3.3 `doctors`

**Purpose**: Extended profile for doctor users with specialization, license, and access configuration.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `user_id` | String (UUID) | Yes | No | FK → users._id (1:1) |
| `full_name` | String | Yes | 🔐 | Doctor full name |
| `license_number` | String | Yes | 🔐 | Medical license ID |
| `license_number_hash` | String | Yes | No | SHA-256 for lookup |
| `specialization` | String | Yes | No | Medical specialization |
| `department` | String | Yes | No | Hospital department |
| `qualification` | String | Yes | No | Degree/certification |
| `phone_number` | String | Yes | 🔐 | Contact number |
| `authorized_hours` | Object | Yes | No | `{ start: "08:00", end: "20:00" }` |
| `break_glass_count` | Integer | Yes | No | Total emergency accesses |
| `active_patients` | Array[String(UUID)] | No | No | Currently assigned patient IDs |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Record creation |
| `updated_at` | DateTime | Yes | No | Last update |
| `created_by` | String (UUID) | Yes | No | Creator |
| `updated_by` | String (UUID) | Yes | No | Last modifier |

**Indexes**:
```
{ "user_id": 1 }                       -- unique, user lookup
{ "license_number_hash": 1 }           -- unique, license dedup
{ "specialization": 1 }               -- specialty search
{ "department": 1 }                    -- department filtering
```

**Example Document**:
```json
{
  "_id": "doc-5678-abcd-efgh-ijkl-mnop",
  "user_id": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
  "full_name": {
    "ciphertext": "enc_Dr_Priya_Sharma...",
    "iv": "...", "tag": "...",
    "key_id": "key-002-doctor-b2c3"
  },
  "license_number": {
    "ciphertext": "enc_MCI-12345...",
    "iv": "...", "tag": "...",
    "key_id": "key-002-doctor-b2c3"
  },
  "license_number_hash": "sha256_of_MCI-12345",
  "specialization": "Cardiology",
  "department": "Cardiac Sciences",
  "qualification": "MD, DM Cardiology",
  "phone_number": {
    "ciphertext": "enc_phone...",
    "iv": "...", "tag": "...",
    "key_id": "key-002-doctor-b2c3"
  },
  "authorized_hours": { "start": "08:00", "end": "20:00" },
  "break_glass_count": 2,
  "active_patients": ["pat-1234-abcd-efgh-ijkl-mnop"],
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2024-06-01T09:00:00Z",
  "updated_at": "2025-06-10T11:00:00Z",
  "created_by": "admin-uuid-001",
  "updated_by": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e"
}
```

---

### 3.4 `pharmacy_staff`

**Purpose**: Extended profile for pharmacy personnel with license and dispensing authorization.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `user_id` | String (UUID) | Yes | No | FK → users._id (1:1) |
| `full_name` | String | Yes | 🔐 | Staff full name |
| `license_number` | String | Yes | 🔐 | Pharmacy license |
| `license_number_hash` | String | Yes | No | SHA-256 for lookup |
| `pharmacy_name` | String | Yes | No | Pharmacy unit name |
| `phone_number` | String | Yes | 🔐 | Contact number |
| `authorized_categories` | Array[String] | Yes | No | `["prescriptions", "allergies"]` |
| `dispensing_count` | Integer | Yes | No | Total dispensed medications |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Record creation |
| `updated_at` | DateTime | Yes | No | Last update |
| `created_by` | String (UUID) | Yes | No | Creator |
| `updated_by` | String (UUID) | Yes | No | Last modifier |

**Indexes**:
```
{ "user_id": 1 }                       -- unique, user lookup
{ "license_number_hash": 1 }           -- unique, license dedup
{ "pharmacy_name": 1 }                -- pharmacy unit queries
```

**Example Document**:
```json
{
  "_id": "pharm-9012-abcd-efgh-ijkl-mnop",
  "user_id": "c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
  "full_name": {
    "ciphertext": "enc_Amit_Patel...",
    "iv": "...", "tag": "...",
    "key_id": "key-003-pharm-c3d4"
  },
  "license_number": {
    "ciphertext": "enc_PH-67890...",
    "iv": "...", "tag": "...",
    "key_id": "key-003-pharm-c3d4"
  },
  "license_number_hash": "sha256_of_PH-67890",
  "pharmacy_name": "Central Pharmacy Unit A",
  "phone_number": {
    "ciphertext": "enc_phone...",
    "iv": "...", "tag": "...",
    "key_id": "key-003-pharm-c3d4"
  },
  "authorized_categories": ["prescriptions", "allergies"],
  "dispensing_count": 1547,
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2024-08-15T09:00:00Z",
  "updated_at": "2025-06-10T16:00:00Z",
  "created_by": "admin-uuid-001",
  "updated_by": "c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f"
}
```

---

### 3.5 `organizations`

**Purpose**: Healthcare organization (Data Fiduciary) registration and configuration.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `name` | String | Yes | No | Organization name |
| `registration_number` | String | Yes | No | Government registration ID |
| `type` | String (Enum) | Yes | No | `hospital`, `clinic`, `pharmacy_chain`, `lab` |
| `address` | Object | Yes | No | Registered address |
| `contact_email` | String | Yes | No | Official contact |
| `contact_phone` | String | Yes | No | Official phone |
| `dpo_user_id` | String (UUID) | No | No | FK → users._id (assigned DPO) |
| `admin_user_id` | String (UUID) | No | No | FK → users._id (primary admin) |
| `data_processing_purposes` | Array[String] | Yes | No | Authorized purposes |
| `dpdp_registration_date` | DateTime | Yes | No | DPDP compliance registration |
| `data_residency_region` | String | Yes | No | Always "IN" |
| `status` | String (Enum) | Yes | No | `active`, `suspended`, `deregistered` |
| `created_at` | DateTime | Yes | No | Registration date |
| `updated_at` | DateTime | Yes | No | Last update |

**Indexes**:
```
{ "registration_number": 1 }           -- unique
{ "type": 1, "status": 1 }            -- type filtering
{ "dpo_user_id": 1 }                  -- DPO lookup
```

**Example Document**:
```json
{
  "_id": "org-0001-abcd-efgh-ijkl-mnop",
  "name": "Apollo Healthcare Systems Pvt. Ltd.",
  "registration_number": "CIN-U85110TN2023PTC123456",
  "type": "hospital",
  "address": {
    "street": "21 Greams Lane",
    "city": "Chennai",
    "state": "Tamil Nadu",
    "pincode": "600006",
    "country": "India"
  },
  "contact_email": "dpo@apollohealthcare.in",
  "contact_phone": "+91-44-28290200",
  "dpo_user_id": "dpo-uuid-0001",
  "admin_user_id": "admin-uuid-001",
  "data_processing_purposes": [
    "healthcare_treatment", "pharmacy_access",
    "research_access", "insurance_access"
  ],
  "dpdp_registration_date": "2024-01-01T00:00:00Z",
  "data_residency_region": "IN",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2025-03-15T10:00:00Z"
}
```

---

## 4. Relationship Summary (Part 1 Collections)

```
organizations ─── (1:N) ──→ users
    │                          │
    │                          ├── (1:1) → patients
    │                          ├── (1:1) → doctors
    │                          └── (1:1) → pharmacy_staff
    │
    └── dpo_user_id ─── (N:1) ──→ users
    └── admin_user_id ── (N:1) ──→ users

users [Guardian] ── (1:N) ──→ users [Minor] (via guardian_id)
```

---

## 5. Indexing Strategy (Global Principles)

| Strategy | Rationale |
|----------|-----------|
| UUID as `_id` | Avoid ObjectId exposure, portable identifiers |
| Hash fields for encrypted lookups | Cannot query encrypted fields; store SHA-256 hash for equality checks |
| Compound indexes for common queries | Role + status, org + role, date ranges |
| TTL indexes for sessions | Auto-expire session documents |
| Sparse indexes for optional fields | Guardian_id (only minors), redacted_at (only redacted) |
| Text indexes | Audit log search, grievance description search |

---

*Part 1 complete. Remaining collections (consents, consent_receipts, healthcare_records, prescriptions, lab_reports, audit_logs, notifications, breach_incidents, grievance_requests, data_access_logs, integrity_verifications, blockchain_anchors, version_history) plus encryption strategy, retention strategy, redaction strategy, DPDP lifecycle mapping, scalability, and chameleon hash metadata storage will follow in subsequent parts.*


---

## 6. Collection Schemas (Part 2 — Clinical & Consent Data)

---

### 6.1 `consents`

**Purpose**: Records all consent decisions made by Data Principals, tracking purpose, scope, expiry, and blockchain proof for DPDP compliance.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id |
| `user_id` | String (UUID) | Yes | No | FK → users._id (Data Principal) |
| `consent_type` | String (Enum) | Yes | No | `healthcare_treatment`, `pharmacy_access`, `research_access`, `insurance_access`, `analytics_access`, `marketing_access` |
| `status` | String (Enum) | Yes | No | `active`, `withdrawn`, `expired`, `modified` |
| `purpose_description` | String | Yes | No | Human-readable purpose statement |
| `data_categories_in_scope` | Array[String] | Yes | No | Categories accessible under this consent |
| `processing_entity_id` | String (UUID) | No | No | FK → organizations._id or data_processors._id |
| `processing_entity_name` | String | Yes | No | Name of entity granted access |
| `granted_at` | DateTime | Yes | No | Consent grant timestamp |
| `expires_at` | DateTime | Yes | No | Consent expiry date |
| `withdrawn_at` | DateTime | No | No | Withdrawal timestamp (if withdrawn) |
| `withdrawal_reason` | String | No | No | Reason for withdrawal |
| `modified_at` | DateTime | No | No | Last modification timestamp |
| `previous_scope` | Array[String] | No | No | Scope before last modification |
| `modification_reason` | String | No | No | Reason for scope change |
| `guardian_consent` | Boolean | Yes | No | Whether consent given by guardian (minors) |
| `guardian_id` | String (UUID) | No | No | FK → users._id (if guardian provided consent) |
| `blockchain_tx_ref` | String | No | No | Blockchain transaction hash |
| `blockchain_anchor_id` | String (UUID) | No | No | FK → blockchain_anchors._id |
| `consent_hash` | String | Yes | No | SHA-256 hash of consent record for verification |
| `data_residency` | Object | Yes | No | `{ region: "IN", verified_at: DateTime }` |
| `created_at` | DateTime | Yes | No | Record creation |
| `updated_at` | DateTime | Yes | No | Last update |
| `created_by` | String (UUID) | Yes | No | Creator (patient or guardian) |
| `updated_by` | String (UUID) | Yes | No | Last modifier |

**Indexes**:
```
{ "patient_id": 1, "consent_type": 1 }          -- patient consent lookup
{ "user_id": 1, "status": 1 }                   -- active consents per user
{ "status": 1, "expires_at": 1 }                -- expiry monitoring
{ "processing_entity_id": 1, "status": 1 }      -- processor access check
{ "consent_type": 1, "status": 1 }              -- type-based filtering
{ "expires_at": 1 }                              -- TTL-like expiry jobs
{ "guardian_id": 1 }                             -- guardian consent lookup
```

**Relationships**:
- `patient_id` → `patients._id` (N:1)
- `user_id` → `users._id` (N:1)
- `processing_entity_id` → `organizations._id` or `data_processors._id` (N:1)
- `guardian_id` → `users._id` (N:1, optional for minors)
- `blockchain_anchor_id` → `blockchain_anchors._id` (N:1)
- One patient can have multiple consents (one per type per entity)
- Each consent generates one or more `consent_receipts`

**Encryption Strategy**: Consent records are NOT field-level encrypted because they contain no sensitive personal data — only references (UUIDs), types, and dates. The `consent_hash` provides integrity verification against the blockchain.

**Example Document**:
```json
{
  "_id": "con-1001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "user_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "consent_type": "healthcare_treatment",
  "status": "active",
  "purpose_description": "Access to medical records for diagnosis and treatment by authorized doctors at Apollo Healthcare",
  "data_categories_in_scope": [
    "medical_history", "allergies", "prescriptions", "lab_reports"
  ],
  "processing_entity_id": "org-0001-abcd-efgh-ijkl-mnop",
  "processing_entity_name": "Apollo Healthcare Systems Pvt. Ltd.",
  "granted_at": "2025-02-01T10:00:00Z",
  "expires_at": "2026-02-01T10:00:00Z",
  "withdrawn_at": null,
  "withdrawal_reason": null,
  "modified_at": null,
  "previous_scope": null,
  "modification_reason": null,
  "guardian_consent": false,
  "guardian_id": null,
  "blockchain_tx_ref": "0xabc123def456789...",
  "blockchain_anchor_id": "blk-2001-wxyz-1234",
  "consent_hash": "sha256_of_consent_record_content",
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-02-01T10:00:00Z",
  "updated_at": "2025-02-01T10:00:00Z",
  "created_by": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "updated_by": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
}
```

---

### 6.2 `consent_receipts`

**Purpose**: Verifiable proof document for every consent action (grant, modify, withdraw) with blockchain anchoring and downloadable receipt generation.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Consent Receipt ID |
| `consent_id` | String (UUID) | Yes | No | FK → consents._id |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id |
| `user_id` | String (UUID) | Yes | No | FK → users._id |
| `action_type` | String (Enum) | Yes | No | `grant`, `modify`, `withdraw` |
| `consent_type` | String (Enum) | Yes | No | Consent category |
| `purpose_description` | String | Yes | No | Purpose at time of action |
| `data_categories` | Array[String] | Yes | No | Categories in scope at action time |
| `scope_before` | Array[String] | No | No | Previous scope (for modify/withdraw) |
| `scope_after` | Array[String] | No | No | New scope (for modify) |
| `expiry_date` | DateTime | Yes | No | Consent expiry at time of receipt |
| `processing_entity_name` | String | Yes | No | Entity name |
| `blockchain_tx_ref` | String | Yes | No | On-chain transaction hash |
| `blockchain_anchor_id` | String (UUID) | Yes | No | FK → blockchain_anchors._id |
| `receipt_hash` | String | Yes | No | SHA-256 hash of receipt content |
| `qr_code_data` | String | Yes | No | QR payload linking to blockchain tx |
| `pdf_generated` | Boolean | Yes | No | Whether PDF was generated |
| `pdf_storage_ref` | String | No | No | Reference to stored PDF (if generated) |
| `issued_at` | DateTime | Yes | No | Receipt issuance timestamp |
| `data_residency` | Object | Yes | No | Residency metadata |

**Indexes**:
```
{ "consent_id": 1 }                    -- receipts per consent
{ "patient_id": 1, "issued_at": -1 }  -- patient receipt history
{ "user_id": 1, "action_type": 1 }    -- user action filtering
{ "blockchain_tx_ref": 1 }            -- blockchain lookup
{ "issued_at": -1 }                    -- chronological listing
```

**Relationships**:
- `consent_id` → `consents._id` (N:1) — multiple receipts per consent lifecycle
- `patient_id` → `patients._id` (N:1)
- `blockchain_anchor_id` → `blockchain_anchors._id` (N:1)

**Encryption Strategy**: Not encrypted. Contains only references, action types, and timestamps. No PII stored directly.

**Example Document**:
```json
{
  "_id": "rcpt-3001-abcd-efgh-ijkl-mnop",
  "consent_id": "con-1001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "user_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "action_type": "grant",
  "consent_type": "healthcare_treatment",
  "purpose_description": "Access to medical records for diagnosis and treatment by authorized doctors at Apollo Healthcare",
  "data_categories": ["medical_history", "allergies", "prescriptions", "lab_reports"],
  "scope_before": null,
  "scope_after": null,
  "expiry_date": "2026-02-01T10:00:00Z",
  "processing_entity_name": "Apollo Healthcare Systems Pvt. Ltd.",
  "blockchain_tx_ref": "0xabc123def456789...",
  "blockchain_anchor_id": "blk-2001-wxyz-1234",
  "receipt_hash": "sha256_of_receipt_content",
  "qr_code_data": "https://verify.platform.in/tx/0xabc123def456789",
  "pdf_generated": true,
  "pdf_storage_ref": "receipts/rcpt-3001-abcd-efgh-ijkl-mnop.pdf",
  "issued_at": "2025-02-01T10:00:05Z",
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" }
}
```

---

### 6.3 `healthcare_records`

**Purpose**: Stores clinical records including consultations, diagnoses, treatment plans, and doctor notes. All clinical content is encrypted at field level.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id |
| `doctor_id` | String (UUID) | Yes | No | FK → doctors._id (creating doctor) |
| `record_type` | String (Enum) | Yes | No | `consultation`, `diagnosis`, `treatment_plan`, `follow_up`, `discharge_summary` |
| `title` | String | Yes | 🔐 | Record title/summary |
| `description` | String | Yes | 🔐 | Detailed clinical notes |
| `diagnosis_codes` | Array[String] | No | 🔐 | ICD-10 codes |
| `symptoms` | Array[String] | No | 🔐 | Reported symptoms |
| `treatment_notes` | String | No | 🔐 | Treatment details |
| `follow_up_date` | DateTime | No | No | Next appointment (if applicable) |
| `attachments` | Array[Object] | No | 🔐 | `[{ file_ref, file_type, file_name }]` |
| `consent_verified` | Boolean | Yes | No | Whether consent was verified at access |
| `consent_id` | String (UUID) | No | No | FK → consents._id (consent used) |
| `break_glass_access` | Boolean | Yes | No | Created under emergency access |
| `break_glass_justification` | String | No | No | Emergency justification text |
| `verification_hash` | String | Yes | No | SHA-256 of record content |
| `blockchain_tx_ref` | String | No | No | On-chain transaction hash |
| `blockchain_anchor_id` | String (UUID) | No | No | FK → blockchain_anchors._id |
| `version` | Integer | Yes | No | Document version number |
| `redacted` | Boolean | Yes | No | Whether record is redacted |
| `redacted_at` | DateTime | No | No | Redaction timestamp |
| `redacted_by` | String (UUID) | No | No | Authorizing actor |
| `redaction_reason` | String | No | No | Legal basis |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Record creation |
| `updated_at` | DateTime | Yes | No | Last update |
| `created_by` | String (UUID) | Yes | No | Creating doctor |
| `updated_by` | String (UUID) | Yes | No | Last modifier |

**Indexes**:
```
{ "patient_id": 1, "created_at": -1 }           -- patient record history
{ "doctor_id": 1, "created_at": -1 }            -- doctor's records
{ "record_type": 1, "patient_id": 1 }           -- type-based patient filter
{ "redacted": 1 }                                -- active record filter
{ "verification_hash": 1 }                      -- integrity lookups
{ "blockchain_tx_ref": 1 }                      -- blockchain verification
{ "break_glass_access": 1 }                     -- emergency record audit
```

**Relationships**:
- `patient_id` → `patients._id` (N:1)
- `doctor_id` → `doctors._id` (N:1)
- `consent_id` → `consents._id` (N:1)
- `blockchain_anchor_id` → `blockchain_anchors._id` (N:1)
- Referenced by `version_history` for change tracking

**Encryption Strategy**: All clinical content fields (title, description, diagnosis_codes, symptoms, treatment_notes, attachments) are encrypted using the patient's unique AES-256-GCM key. The `verification_hash` is computed from the plaintext before encryption for integrity verification.

**Example Document**:
```json
{
  "_id": "hr-4001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "doctor_id": "doc-5678-abcd-efgh-ijkl-mnop",
  "record_type": "consultation",
  "title": {
    "ciphertext": "enc_Cardiology_Consultation_June_2025...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "description": {
    "ciphertext": "enc_Patient_presents_with_chest_pain...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "diagnosis_codes": {
    "ciphertext": "enc_[I25.1, R07.9]...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "symptoms": {
    "ciphertext": "enc_[chest_pain, shortness_of_breath]...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "treatment_notes": {
    "ciphertext": "enc_Prescribed_Aspirin_75mg...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "follow_up_date": "2025-07-10T10:00:00Z",
  "attachments": {
    "ciphertext": "enc_attachments_array...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "consent_verified": true,
  "consent_id": "con-1001-abcd-efgh-ijkl-mnop",
  "break_glass_access": false,
  "break_glass_justification": null,
  "verification_hash": "sha256_of_plaintext_record_content",
  "blockchain_tx_ref": "0xdef456abc789012...",
  "blockchain_anchor_id": "blk-4001-wxyz-5678",
  "version": 1,
  "redacted": false,
  "redacted_at": null,
  "redacted_by": null,
  "redaction_reason": null,
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T11:30:00Z",
  "updated_at": "2025-06-10T11:30:00Z",
  "created_by": "doc-5678-abcd-efgh-ijkl-mnop",
  "updated_by": "doc-5678-abcd-efgh-ijkl-mnop"
}
```

---

### 6.4 `prescriptions`

**Purpose**: Stores medication prescriptions issued by doctors and tracks dispensing status by pharmacy staff. Accessible to both healthcare_treatment and pharmacy_access consent holders.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id |
| `doctor_id` | String (UUID) | Yes | No | FK → doctors._id (prescribing doctor) |
| `healthcare_record_id` | String (UUID) | No | No | FK → healthcare_records._id (linked consultation) |
| `prescription_date` | DateTime | Yes | No | Date prescribed |
| `medications` | Array[Object] | Yes | 🔐 | Medication details array |
| `diagnosis_summary` | String | Yes | 🔐 | Brief diagnosis context |
| `instructions` | String | No | 🔐 | Special instructions |
| `duration_days` | Integer | Yes | No | Treatment duration |
| `refill_allowed` | Boolean | Yes | No | Whether refills permitted |
| `refill_count` | Integer | Yes | No | Max refill count |
| `refills_used` | Integer | Yes | No | Refills consumed |
| `status` | String (Enum) | Yes | No | `active`, `dispensed`, `partially_dispensed`, `expired`, `cancelled` |
| `dispensed_by` | String (UUID) | No | No | FK → pharmacy_staff._id |
| `dispensed_at` | DateTime | No | No | Dispensing timestamp |
| `dispensing_notes` | String | No | 🔐 | Pharmacy staff notes |
| `consent_verified` | Boolean | Yes | No | Consent check status |
| `consent_id` | String (UUID) | No | No | FK → consents._id |
| `verification_hash` | String | Yes | No | SHA-256 of prescription content |
| `blockchain_tx_ref` | String | No | No | On-chain tx hash |
| `blockchain_anchor_id` | String (UUID) | No | No | FK → blockchain_anchors._id |
| `version` | Integer | Yes | No | Document version |
| `redacted` | Boolean | Yes | No | Redaction flag |
| `redacted_at` | DateTime | No | No | Redaction timestamp |
| `redacted_by` | String (UUID) | No | No | Redaction authorizer |
| `redaction_reason` | String | No | No | Legal basis |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Creation timestamp |
| `updated_at` | DateTime | Yes | No | Last update |
| `created_by` | String (UUID) | Yes | No | Prescribing doctor |
| `updated_by` | String (UUID) | Yes | No | Last modifier |

**Medications Array Structure** (encrypted as single blob):
```json
[
  {
    "name": "Aspirin",
    "dosage": "75mg",
    "frequency": "Once daily",
    "route": "Oral",
    "duration_days": 30,
    "quantity": 30,
    "notes": "Take after breakfast"
  }
]
```

**Indexes**:
```
{ "patient_id": 1, "status": 1, "created_at": -1 }    -- patient active prescriptions
{ "doctor_id": 1, "created_at": -1 }                   -- doctor's prescriptions
{ "dispensed_by": 1, "dispensed_at": -1 }              -- pharmacy staff history
{ "status": 1, "prescription_date": -1 }               -- status filtering
{ "redacted": 1 }                                       -- active record filter
{ "healthcare_record_id": 1 }                          -- consultation linkage
{ "verification_hash": 1 }                             -- integrity check
```

**Relationships**:
- `patient_id` → `patients._id` (N:1)
- `doctor_id` → `doctors._id` (N:1)
- `healthcare_record_id` → `healthcare_records._id` (N:1, optional)
- `dispensed_by` → `pharmacy_staff._id` (N:1, optional)
- `consent_id` → `consents._id` (N:1)
- `blockchain_anchor_id` → `blockchain_anchors._id` (N:1)

**Encryption Strategy**: Medication details, diagnosis summary, instructions, and dispensing notes are encrypted using the patient's AES-256-GCM key. Status, dates, and reference IDs remain unencrypted for query operations.

**Example Document**:
```json
{
  "_id": "rx-5001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "doctor_id": "doc-5678-abcd-efgh-ijkl-mnop",
  "healthcare_record_id": "hr-4001-abcd-efgh-ijkl-mnop",
  "prescription_date": "2025-06-10T11:45:00Z",
  "medications": {
    "ciphertext": "enc_medications_array...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "diagnosis_summary": {
    "ciphertext": "enc_Chronic_ischemic_heart_disease...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "instructions": {
    "ciphertext": "enc_Take_with_food...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "duration_days": 30,
  "refill_allowed": true,
  "refill_count": 3,
  "refills_used": 0,
  "status": "dispensed",
  "dispensed_by": "pharm-9012-abcd-efgh-ijkl-mnop",
  "dispensed_at": "2025-06-10T15:30:00Z",
  "dispensing_notes": {
    "ciphertext": "enc_All_medications_dispensed...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "consent_verified": true,
  "consent_id": "con-1002-pharmacy-consent",
  "verification_hash": "sha256_of_prescription_plaintext",
  "blockchain_tx_ref": "0x789abc012def345...",
  "blockchain_anchor_id": "blk-5001-wxyz-9012",
  "version": 2,
  "redacted": false,
  "redacted_at": null,
  "redacted_by": null,
  "redaction_reason": null,
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T11:45:00Z",
  "updated_at": "2025-06-10T15:30:00Z",
  "created_by": "doc-5678-abcd-efgh-ijkl-mnop",
  "updated_by": "pharm-9012-abcd-efgh-ijkl-mnop"
}
```

---

### 6.5 `lab_reports`

**Purpose**: Stores laboratory test results including blood work, imaging reports, and diagnostic test outcomes. Linked to ordering doctor and patient records.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id |
| `ordered_by` | String (UUID) | Yes | No | FK → doctors._id (ordering doctor) |
| `healthcare_record_id` | String (UUID) | No | No | FK → healthcare_records._id (linked consultation) |
| `lab_name` | String | Yes | No | Laboratory/facility name |
| `test_type` | String (Enum) | Yes | No | `blood_work`, `imaging`, `pathology`, `microbiology`, `biochemistry`, `other` |
| `test_name` | String | Yes | 🔐 | Specific test name |
| `test_date` | DateTime | Yes | No | Date test performed |
| `report_date` | DateTime | Yes | No | Date report issued |
| `results` | Object | Yes | 🔐 | Structured test results |
| `result_summary` | String | Yes | 🔐 | Doctor-readable summary |
| `normal_ranges` | Object | No | No | Reference ranges (non-sensitive) |
| `abnormal_flags` | Array[String] | No | 🔐 | Flagged abnormal values |
| `interpretation` | String | No | 🔐 | Pathologist/radiologist interpretation |
| `attachments` | Array[Object] | No | 🔐 | Scanned reports, images |
| `status` | String (Enum) | Yes | No | `pending`, `completed`, `reviewed`, `cancelled` |
| `reviewed_by` | String (UUID) | No | No | FK → doctors._id (reviewing doctor) |
| `reviewed_at` | DateTime | No | No | Review timestamp |
| `consent_verified` | Boolean | Yes | No | Consent check status |
| `consent_id` | String (UUID) | No | No | FK → consents._id |
| `verification_hash` | String | Yes | No | SHA-256 of report content |
| `blockchain_tx_ref` | String | No | No | On-chain tx hash |
| `blockchain_anchor_id` | String (UUID) | No | No | FK → blockchain_anchors._id |
| `version` | Integer | Yes | No | Document version |
| `redacted` | Boolean | Yes | No | Redaction flag |
| `redacted_at` | DateTime | No | No | Redaction timestamp |
| `redacted_by` | String (UUID) | No | No | Redaction authorizer |
| `redaction_reason` | String | No | No | Legal basis |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Creation timestamp |
| `updated_at` | DateTime | Yes | No | Last update |
| `created_by` | String (UUID) | Yes | No | Creator |
| `updated_by` | String (UUID) | Yes | No | Last modifier |

**Results Object Structure** (encrypted as single blob):
```json
{
  "parameters": [
    {
      "name": "Hemoglobin",
      "value": "14.2",
      "unit": "g/dL",
      "normal_range": "13.5-17.5",
      "flag": "normal"
    },
    {
      "name": "WBC Count",
      "value": "11500",
      "unit": "cells/μL",
      "normal_range": "4000-11000",
      "flag": "high"
    }
  ]
}
```

**Indexes**:
```
{ "patient_id": 1, "test_date": -1 }              -- patient lab history
{ "ordered_by": 1, "created_at": -1 }             -- doctor's ordered tests
{ "test_type": 1, "patient_id": 1 }               -- type-based filtering
{ "status": 1, "report_date": -1 }                -- pending reports
{ "redacted": 1 }                                   -- active records
{ "healthcare_record_id": 1 }                      -- consultation linkage
{ "verification_hash": 1 }                         -- integrity check
```

**Relationships**:
- `patient_id` → `patients._id` (N:1)
- `ordered_by` → `doctors._id` (N:1)
- `reviewed_by` → `doctors._id` (N:1, optional)
- `healthcare_record_id` → `healthcare_records._id` (N:1, optional)
- `consent_id` → `consents._id` (N:1)
- `blockchain_anchor_id` → `blockchain_anchors._id` (N:1)

**Encryption Strategy**: All clinical result data (test_name, results, result_summary, abnormal_flags, interpretation, attachments) encrypted with patient's key. Metadata fields (test_type, dates, status, lab_name) remain unencrypted for querying.

**Example Document**:
```json
{
  "_id": "lab-6001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "ordered_by": "doc-5678-abcd-efgh-ijkl-mnop",
  "healthcare_record_id": "hr-4001-abcd-efgh-ijkl-mnop",
  "lab_name": "Apollo Diagnostics Chennai",
  "test_type": "blood_work",
  "test_name": {
    "ciphertext": "enc_Complete_Blood_Count...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "test_date": "2025-06-10T08:00:00Z",
  "report_date": "2025-06-10T14:00:00Z",
  "results": {
    "ciphertext": "enc_results_object...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "result_summary": {
    "ciphertext": "enc_Mildly_elevated_WBC...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "normal_ranges": {
    "hemoglobin": "13.5-17.5 g/dL",
    "wbc": "4000-11000 cells/μL",
    "platelets": "150000-400000 cells/μL"
  },
  "abnormal_flags": {
    "ciphertext": "enc_[elevated_wbc]...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "interpretation": {
    "ciphertext": "enc_Mild_leukocytosis...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "attachments": {
    "ciphertext": "enc_attachments...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "status": "reviewed",
  "reviewed_by": "doc-5678-abcd-efgh-ijkl-mnop",
  "reviewed_at": "2025-06-10T16:00:00Z",
  "consent_verified": true,
  "consent_id": "con-1001-abcd-efgh-ijkl-mnop",
  "verification_hash": "sha256_of_lab_report_plaintext",
  "blockchain_tx_ref": "0x012345def678abc...",
  "blockchain_anchor_id": "blk-6001-wxyz-3456",
  "version": 1,
  "redacted": false,
  "redacted_at": null,
  "redacted_by": null,
  "redaction_reason": null,
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T14:00:00Z",
  "updated_at": "2025-06-10T16:00:00Z",
  "created_by": "lab-system-uuid",
  "updated_by": "doc-5678-abcd-efgh-ijkl-mnop"
}
```

---

*Part 2 complete. Part 3 will cover: audit_logs, notifications, breach_incidents, grievance_requests, data_access_logs, integrity_verifications, blockchain_anchors, version_history, plus the cross-cutting design sections (encryption strategy, retention strategy, redaction strategy, DPDP lifecycle mapping, scalability, chameleon hash metadata).*


---

## 7. Collection Schemas (Part 3 — Audit, Verification & Blockchain)

---

### 7.1 `audit_logs`

**Purpose**: Immutable record of every data operation in the system. Every create, read, update, delete, consent change, breach event, and emergency access generates an audit entry. Blockchain-anchored for tamper evidence.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `actor_id` | String (UUID) | Yes | No | FK → users._id (who performed action) |
| `actor_role` | String (Enum) | Yes | No | Role at time of action |
| `actor_name_hash` | String | Yes | No | SHA-256 of actor name (for search without decryption) |
| `action_type` | String (Enum) | Yes | No | `create`, `read`, `update`, `delete`, `consent_grant`, `consent_withdraw`, `consent_modify`, `login`, `logout`, `break_glass`, `breach_detected`, `redaction`, `key_rotation`, `grievance`, `export`, `verification` |
| `action_category` | String (Enum) | Yes | No | `data_operation`, `auth_event`, `consent_event`, `security_event`, `compliance_event`, `system_event` |
| `severity` | String (Enum) | Yes | No | `info`, `warning`, `critical` |
| `resource_type` | String | Yes | No | Collection/entity affected (e.g., `healthcare_records`, `consents`) |
| `resource_id` | String (UUID) | Yes | No | ID of affected document |
| `patient_id` | String (UUID) | No | No | FK → patients._id (affected patient, if applicable) |
| `reason` | String | Yes | No | Stated reason or system-generated purpose |
| `details` | Object | Yes | No | Action-specific metadata |
| `affected_fields` | Array[String] | No | No | List of modified field names |
| `previous_value_hash` | String | No | No | SHA-256 of previous value (for updates) |
| `new_value_hash` | String | No | No | SHA-256 of new value (for updates) |
| `source_ip` | String | Yes | No | Request origin IP address |
| `user_agent` | String | No | No | Client user agent string |
| `session_id_hash` | String | No | No | SHA-256 of session ID |
| `request_id` | String (UUID) | Yes | No | Correlation ID for request tracing |
| `duration_ms` | Integer | No | No | Operation duration in milliseconds |
| `consent_reference` | String (UUID) | No | No | FK → consents._id (consent authorizing this access) |
| `log_hash` | String | Yes | No | SHA-256 hash of this log entry for integrity |
| `previous_log_hash` | String | No | No | Hash of preceding log (chain linking) |
| `blockchain_tx_ref` | String | No | No | On-chain transaction hash |
| `blockchain_anchor_id` | String (UUID) | No | No | FK → blockchain_anchors._id |
| `tampered` | Boolean | Yes | No | Integrity violation flag |
| `tamper_detected_at` | DateTime | No | No | When tampering was detected |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Log creation timestamp (immutable) |

**Indexes**:
```
{ "actor_id": 1, "created_at": -1 }                    -- actor history
{ "patient_id": 1, "created_at": -1 }                  -- patient audit trail
{ "action_type": 1, "created_at": -1 }                 -- action filtering
{ "action_category": 1, "severity": 1, "created_at": -1 } -- category + severity
{ "resource_type": 1, "resource_id": 1 }               -- resource audit
{ "severity": 1, "created_at": -1 }                    -- critical event monitoring
{ "blockchain_tx_ref": 1 }                              -- blockchain lookup
{ "log_hash": 1 }                                       -- integrity verification
{ "tampered": 1 }                                       -- compromised entries
{ "request_id": 1 }                                     -- request correlation
{ "created_at": -1 }                                    -- chronological (TTL: 8 years)
```

**Immutability Design**:
- Audit logs are **append-only**. No update or delete operations permitted.
- `log_hash` = SHA-256(actor_id + action_type + resource_id + patient_id + reason + created_at + previous_log_hash)
- `previous_log_hash` creates a hash chain within the collection for sequential integrity verification
- If `tampered` flag is set, the Integrity_Verifier detected a discrepancy

**Retention**: 8 years minimum (healthcare compliance). No TTL index — archival strategy moves old logs to cold storage after 2 years while maintaining blockchain references.

**Example Document**:
```json
{
  "_id": "aud-7001-abcd-efgh-ijkl-mnop",
  "actor_id": "doc-5678-abcd-efgh-ijkl-mnop",
  "actor_role": "doctor",
  "actor_name_hash": "sha256_of_Dr_Priya_Sharma",
  "action_type": "read",
  "action_category": "data_operation",
  "severity": "info",
  "resource_type": "healthcare_records",
  "resource_id": "hr-4001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "reason": "Patient consultation - reviewing medical history",
  "details": {
    "data_categories_accessed": ["medical_history", "allergies"],
    "access_duration_seconds": 180
  },
  "affected_fields": null,
  "previous_value_hash": null,
  "new_value_hash": null,
  "source_ip": "192.168.1.45",
  "user_agent": "Mozilla/5.0 Chrome/125.0",
  "session_id_hash": "sha256_of_session_token",
  "request_id": "req-8001-correlation-uuid",
  "duration_ms": 245,
  "consent_reference": "con-1001-abcd-efgh-ijkl-mnop",
  "log_hash": "sha256_of_this_log_entry",
  "previous_log_hash": "sha256_of_previous_log_entry",
  "blockchain_tx_ref": "0xaaa111bbb222ccc333...",
  "blockchain_anchor_id": "blk-7001-wxyz-0001",
  "tampered": false,
  "tamper_detected_at": null,
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T11:30:00Z"
}
```

---

### 7.2 `data_access_logs`

**Purpose**: Patient-facing access transparency log showing who accessed their data, when, why, and what category. Feeds the Data Usage Timeline UI. Derived from audit_logs but structured for patient consumption.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id (data subject) |
| `accessor_id` | String (UUID) | Yes | No | FK → users._id (who accessed) |
| `accessor_role` | String (Enum) | Yes | No | Role of accessor |
| `accessor_name` | String | Yes | No | Display name (non-encrypted for timeline display) |
| `accessor_organization` | String | No | No | Organization name |
| `access_type` | String (Enum) | Yes | No | `view`, `download`, `modify`, `emergency_access`, `processor_access` |
| `data_categories` | Array[String] | Yes | No | Categories accessed |
| `purpose` | String | Yes | No | Stated reason for access |
| `consent_id` | String (UUID) | No | No | FK → consents._id (authorizing consent) |
| `access_start` | DateTime | Yes | No | Access session start |
| `access_end` | DateTime | No | No | Access session end |
| `duration_seconds` | Integer | No | No | Computed access duration |
| `break_glass` | Boolean | Yes | No | Emergency access flag |
| `processor_id` | String (UUID) | No | No | FK → data_processors._id (if processor) |
| `audit_log_id` | String (UUID) | Yes | No | FK → audit_logs._id (source audit entry) |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Log creation |

**Indexes**:
```
{ "patient_id": 1, "created_at": -1 }            -- patient timeline (primary query)
{ "patient_id": 1, "accessor_role": 1 }          -- filter by accessor role
{ "patient_id": 1, "data_categories": 1 }        -- filter by category
{ "patient_id": 1, "access_type": 1 }            -- filter by access type
{ "accessor_id": 1, "created_at": -1 }           -- accessor's access history
{ "break_glass": 1, "created_at": -1 }           -- emergency access audit
{ "processor_id": 1, "created_at": -1 }          -- processor access tracking
```

**Relationship to audit_logs**: Each `data_access_logs` entry is derived from one or more `audit_logs` entries. The `audit_log_id` provides traceability back to the immutable source.

**Example Document**:
```json
{
  "_id": "dal-8001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "accessor_id": "doc-5678-abcd-efgh-ijkl-mnop",
  "accessor_role": "doctor",
  "accessor_name": "Dr. Priya Sharma",
  "accessor_organization": "Apollo Healthcare Systems Pvt. Ltd.",
  "access_type": "view",
  "data_categories": ["medical_history", "allergies"],
  "purpose": "Cardiology consultation - reviewing patient history",
  "consent_id": "con-1001-abcd-efgh-ijkl-mnop",
  "access_start": "2025-06-10T11:30:00Z",
  "access_end": "2025-06-10T11:33:00Z",
  "duration_seconds": 180,
  "break_glass": false,
  "processor_id": null,
  "audit_log_id": "aud-7001-abcd-efgh-ijkl-mnop",
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T11:33:00Z"
}
```

---

### 7.3 `integrity_verifications`

**Purpose**: Records every integrity verification operation — whether initiated by patient (on-demand), system (scheduled batch), or DPO (compliance audit). Stores comparison results.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id |
| `initiated_by` | String (UUID) | Yes | No | FK → users._id (requestor) |
| `initiated_by_role` | String (Enum) | Yes | No | Role of requestor |
| `verification_type` | String (Enum) | Yes | No | `single_record`, `batch_all`, `scheduled`, `dpo_audit` |
| `resource_type` | String | Yes | No | Collection verified |
| `resource_id` | String (UUID) | No | No | Specific record (null for batch) |
| `records_verified` | Integer | Yes | No | Count of records checked |
| `records_passed` | Integer | Yes | No | Count with matching hashes |
| `records_failed` | Integer | Yes | No | Count with mismatched hashes |
| `failed_records` | Array[Object] | No | No | `[{ resource_id, expected_hash, computed_hash }]` |
| `overall_status` | String (Enum) | Yes | No | `verified`, `integrity_violation`, `partial_failure` |
| `current_hash` | String | No | No | Computed hash of current record state |
| `blockchain_hash` | String | No | No | Hash stored on blockchain |
| `blockchain_tx_ref` | String | No | No | Source blockchain transaction |
| `block_number` | Integer | No | No | Ethereum block number |
| `verification_duration_ms` | Integer | Yes | No | Time taken for verification |
| `dpo_notified` | Boolean | Yes | No | Whether DPO was alerted (on failure) |
| `patient_notified` | Boolean | Yes | No | Whether patient was notified (on failure) |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Verification timestamp |

**Indexes**:
```
{ "patient_id": 1, "created_at": -1 }              -- patient verification history
{ "overall_status": 1, "created_at": -1 }          -- failure monitoring
{ "verification_type": 1, "created_at": -1 }       -- type filtering
{ "initiated_by": 1 }                               -- requestor lookup
{ "resource_type": 1, "resource_id": 1 }           -- record-level lookup
```

**Example Document**:
```json
{
  "_id": "iv-9001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "initiated_by": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "initiated_by_role": "patient",
  "verification_type": "batch_all",
  "resource_type": "all",
  "resource_id": null,
  "records_verified": 12,
  "records_passed": 12,
  "records_failed": 0,
  "failed_records": [],
  "overall_status": "verified",
  "current_hash": null,
  "blockchain_hash": null,
  "blockchain_tx_ref": null,
  "block_number": null,
  "verification_duration_ms": 3420,
  "dpo_notified": false,
  "patient_notified": false,
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T18:00:00Z"
}
```

---

### 7.4 `blockchain_anchors`

**Purpose**: Central registry of all blockchain transactions made by the system. Links off-chain records to on-chain proofs. Serves as the lookup table for integrity verification.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `anchor_type` | String (Enum) | Yes | No | `consent`, `audit_log`, `record_verification`, `consent_receipt`, `redaction_proof`, `version_anchor`, `breach_trail`, `grievance_resolution`, `processor_authorization` |
| `resource_type` | String | Yes | No | Source collection name |
| `resource_id` | String (UUID) | Yes | No | Source document ID |
| `patient_id` | String (UUID) | No | No | FK → patients._id (if patient-related) |
| `data_hash` | String | Yes | No | SHA-256 hash stored on-chain |
| `hash_algorithm` | String | Yes | No | Always `sha256` |
| `smart_contract` | String (Enum) | Yes | No | `ConsentContract`, `VerificationContract`, `AuditContract` |
| `contract_function` | String | Yes | No | Function called (e.g., `storeConsent`, `storeHash`) |
| `transaction_hash` | String | Yes | No | Ethereum transaction hash |
| `block_number` | Integer | Yes | No | Block in which tx was mined |
| `block_timestamp` | DateTime | Yes | No | Block timestamp |
| `gas_used` | Integer | Yes | No | Gas consumed |
| `transaction_status` | String (Enum) | Yes | No | `success`, `failed`, `pending` |
| `retry_count` | Integer | Yes | No | Number of retry attempts |
| `chameleon_hash_ref` | String (UUID) | No | No | FK → chameleon_hash_records._id (if redaction-related) |
| `previous_anchor_id` | String (UUID) | No | No | FK → blockchain_anchors._id (chain linking for same resource) |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Anchor creation timestamp |

**Indexes**:
```
{ "transaction_hash": 1 }                           -- unique, tx lookup
{ "resource_type": 1, "resource_id": 1 }           -- resource → blockchain mapping
{ "patient_id": 1, "anchor_type": 1 }             -- patient blockchain history
{ "anchor_type": 1, "created_at": -1 }            -- type-based listing
{ "smart_contract": 1, "block_number": -1 }       -- contract activity
{ "transaction_status": 1 }                         -- pending/failed monitoring
{ "block_number": -1 }                              -- chronological by block
{ "data_hash": 1 }                                  -- hash lookup for verification
```

**Blockchain Anchoring Strategy**:

1. **What gets anchored**: Consent events, audit log entries, record verification hashes, consent receipts, redaction proofs, version entries, breach trails, grievance resolutions, processor authorizations
2. **SLA**: All anchoring completes within 10 seconds of the triggering event
3. **Hash computation**: SHA-256 of the canonical JSON representation of the source document (sorted keys, no whitespace)
4. **Contract routing**: 
   - Consent events → `ConsentContract.storeConsent()`
   - Record hashes → `VerificationContract.storeHash()`
   - Audit hashes → `AuditContract.storeAuditHash()`
5. **Retry logic**: If transaction fails, retry up to 3 times with exponential backoff (2s, 4s, 8s)
6. **Chain linking**: `previous_anchor_id` links successive anchors for the same resource, creating a verifiable modification chain

**Example Document**:
```json
{
  "_id": "blk-2001-wxyz-1234",
  "anchor_type": "consent",
  "resource_type": "consents",
  "resource_id": "con-1001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "data_hash": "a3f2b1c4d5e6f7890123456789abcdef0123456789abcdef0123456789abcdef",
  "hash_algorithm": "sha256",
  "smart_contract": "ConsentContract",
  "contract_function": "storeConsent",
  "transaction_hash": "0xabc123def456789012345678901234567890123456789012345678901234abcd",
  "block_number": 1547,
  "block_timestamp": "2025-02-01T10:00:03Z",
  "gas_used": 45000,
  "transaction_status": "success",
  "retry_count": 0,
  "chameleon_hash_ref": null,
  "previous_anchor_id": null,
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-02-01T10:00:03Z"
}
```

---

### 7.5 `version_history`

**Purpose**: Stores complete version history for every mutable field in patient data, healthcare records, prescriptions, and lab reports. Supports right-to-access previous states, diff views, and audit compliance.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `resource_type` | String | Yes | No | Source collection name |
| `resource_id` | String (UUID) | Yes | No | Source document ID |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id (owning patient) |
| `field_path` | String | Yes | No | Dot-notation field path (e.g., `full_name`, `medications`) |
| `version_number` | Integer | Yes | No | Sequential version for this field |
| `previous_value` | Object | Yes | 🔐 | Previous field value (encrypted) |
| `new_value` | Object | Yes | 🔐 | Updated field value (encrypted) |
| `previous_value_hash` | String | Yes | No | SHA-256 of plaintext previous value |
| `new_value_hash` | String | Yes | No | SHA-256 of plaintext new value |
| `modified_by` | String (UUID) | Yes | No | FK → users._id (actor) |
| `modified_by_role` | String (Enum) | Yes | No | Actor role |
| `modification_reason` | String | Yes | No | Stated reason for change |
| `modification_type` | String (Enum) | Yes | No | `correction`, `update`, `redaction`, `system_migration` |
| `legal_basis` | String | No | No | DPDP legal basis (for corrections/redactions) |
| `chameleon_hash_ref` | String (UUID) | No | No | FK → chameleon_hash_records._id (if redaction) |
| `blockchain_tx_ref` | String | No | No | On-chain verification tx |
| `blockchain_anchor_id` | String (UUID) | No | No | FK → blockchain_anchors._id |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Version creation timestamp |

**Indexes**:
```
{ "resource_type": 1, "resource_id": 1, "field_path": 1, "version_number": -1 }  -- field version lookup
{ "patient_id": 1, "created_at": -1 }                                              -- patient version history
{ "modified_by": 1, "created_at": -1 }                                             -- actor modification history
{ "modification_type": 1, "created_at": -1 }                                       -- type filtering
{ "chameleon_hash_ref": 1 }                                                         -- redaction tracking
{ "resource_type": 1, "resource_id": 1, "created_at": -1 }                        -- all versions for a doc
```

**Encryption Strategy**: `previous_value` and `new_value` are encrypted with the patient's AES-256-GCM key. Hashes of plaintext values are stored for integrity verification without requiring decryption.

**Retention**: 8 years minimum (aligned with healthcare record retention). Versions are never deleted, even after patient data erasure — only the `previous_value` and `new_value` fields are replaced with `[REDACTED]` ciphertext.

**Example Document**:
```json
{
  "_id": "ver-1001-abcd-efgh-ijkl-mnop",
  "resource_type": "patients",
  "resource_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "field_path": "phone_number",
  "version_number": 2,
  "previous_value": {
    "ciphertext": "enc_previous_phone...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "new_value": {
    "ciphertext": "enc_new_phone...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "previous_value_hash": "sha256_of_old_phone_plaintext",
  "new_value_hash": "sha256_of_new_phone_plaintext",
  "modified_by": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "modified_by_role": "patient",
  "modification_reason": "Phone number changed - updated to current number",
  "modification_type": "correction",
  "legal_basis": "DPDP Act Section 12 - Right to Correction",
  "chameleon_hash_ref": "ch-2001-abcd-efgh",
  "blockchain_tx_ref": "0xversion_tx_hash...",
  "blockchain_anchor_id": "blk-ver-1001",
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T14:30:00Z"
}
```

---

## 8. Audit Trail Storage Design

### 8.1 Append-Only Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    AUDIT LOG CHAIN                             │
│                                                                │
│  Log₁ ──hash──→ Log₂ ──hash──→ Log₃ ──hash──→ Log₄          │
│   │               │               │               │           │
│   └─blockchain    └─blockchain    └─blockchain    └─blockchain│
│     anchor          anchor          anchor          anchor    │
└──────────────────────────────────────────────────────────────┘
```

- **Chain Integrity**: Each log's `previous_log_hash` references the preceding entry, forming a hash chain
- **Blockchain Anchoring**: Every log is independently anchored on-chain via `AuditContract.storeAuditHash()`
- **Dual Verification**: Integrity can be verified via (1) hash chain continuity AND (2) blockchain comparison
- **Tamper Detection**: If `log_hash` recomputed ≠ stored `log_hash`, the entry is marked `tampered: true`

### 8.2 Audit Log Lifecycle

```
Event Occurs
  → AuditService generates log entry
  → Compute log_hash = SHA-256(fields + previous_log_hash)
  → Insert into audit_logs (append-only)
  → Queue blockchain anchor (async, <10s SLA)
  → If patient-related → create/update data_access_logs entry
  → If security event → trigger BreachDetector analysis
```

### 8.3 Storage Tiers

| Tier | Age | Storage | Access Pattern |
|------|-----|---------|----------------|
| Hot | 0-90 days | MongoDB primary (SSD) | Frequent queries, real-time |
| Warm | 90 days - 2 years | MongoDB secondary (HDD) | Occasional queries |
| Cold | 2-8 years | Compressed archive (India DC) | Compliance/legal requests only |

### 8.4 Audit Log Aggregation for Patient Timeline

The `data_access_logs` collection is a **materialized view** derived from `audit_logs`:
- Filtered to patient-relevant events only
- Enriched with accessor display name and organization
- Optimized for timeline rendering (patient_id + created_at index)
- Updated in near-real-time (within 5 seconds of source audit log creation)

---

## 9. Chameleon Hash Metadata Storage Design

### 9.1 `chameleon_hash_records` Collection

**Purpose**: Stores all Chameleon Hash operations including key parameters, collision generation events, and authorization proofs. This is the cryptographic backbone of the redactable blockchain.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `resource_type` | String | Yes | No | Collection that was redacted |
| `resource_id` | String (UUID) | Yes | No | Document that was redacted |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id |
| `operation_type` | String (Enum) | Yes | No | `correction`, `erasure`, `consent_withdrawal` |
| `status` | String (Enum) | Yes | No | `pending_authorization`, `authorized`, `collision_generated`, `completed`, `failed` |
| `original_message_hash` | String | Yes | No | SHA-256 of original plaintext (m) |
| `modified_message_hash` | String | Yes | No | SHA-256 of modified plaintext (m') |
| `chameleon_hash_value` | String | Yes | No | CH(m,r) = CH(m',r') — the preserved hash |
| `original_randomness` | String | Yes | 🔐 | Original r value |
| `new_randomness` | String | Yes | 🔐 | Computed r' value (collision) |
| `public_key_ref` | String | Yes | No | Reference to Chameleon Hash public key (y) |
| `generator` | String | Yes | No | Generator value (g) used |
| `prime_modulus` | String | Yes | No | Prime modulus (p) used |
| `trapdoor_key_used` | Boolean | Yes | No | Whether trapdoor (secret key) was used |
| `authorized_by` | String (UUID) | Yes | No | FK → users._id (DPO/Admin) |
| `authorized_by_role` | String (Enum) | Yes | No | Must be `dpo` or `admin` |
| `authorization_timestamp` | DateTime | Yes | No | When authorization was granted |
| `mfa_verified` | Boolean | Yes | No | Whether MFA was confirmed |
| `legal_basis` | String | Yes | No | DPDP Act section justifying the operation |
| `modification_reason` | String | Yes | No | Detailed reason for redaction/correction |
| `collision_generated_at` | DateTime | No | No | When r' was computed |
| `collision_proof` | Object | Yes | 🔐 | Cryptographic proof linking trapdoor usage to authorizer |
| `previous_version_id` | String (UUID) | No | No | FK → version_history._id (preserved version) |
| `blockchain_anchor_id` | String (UUID) | No | No | FK → blockchain_anchors._id |
| `blockchain_tx_ref` | String | No | No | On-chain proof transaction |
| `audit_log_id` | String (UUID) | Yes | No | FK → audit_logs._id (linked audit entry) |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Record creation |
| `completed_at` | DateTime | No | No | Operation completion |

**Indexes**:
```
{ "resource_type": 1, "resource_id": 1 }           -- resource redaction history
{ "patient_id": 1, "created_at": -1 }              -- patient redaction history
{ "status": 1 }                                     -- pending operations
{ "authorized_by": 1, "created_at": -1 }           -- authorizer activity
{ "operation_type": 1, "status": 1 }               -- type + status filtering
{ "chameleon_hash_value": 1 }                       -- hash lookup
{ "blockchain_tx_ref": 1 }                          -- blockchain verification
```

**Example Document**:
```json
{
  "_id": "ch-2001-abcd-efgh-ijkl-mnop",
  "resource_type": "patients",
  "resource_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "operation_type": "correction",
  "status": "completed",
  "original_message_hash": "sha256_of_original_phone_number",
  "modified_message_hash": "sha256_of_corrected_phone_number",
  "chameleon_hash_value": "preserved_chameleon_hash_output",
  "original_randomness": {
    "ciphertext": "enc_original_r_value...",
    "iv": "...", "tag": "...",
    "key_id": "key-system-chameleon"
  },
  "new_randomness": {
    "ciphertext": "enc_new_r_prime_value...",
    "iv": "...", "tag": "...",
    "key_id": "key-system-chameleon"
  },
  "public_key_ref": "chameleon-pubkey-001",
  "generator": "2",
  "prime_modulus": "large_prime_p_value",
  "trapdoor_key_used": true,
  "authorized_by": "dpo-uuid-0001",
  "authorized_by_role": "dpo",
  "authorization_timestamp": "2025-06-10T14:25:00Z",
  "mfa_verified": true,
  "legal_basis": "DPDP Act Section 12 - Right to Correction",
  "modification_reason": "Patient requested correction of phone number - verified identity via MFA",
  "collision_generated_at": "2025-06-10T14:25:05Z",
  "collision_proof": {
    "ciphertext": "enc_cryptographic_proof...",
    "iv": "...", "tag": "...",
    "key_id": "key-system-chameleon"
  },
  "previous_version_id": "ver-1001-abcd-efgh-ijkl-mnop",
  "blockchain_anchor_id": "blk-ch-2001",
  "blockchain_tx_ref": "0xchameleon_tx_hash...",
  "audit_log_id": "aud-ch-2001-linked",
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T14:25:00Z",
  "completed_at": "2025-06-10T14:25:08Z"
}
```

### 9.2 Chameleon Hash Workflow (Database Perspective)

```
1. Correction/Erasure Request Received
   └── Create chameleon_hash_records entry (status: pending_authorization)

2. DPO/Admin Authorization (MFA verified)
   └── Update status → authorized
   └── Record authorized_by, authorization_timestamp

3. Collision Generation
   └── Compute r' such that CH(m,r) = CH(m',r')
   └── Store original_randomness (encrypted) and new_randomness (encrypted)
   └── Update status → collision_generated
   └── Generate collision_proof

4. Apply Modification
   └── Update source document with new value
   └── Create version_history entry (previous_version_id)
   └── Blockchain remains valid (hash unchanged)
   └── Update status → completed

5. Blockchain Proof
   └── Anchor redaction proof on-chain
   └── Store blockchain_anchor_id, blockchain_tx_ref
   └── Create audit_log entry
```

---

## 10. Blockchain Anchoring Strategy

### 10.1 Anchoring Decision Matrix

| Event | Smart Contract | Function | Priority | SLA |
|-------|---------------|----------|----------|-----|
| Consent grant/modify/withdraw | ConsentContract | `storeConsent()` | High | 10s |
| Consent receipt generation | ConsentContract | `storeReceipt()` | Medium | 10s |
| Healthcare record creation | VerificationContract | `storeHash()` | High | 10s |
| Prescription creation/dispensing | VerificationContract | `storeHash()` | High | 10s |
| Lab report creation | VerificationContract | `storeHash()` | High | 10s |
| Patient data correction | VerificationContract | `storeHash()` | High | 10s |
| Data erasure/redaction | VerificationContract | `storeRedactionProof()` | Critical | 10s |
| Audit log entry | AuditContract | `storeAuditHash()` | Medium | 10s |
| Version history entry | VerificationContract | `storeHash()` | Medium | 10s |
| Breach trail | AuditContract | `storeAuditHash()` | Critical | 10s |
| Grievance resolution | AuditContract | `storeAuditHash()` | Medium | 10s |
| Processor authorization | ConsentContract | `storeConsent()` | Medium | 10s |

### 10.2 Hash Computation Standard

All hashes stored on-chain follow a canonical format:

```python
import json
import hashlib

def compute_anchor_hash(document: dict, fields_to_hash: list) -> str:
    """
    Compute deterministic SHA-256 hash for blockchain anchoring.
    - Extract specified fields from document
    - Sort keys alphabetically
    - Serialize as compact JSON (no whitespace)
    - Compute SHA-256 hex digest
    """
    subset = {k: document[k] for k in sorted(fields_to_hash) if k in document}
    canonical = json.dumps(subset, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

### 10.3 Anchor Chain Linking

For documents that undergo multiple modifications, each `blockchain_anchors` entry links to the previous anchor for the same resource via `previous_anchor_id`:

```
Record Created → Anchor₁ (previous: null)
Record Updated → Anchor₂ (previous: Anchor₁._id)
Record Corrected → Anchor₃ (previous: Anchor₂._id)
Record Redacted → Anchor₄ (previous: Anchor₃._id)
```

This creates a verifiable chain of modifications per resource, complementing the global blockchain ordering.

---

*Part 3 complete. Part 4 will cover: notifications, breach_incidents, grievance_requests, plus the cross-cutting design sections (encryption strategy, data retention strategy, soft delete vs redaction strategy, DPDP data lifecycle mapping, and scalability considerations).*


---

## 11. Collection Schemas (Part 4 — Notifications, Incidents & Grievances)

---

### 11.1 `notifications`

**Purpose**: Stores all system-generated notifications for users including data access alerts, consent expiry warnings, breach notifications, integrity violations, and grievance status updates. Supports priority levels and read/unread tracking.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Primary identifier |
| `recipient_id` | String (UUID) | Yes | No | FK → users._id (notification target) |
| `recipient_role` | String (Enum) | Yes | No | Role of recipient |
| `notification_type` | String (Enum) | Yes | No | `data_access`, `consent_expiry`, `consent_change`, `breach_alert`, `integrity_violation`, `emergency_access`, `erasure_complete`, `grievance_update`, `session_alert`, `rate_limit_warning`, `key_rotation`, `processor_breach` |
| `priority` | String (Enum) | Yes | No | `critical`, `high`, `medium`, `low` |
| `title` | String | Yes | No | Short notification title |
| `message` | String | Yes | No | Notification body text |
| `category` | String (Enum) | Yes | No | `security`, `consent`, `access`, `compliance`, `system` |
| `source_resource_type` | String | No | No | Triggering collection |
| `source_resource_id` | String (UUID) | No | No | Triggering document ID |
| `action_url` | String | No | No | Deep link to relevant page |
| `action_label` | String | No | No | CTA button text (e.g., "Review Access") |
| `read` | Boolean | Yes | No | Read status |
| `read_at` | DateTime | No | No | When notification was read |
| `dismissed` | Boolean | Yes | No | Dismissed by user |
| `dismissed_at` | DateTime | No | No | Dismissal timestamp |
| `delivery_channel` | String (Enum) | Yes | No | `in_app`, `email`, `both` |
| `email_sent` | Boolean | Yes | No | Whether email was dispatched |
| `email_sent_at` | DateTime | No | No | Email dispatch timestamp |
| `expires_at` | DateTime | No | No | Auto-dismiss after this date |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Notification creation |

**Indexes**:
```
{ "recipient_id": 1, "read": 1, "created_at": -1 }        -- unread notifications (primary query)
{ "recipient_id": 1, "category": 1, "created_at": -1 }    -- category filtering
{ "recipient_id": 1, "priority": 1, "created_at": -1 }    -- priority filtering
{ "notification_type": 1, "created_at": -1 }               -- type-based queries
{ "expires_at": 1 }                                         -- TTL: auto-cleanup expired
{ "created_at": -1 }                                        -- chronological listing
```

**Retention**: Notifications auto-expire after 90 days. Critical notifications (breach, integrity) retained for 1 year. TTL index on `expires_at` handles cleanup.

**Example Document**:
```json
{
  "_id": "ntf-1001-abcd-efgh-ijkl-mnop",
  "recipient_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "recipient_role": "patient",
  "notification_type": "data_access",
  "priority": "medium",
  "title": "Your medical records were accessed",
  "message": "Dr. Priya Sharma (Cardiology) accessed your Medical History and Allergies data for a consultation.",
  "category": "access",
  "source_resource_type": "data_access_logs",
  "source_resource_id": "dal-8001-abcd-efgh-ijkl-mnop",
  "action_url": "/timeline",
  "action_label": "View Timeline",
  "read": false,
  "read_at": null,
  "dismissed": false,
  "dismissed_at": null,
  "delivery_channel": "in_app",
  "email_sent": false,
  "email_sent_at": null,
  "expires_at": "2025-09-10T11:33:00Z",
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T11:33:00Z"
}
```

---

### 11.2 `breach_incidents`

**Purpose**: Stores security incident records from detection through containment and resolution. Supports the DPO's incident management workflow and DPDP breach notification compliance.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Incident identifier |
| `incident_type` | String (Enum) | Yes | No | `unauthorized_access`, `data_exfiltration`, `consent_violation`, `rate_limit_abuse`, `session_hijack`, `privilege_escalation`, `anomalous_pattern`, `processor_breach` |
| `severity` | String (Enum) | Yes | No | `low`, `medium`, `high`, `critical` |
| `status` | String (Enum) | Yes | No | `open`, `investigating`, `contained`, `resolved`, `closed` |
| `detected_at` | DateTime | Yes | No | Detection timestamp |
| `detected_by` | String (Enum) | Yes | No | `breach_detector`, `rate_limiter`, `session_manager`, `manual_report`, `processor_report` |
| `suspected_actor_id` | String (UUID) | No | No | FK → users._id (suspected user) |
| `suspected_actor_role` | String | No | No | Role of suspected actor |
| `suspected_actor_ip` | String | No | No | Source IP address |
| `affected_patients` | Array[String(UUID)] | Yes | No | FKs → patients._id |
| `affected_patient_count` | Integer | Yes | No | Count of affected patients |
| `affected_data_categories` | Array[String] | Yes | No | Data categories involved |
| `affected_records_count` | Integer | Yes | No | Number of records affected |
| `detection_rule` | String | No | No | Rule ID that triggered detection |
| `detection_details` | Object | Yes | No | Rule parameters and threshold values |
| `containment_actions` | Array[Object] | No | No | Actions taken to contain breach |
| `resolution_details` | Object | No | No | How incident was resolved |
| `resolved_at` | DateTime | No | No | Resolution timestamp |
| `resolved_by` | String (UUID) | No | No | FK → users._id (resolver) |
| `dpo_notified` | Boolean | Yes | No | Whether DPO was notified |
| `dpo_notified_at` | DateTime | No | No | DPO notification timestamp |
| `patients_notified` | Boolean | Yes | No | Whether affected patients notified |
| `patients_notified_at` | DateTime | No | No | Patient notification timestamp |
| `notification_within_sla` | Boolean | No | No | Whether notification met 72h SLA |
| `root_cause` | String | No | No | Root cause analysis |
| `remediation_plan` | String | No | No | Steps to prevent recurrence |
| `blockchain_trail_ref` | String (UUID) | No | No | FK → blockchain_anchors._id |
| `audit_log_ids` | Array[String(UUID)] | Yes | No | FKs → audit_logs._id (related entries) |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Record creation |
| `updated_at` | DateTime | Yes | No | Last status update |

**Containment Actions Structure**:
```json
[
  {
    "action": "session_terminated",
    "target_user_id": "uuid",
    "timestamp": "2025-06-10T12:00:05Z",
    "performed_by": "system"
  },
  {
    "action": "account_suspended",
    "target_user_id": "uuid",
    "timestamp": "2025-06-10T12:00:10Z",
    "performed_by": "dpo-uuid"
  }
]
```

**Indexes**:
```
{ "status": 1, "severity": 1, "detected_at": -1 }         -- DPO dashboard (primary)
{ "severity": 1, "detected_at": -1 }                       -- severity monitoring
{ "suspected_actor_id": 1 }                                 -- actor investigation
{ "affected_patients": 1 }                                  -- patient impact lookup
{ "incident_type": 1, "status": 1 }                        -- type filtering
{ "detected_at": -1 }                                       -- chronological
{ "notification_within_sla": 1 }                            -- SLA compliance tracking
```

**Retention**: Breach incidents retained for 8 years (compliance). Never deleted.

**Example Document**:
```json
{
  "_id": "brch-2001-abcd-efgh-ijkl-mnop",
  "incident_type": "unauthorized_access",
  "severity": "high",
  "status": "contained",
  "detected_at": "2025-06-10T12:00:00Z",
  "detected_by": "breach_detector",
  "suspected_actor_id": "suspicious-user-uuid",
  "suspected_actor_role": "doctor",
  "suspected_actor_ip": "103.45.67.89",
  "affected_patients": ["pat-1234-abcd-efgh-ijkl-mnop", "pat-5678-wxyz"],
  "affected_patient_count": 2,
  "affected_data_categories": ["medical_history", "prescriptions"],
  "affected_records_count": 5,
  "detection_rule": "rule-003-consent-scope-violation",
  "detection_details": {
    "rule_description": "Access to data categories outside consent scope",
    "threshold": "any single violation",
    "observed": "Attempted access to prescriptions without pharmacy_access consent"
  },
  "containment_actions": [
    {
      "action": "session_terminated",
      "target_user_id": "suspicious-user-uuid",
      "timestamp": "2025-06-10T12:00:05Z",
      "performed_by": "system"
    },
    {
      "action": "account_suspended",
      "target_user_id": "suspicious-user-uuid",
      "timestamp": "2025-06-10T12:01:00Z",
      "performed_by": "dpo-uuid-0001"
    }
  ],
  "resolution_details": null,
  "resolved_at": null,
  "resolved_by": null,
  "dpo_notified": true,
  "dpo_notified_at": "2025-06-10T12:00:15Z",
  "patients_notified": true,
  "patients_notified_at": "2025-06-10T12:00:45Z",
  "notification_within_sla": true,
  "root_cause": null,
  "remediation_plan": null,
  "blockchain_trail_ref": "blk-brch-2001",
  "audit_log_ids": ["aud-brch-001", "aud-brch-002", "aud-brch-003"],
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T12:00:00Z",
  "updated_at": "2025-06-10T12:01:00Z"
}
```

---

### 11.3 `grievance_requests`

**Purpose**: Tracks grievance submissions by Data Principals per DPDP Act Section 13. Manages the full lifecycle from submission through escalation to resolution with SLA enforcement.

| Field | Type | Required | Encrypted | Description |
|-------|------|----------|-----------|-------------|
| `_id` | String (UUID v4) | Yes | No | Grievance identifier |
| `patient_id` | String (UUID) | Yes | No | FK → patients._id (complainant) |
| `user_id` | String (UUID) | Yes | No | FK → users._id (complainant) |
| `grievance_category` | String (Enum) | Yes | No | `consent_violation`, `unauthorized_access`, `erasure_failure`, `data_inaccuracy`, `breach_notification_failure`, `processor_violation`, `other` |
| `description` | String | Yes | 🔐 | Detailed grievance description (min 100 chars) |
| `affected_data_categories` | Array[String] | No | No | Data categories involved |
| `status` | String (Enum) | Yes | No | `submitted`, `acknowledged`, `under_investigation`, `escalated_l2`, `escalated_l3`, `resolved`, `closed` |
| `priority` | String (Enum) | Yes | No | `low`, `medium`, `high`, `critical` |
| `submitted_at` | DateTime | Yes | No | Submission timestamp |
| `acknowledged_at` | DateTime | No | No | Acknowledgment timestamp (SLA: 24h) |
| `acknowledgment_sla_met` | Boolean | No | No | Whether 24h SLA was met |
| `resolution_due_date` | DateTime | Yes | No | 15 business days from submission |
| `resolved_at` | DateTime | No | No | Resolution timestamp |
| `resolution_sla_met` | Boolean | No | No | Whether 15-day SLA was met |
| `resolution_summary` | String | No | No | How grievance was resolved |
| `resolution_category` | String (Enum) | No | No | `upheld`, `partially_upheld`, `not_upheld`, `withdrawn` |
| `current_handler_id` | String (UUID) | No | No | FK → users._id (assigned handler) |
| `current_level` | String (Enum) | Yes | No | `level_1_support`, `level_2_dpo`, `level_3_external` |
| `escalation_history` | Array[Object] | No | No | Escalation events |
| `communications` | Array[Object] | No | 🔐 | Messages between parties |
| `supporting_evidence` | Array[Object] | No | 🔐 | Attached files/screenshots |
| `satisfaction_rating` | Integer | No | No | 1-5 rating by patient (post-resolution) |
| `satisfaction_feedback` | String | No | 🔐 | Patient feedback text |
| `blockchain_resolution_ref` | String (UUID) | No | No | FK → blockchain_anchors._id (resolution proof) |
| `audit_log_ids` | Array[String(UUID)] | Yes | No | FKs → audit_logs._id |
| `data_residency` | Object | Yes | No | Residency metadata |
| `created_at` | DateTime | Yes | No | Record creation |
| `updated_at` | DateTime | Yes | No | Last update |

**Escalation History Structure**:
```json
[
  {
    "from_level": "level_1_support",
    "to_level": "level_2_dpo",
    "escalated_at": "2025-06-15T09:00:00Z",
    "escalated_by": "system",
    "reason": "Resolution SLA approaching - 10 business days elapsed"
  }
]
```

**Communications Structure** (encrypted):
```json
[
  {
    "sender_id": "uuid",
    "sender_role": "support",
    "message": "We are investigating your concern...",
    "timestamp": "2025-06-11T10:00:00Z",
    "attachments": []
  }
]
```

**Indexes**:
```
{ "patient_id": 1, "status": 1, "created_at": -1 }        -- patient grievance list
{ "status": 1, "resolution_due_date": 1 }                  -- SLA monitoring
{ "current_handler_id": 1, "status": 1 }                   -- handler queue
{ "current_level": 1, "status": 1 }                        -- escalation level filtering
{ "grievance_category": 1, "status": 1 }                   -- category reporting
{ "acknowledgment_sla_met": 1 }                             -- SLA compliance audit
{ "resolution_sla_met": 1 }                                 -- resolution SLA audit
{ "submitted_at": -1 }                                      -- chronological
```

**Retention**: Grievance records retained for 5 years post-closure. Resolution records blockchain-anchored.

**Example Document**:
```json
{
  "_id": "grv-3001-abcd-efgh-ijkl-mnop",
  "patient_id": "pat-1234-abcd-efgh-ijkl-mnop",
  "user_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "grievance_category": "unauthorized_access",
  "description": {
    "ciphertext": "enc_I_noticed_unauthorized_access_to_my_prescription_records...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "affected_data_categories": ["prescriptions"],
  "status": "under_investigation",
  "priority": "high",
  "submitted_at": "2025-06-10T09:00:00Z",
  "acknowledged_at": "2025-06-10T14:00:00Z",
  "acknowledgment_sla_met": true,
  "resolution_due_date": "2025-07-01T09:00:00Z",
  "resolved_at": null,
  "resolution_sla_met": null,
  "resolution_summary": null,
  "resolution_category": null,
  "current_handler_id": "support-agent-uuid",
  "current_level": "level_1_support",
  "escalation_history": [],
  "communications": {
    "ciphertext": "enc_communications_array...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "supporting_evidence": {
    "ciphertext": "enc_evidence_array...",
    "iv": "...", "tag": "...",
    "key_id": "key-001-patient-a1b2"
  },
  "satisfaction_rating": null,
  "satisfaction_feedback": null,
  "blockchain_resolution_ref": null,
  "audit_log_ids": ["aud-grv-001"],
  "data_residency": { "region": "IN", "verified_at": "2025-06-01T00:00:00Z" },
  "created_at": "2025-06-10T09:00:00Z",
  "updated_at": "2025-06-10T14:00:00Z"
}
```

---

## 12. Data Retention Strategy

### 12.1 Retention Periods by Collection

| Collection | Retention Period | Basis | Archival Strategy |
|------------|-----------------|-------|-------------------|
| `users` | Account lifetime + 3 years post-deactivation | DPDP Act + business need | Anonymize after retention |
| `patients` | 8 years from last clinical interaction | Healthcare record retention laws | Cold storage archive |
| `doctors` | Employment duration + 3 years | Professional record keeping | Deactivate, retain license ref |
| `pharmacy_staff` | Employment duration + 3 years | Professional record keeping | Deactivate, retain license ref |
| `organizations` | Indefinite (while registered) | Business entity | Mark inactive on deregistration |
| `consents` | 8 years from consent action | DPDP compliance proof | Never delete, cold archive |
| `consent_receipts` | 8 years from issuance | DPDP compliance proof | Never delete, cold archive |
| `healthcare_records` | 8 years from record creation | Healthcare regulations | Cold storage after 2 years |
| `prescriptions` | 8 years from prescription date | Healthcare regulations | Cold storage after 2 years |
| `lab_reports` | 8 years from report date | Healthcare regulations | Cold storage after 2 years |
| `audit_logs` | 8 years | Compliance + legal | Tiered: hot → warm → cold |
| `data_access_logs` | 3 years | Transparency requirement | Archive after 1 year |
| `integrity_verifications` | 3 years | Operational | Auto-archive after 1 year |
| `blockchain_anchors` | Indefinite | Blockchain references permanent | No deletion (references immutable chain) |
| `version_history` | 8 years | Healthcare record lifecycle | Cold storage, values redactable |
| `notifications` | 90 days (standard), 1 year (critical) | Operational | TTL auto-delete |
| `breach_incidents` | 8 years | Compliance + legal | Never delete |
| `grievance_requests` | 5 years post-closure | DPDP Section 13 compliance | Cold archive after 2 years |
| `chameleon_hash_records` | Indefinite | Cryptographic proof | Never delete |

### 12.2 Retention Enforcement

```
┌─────────────────────────────────────────────────┐
│           RETENTION ENFORCEMENT JOBS             │
├─────────────────────────────────────────────────┤
│                                                  │
│  Daily:                                          │
│  ├── Check notification TTL expiry              │
│  ├── Flag approaching-expiry consents (7 days) │
│  └── Update data_categories retention status    │
│                                                  │
│  Weekly:                                         │
│  ├── Archive warm-tier audit logs (>90 days)    │
│  ├── Archive data_access_logs (>1 year)         │
│  └── Generate retention compliance report       │
│                                                  │
│  Monthly:                                        │
│  ├── Move cold-tier data (>2 years)            │
│  ├── Verify residency compliance               │
│  └── DPO retention summary notification        │
│                                                  │
│  Annually:                                       │
│  ├── Review and purge beyond-retention data    │
│  └── Full retention audit with blockchain proof │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 13. Soft Delete vs Redaction Strategy

### 13.1 Strategy Overview

The system does NOT use traditional soft delete (setting a `deleted` flag). Instead, it implements **DPDP-compliant redaction** using Chameleon Hashing:

| Strategy | When Used | Mechanism | Audit Trail |
|----------|-----------|-----------|-------------|
| **Redaction** | Right to Erasure (DPDP Section 12) | Replace sensitive fields with `[REDACTED]`, update Chameleon Hash | Full audit + blockchain proof preserved |
| **Logical Deactivation** | Account closure, staff departure | Set `status: deactivated`, retain record | Audit entry, no data loss |
| **Consent Expiry** | Consent auto-expires | Revoke access, mark consent `expired` | Consent record preserved with status change |
| **Never Delete** | Audit logs, blockchain anchors, consent receipts | Immutable, append-only | Self-evident from existence |

### 13.2 Redaction Workflow (Database Operations)

```
Step 1: Patient requests erasure
  └── Create grievance/erasure request document

Step 2: Identity verification (MFA)
  └── Verified via Auth_Service

Step 3: DPO authorization
  └── Create chameleon_hash_records entry (status: pending_authorization)
  └── DPO approves → status: authorized

Step 4: Version preservation
  └── Create version_history entry with encrypted current values
  └── Link to chameleon_hash_records._id

Step 5: Chameleon Hash collision
  └── Compute new randomness r' maintaining CH(m,r) = CH(m',r')
  └── Store r' in chameleon_hash_records (encrypted)

Step 6: Field redaction
  └── Replace field values with redacted ciphertext:
      {
        "ciphertext": "REDACTED",
        "iv": "000...",
        "tag": "000...",
        "key_id": "REDACTED"
      }
  └── Set document flags: redacted=true, redacted_at, redacted_by

Step 7: Blockchain proof
  └── Anchor redaction proof on-chain
  └── Link blockchain_anchors entry

Step 8: Propagation
  └── Revoke all active consents for affected categories
  └── Notify processors to delete shared data
  └── Update data_categories_stored in patients collection
```

### 13.3 What Gets Redacted vs Preserved

| Data Type | On Erasure | Justification |
|-----------|------------|---------------|
| Personal information (name, phone, address, ID) | **REDACTED** | DPDP right to erasure |
| Medical records (clinical content) | **REDACTED** | Patient-controlled data |
| Prescriptions (medication details) | **REDACTED** | Patient-controlled data |
| Lab reports (results) | **REDACTED** | Patient-controlled data |
| Audit log entries | **PRESERVED** (actor identity anonymized) | Legal compliance requirement |
| Consent records | **PRESERVED** (metadata only) | Proof of lawful processing |
| Blockchain anchors | **PRESERVED** | Immutable by design |
| Version history (values) | **REDACTED** (field values only) | Values erasable, metadata preserved |
| Chameleon hash records | **PRESERVED** | Cryptographic proof of lawful redaction |

---

## 14. DPDP Data Lifecycle Mapping

### 14.1 Data Lifecycle Stages

```
┌─────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│COLLECTION│ →  │PROCESSING│ →  │  STORAGE  │ →  │RETENTION │ →  │ ERASURE  │
│          │    │          │    │           │    │          │    │          │
│Register  │    │Encrypt   │    │MongoDB    │    │8yr timer │    │Chameleon │
│Consent   │    │Hash      │    │Blockchain │    │Archival  │    │Redaction │
│Purpose   │    │Anchor    │    │Key Store  │    │Audit     │    │Proof     │
└─────────┘    └──────────┘    └───────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
 Audit Log       Audit Log       Audit Log       Audit Log       Audit Log
 Consent Rec     Blockchain      Integrity       Retention Chk   Blockchain
                 Anchor          Verify                          Proof
```

### 14.2 DPDP Act Section → Database Mapping

| DPDP Act Section | Right/Obligation | Database Implementation |
|------------------|-------------------|------------------------|
| Section 5 | Consent for processing | `consents` collection with blockchain anchoring |
| Section 6 | Consent specifics (purpose, scope, withdrawal) | `consents.consent_type`, `data_categories_in_scope`, `status` |
| Section 7 | Notice to Data Principal | `notifications` with consent context |
| Section 8(2) | Data Processor obligations | `data_processors` collection (future Part), `processor_access` in `data_access_logs` |
| Section 9 | Children's data (minors) | `users.is_minor`, `users.guardian_id`, `consents.guardian_consent` |
| Section 11 | Right to access | `patients` decryption + display, `data_access_logs` transparency |
| Section 12 | Right to correction | `version_history` + `chameleon_hash_records` |
| Section 12 | Right to erasure | Redaction workflow + `chameleon_hash_records` + blockchain proof |
| Section 13 | Grievance redressal | `grievance_requests` with SLA tracking |
| Section 8(6) | Breach notification | `breach_incidents` + `notifications` within 72h |
| Section 16-17 | Data localization | `data_residency` field on every collection |
| Accountability | Audit trail | `audit_logs` + `blockchain_anchors` chain |
| Transparency | Data usage visibility | `data_access_logs` + Data Usage Timeline UI |
| Purpose limitation | Minimal data per purpose | `consents.data_categories_in_scope` enforcement |
| Data minimization | Minimal collection | `patients.data_categories_stored` tracking |

### 14.3 Consent Lifecycle in Database

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   GRANT      │     │   ACTIVE     │     │   EXPIRE     │
│              │     │              │     │              │
│ consents:    │     │ consents:    │     │ consents:    │
│ status=active│ ──→ │ status=active│ ──→ │ status=      │
│ granted_at=  │     │ (enforced)   │     │  expired     │
│ now          │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                     │
       ▼                    ▼                     ▼
consent_receipts     data_access_logs       notifications
blockchain_anchors   (consent_id check)     (expiry alert)
audit_logs                                  audit_logs

                    ┌──────────────┐
                    │  WITHDRAW    │
                    │              │
                    │ consents:    │
                    │ status=      │
                    │  withdrawn   │
                    │ withdrawn_at │
                    └──────────────┘
                           │
                           ▼
                    consent_receipts
                    blockchain_anchors
                    notifications (to processors)
                    audit_logs
```

---

## 15. Scalability Considerations

### 15.1 Collection Size Projections (Year 1)

| Collection | Est. Documents/Year | Avg Doc Size | Est. Storage/Year |
|------------|--------------------:|-------------:|------------------:|
| `users` | 10,000 | 2 KB | 20 MB |
| `patients` | 8,000 | 4 KB | 32 MB |
| `doctors` | 500 | 2 KB | 1 MB |
| `pharmacy_staff` | 200 | 1.5 KB | 0.3 MB |
| `organizations` | 10 | 1 KB | 0.01 MB |
| `consents` | 50,000 | 1.5 KB | 75 MB |
| `consent_receipts` | 60,000 | 1 KB | 60 MB |
| `healthcare_records` | 100,000 | 5 KB | 500 MB |
| `prescriptions` | 80,000 | 3 KB | 240 MB |
| `lab_reports` | 60,000 | 6 KB | 360 MB |
| `audit_logs` | 5,000,000 | 1.5 KB | 7.5 GB |
| `data_access_logs` | 2,000,000 | 0.8 KB | 1.6 GB |
| `integrity_verifications` | 100,000 | 1 KB | 100 MB |
| `blockchain_anchors` | 6,000,000 | 0.8 KB | 4.8 GB |
| `version_history` | 500,000 | 2 KB | 1 GB |
| `notifications` | 3,000,000 | 0.5 KB | 1.5 GB |
| `breach_incidents` | 100 | 3 KB | 0.3 MB |
| `grievance_requests` | 500 | 4 KB | 2 MB |
| **Total** | | | **~17.8 GB** |

### 15.2 Scaling Strategies

| Challenge | Strategy | Implementation |
|-----------|----------|----------------|
| Audit log volume | Time-based sharding | Shard key: `{ created_at: "hashed" }` |
| Blockchain anchor volume | Batch anchoring | Group anchors in 5-second windows |
| Read scalability | Replica set read preference | `secondaryPreferred` for read-heavy queries |
| Write scalability | Write concern tuning | `w:majority` for critical, `w:1` for audit logs |
| Index memory | Covered queries | Design indexes to cover common query patterns |
| Large documents | Field projection | Always project only needed fields in queries |
| Cold data | Tiered storage | Online Archive for data >2 years |

### 15.3 Index Memory Budget

Target: Keep working set (frequently queried indexes) within available RAM.

| Collection | Index Count | Est. Index Size (Year 1) |
|------------|:-----------:|-------------------------:|
| `audit_logs` | 11 | ~1.2 GB |
| `blockchain_anchors` | 8 | ~900 MB |
| `data_access_logs` | 7 | ~400 MB |
| `notifications` | 6 | ~300 MB |
| `healthcare_records` | 7 | ~200 MB |
| Others (combined) | ~40 | ~500 MB |
| **Total** | | **~3.5 GB** |

Recommendation: Minimum 8 GB RAM for MongoDB primary node to accommodate indexes + working set.

### 15.4 Query Optimization Patterns

| Query Pattern | Optimization | Index Used |
|---------------|-------------|------------|
| Patient timeline (last 50 events) | Covered query + limit | `patient_id + created_at DESC` |
| Unread notifications | Partial index on `read: false` | `recipient_id + read + created_at` |
| Active consents check | Compound filter | `patient_id + consent_type + status` |
| Integrity verification | Direct hash lookup | `verification_hash` or `data_hash` |
| DPO breach dashboard | Status + severity filter | `status + severity + detected_at` |
| Audit search (date range) | Range scan with limit | `created_at DESC` with filters |

---

*Part 4 complete. The database_design.md document is now fully defined with all 18 collections, audit trail design, chameleon hash metadata, blockchain anchoring strategy, retention policy, redaction strategy, DPDP lifecycle mapping, and scalability considerations.*
