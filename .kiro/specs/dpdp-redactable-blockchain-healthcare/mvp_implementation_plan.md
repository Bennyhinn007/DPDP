# MVP Implementation Plan

## DPDP Compliant Redactable Blockchain Based Healthcare and Pharmacy Management System

---

## MVP Scope

### Included

| Feature | Core Capability |
|---------|-----------------|
| Authentication | Registration, login, JWT, RBAC (5 roles) |
| Patient Dashboard | Profile summary, health summary, recent activity |
| Healthcare Records | Consultations, prescriptions, lab reports (CRUD) |
| Consent Management | Grant, withdraw, enforce, receipts |
| AES Encryption | Field-level AES-256-GCM for all PII |
| Audit Logs | Every operation logged, data usage timeline |
| Blockchain Hash Anchoring | Consent + record hashes stored on-chain |
| Integrity Verification | Hash comparison, verified/violation status |

### Excluded (Post-MVP)

Breach Center, Privacy Score, Minors Workflow, Advanced Analytics, Third-Party Governance, Grievance Portal, Chameleon Hashing, Processor Management, Data Residency Checks, Notification Center.

---

## 1. Folder Structure

### 1.1 Backend

```
backend/
├── app/
│   ├── __init__.py                    # Flask app factory
│   ├── config.py                      # Config (dev/prod/test)
│   ├── extensions.py                  # MongoDB + Web3 init
│   │
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # /api/v1/auth/*
│   │   │   └── schemas.py
│   │   ├── patients/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # /api/v1/patients/*
│   │   │   └── schemas.py
│   │   ├── doctors/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # /api/v1/doctors/*
│   │   │   └── schemas.py
│   │   ├── pharmacy/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # /api/v1/pharmacy/*
│   │   │   └── schemas.py
│   │   ├── consents/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # /api/v1/consents/*
│   │   │   └── schemas.py
│   │   ├── audit/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # /api/v1/audit/*
│   │   │   └── schemas.py
│   │   ├── blockchain/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # /api/v1/blockchain/*
│   │   │   └── schemas.py
│   │   └── integrity/
│   │       ├── __init__.py
│   │       ├── routes.py             # /api/v1/integrity/*
│   │       └── schemas.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── patient_service.py
│   │   ├── doctor_service.py
│   │   ├── pharmacy_service.py
│   │   ├── consent_service.py
│   │   ├── audit_service.py
│   │   ├── encryption_service.py
│   │   ├── blockchain_service.py
│   │   └── integrity_service.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── patient_repository.py
│   │   ├── healthcare_record_repository.py
│   │   ├── prescription_repository.py
│   │   ├── consent_repository.py
│   │   ├── audit_repository.py
│   │   └── blockchain_repository.py
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth_middleware.py         # JWT validation
│   │   ├── rbac_middleware.py         # Role permission check
│   │   └── audit_middleware.py        # Auto audit logging
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── doctor.py
│   │   ├── pharmacy_staff.py
│   │   ├── healthcare_record.py
│   │   ├── prescription.py
│   │   ├── consent.py
│   │   ├── consent_receipt.py
│   │   ├── audit_log.py
│   │   └── blockchain_anchor.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── crypto.py                  # AES-256-GCM helpers
│   │   ├── validators.py             # Input validation
│   │   ├── constants.py              # Enums, config constants
│   │   ├── errors.py                 # Custom exceptions
│   │   └── helpers.py                # UUID generation, hashing
│   │
│   └── contracts/
│       ├── ConsentContract.sol
│       ├── VerificationContract.sol
│       ├── AuditContract.sol
│       ├── compiled/                  # ABI + bytecode (generated)
│       │   ├── ConsentContract.json
│       │   ├── VerificationContract.json
│       │   └── AuditContract.json
│       └── deploy.py                  # Deployment script
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Fixtures
│   ├── test_auth.py
│   ├── test_patients.py
│   ├── test_consents.py
│   ├── test_encryption.py
│   ├── test_blockchain.py
│   └── test_integrity.py
│
├── seeds/
│   └── seed_data.py                   # Demo data generation
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── run.py                             # Entry point
```

### 1.2 Frontend

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx                        # Root + routing
│   │
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   └── RegisterPage.tsx
│   │   ├── patient/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── PersonalDataCenter.tsx
│   │   │   ├── ConsentCenter.tsx
│   │   │   ├── DataTimeline.tsx
│   │   │   ├── AuditLogsPage.tsx
│   │   │   └── IntegrityVerification.tsx
│   │   ├── doctor/
│   │   │   ├── DoctorDashboard.tsx
│   │   │   ├── PatientAccess.tsx
│   │   │   └── ConsultationForm.tsx
│   │   └── pharmacy/
│   │       ├── PharmacyDashboard.tsx
│   │       └── DispenseForm.tsx
│   │
│   ├── components/
│   │   ├── ui/                        # Shadcn components (auto-gen)
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── RoleBasedNav.tsx
│   │   ├── privacy/
│   │   │   ├── ConsentCard.tsx
│   │   │   ├── IntegrityBadge.tsx
│   │   │   └── DataCategoryChip.tsx
│   │   ├── blockchain/
│   │   │   ├── TransactionRef.tsx
│   │   │   └── VerificationStatus.tsx
│   │   ├── timeline/
│   │   │   ├── TimelineEvent.tsx
│   │   │   └── TimelineFilter.tsx
│   │   └── shared/
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       └── ConfirmDialog.tsx
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useConsents.ts
│   │   ├── useBlockchain.ts
│   │   └── useAuditLogs.ts
│   │
│   ├── services/
│   │   ├── api.ts                     # Axios instance
│   │   ├── authApi.ts
│   │   ├── patientApi.ts
│   │   ├── consentApi.ts
│   │   ├── auditApi.ts
│   │   └── blockchainApi.ts
│   │
│   ├── store/
│   │   └── AuthContext.tsx
│   │
│   ├── types/
│   │   ├── user.ts
│   │   ├── patient.ts
│   │   ├── consent.ts
│   │   ├── audit.ts
│   │   └── blockchain.ts
│   │
│   └── utils/
│       ├── constants.ts
│       ├── formatters.ts
│       └── roleGuard.ts
│
├── tailwind.config.ts
├── tsconfig.json
├── vite.config.ts
├── package.json
└── Dockerfile
```

---

## 2. Backend APIs (MVP Scope)

### 2.1 Auth Blueprint (`/api/v1/auth`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/register` | Register new user (any role) | Public |
| POST | `/login` | Authenticate, return JWT + refresh | Public |
| POST | `/refresh` | Rotate refresh token, issue new JWT | Refresh token |
| POST | `/logout` | Invalidate session | JWT |
| GET | `/me` | Get current user profile | JWT |

### 2.2 Patients Blueprint (`/api/v1/patients`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/me` | Get own patient profile (decrypted) | Patient |
| PUT | `/me` | Update own profile fields | Patient |
| GET | `/me/health-summary` | Get health summary (conditions, allergies) | Patient |
| GET | `/me/data-categories` | Get stored data categories + retention | Patient |
| GET | `/me/download` | Export all data as JSON | Patient |
| GET | `/me/records` | Get all healthcare records | Patient |
| GET | `/me/prescriptions` | Get all prescriptions | Patient |
| GET | `/:patient_id` | Get patient profile (consent-gated) | Doctor |

### 2.3 Doctors Blueprint (`/api/v1/doctors`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/patients` | List patients with active consent | Doctor |
| GET | `/patients/:id/records` | Get patient records (consent-gated) | Doctor |
| POST | `/consultations` | Create consultation record | Doctor |
| GET | `/consultations` | List own consultations | Doctor |
| POST | `/break-glass` | Invoke emergency access | Doctor |

### 2.4 Pharmacy Blueprint (`/api/v1/pharmacy`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/prescriptions/:patient_id` | Get patient prescriptions (consent-gated) | Pharmacy |
| POST | `/dispense/:prescription_id` | Record dispensing event | Pharmacy |
| GET | `/history` | Get own dispensing history | Pharmacy |

### 2.5 Consents Blueprint (`/api/v1/consents`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/` | Get all own consents (6 types) | Patient |
| POST | `/grant` | Grant consent for a purpose | Patient |
| POST | `/:id/withdraw` | Withdraw consent | Patient |
| PUT | `/:id/modify` | Modify consent scope | Patient |
| GET | `/:id/receipt` | Get consent receipt | Patient |
| GET | `/receipts` | List all receipts | Patient |
| GET | `/active-sharing` | Get entities with active access | Patient |

### 2.6 Audit Blueprint (`/api/v1/audit`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/logs` | Search audit logs (own data) | Patient |
| GET | `/timeline` | Get data access timeline | Patient |
| GET | `/logs/all` | Search all audit logs | DPO |

### 2.7 Blockchain Blueprint (`/api/v1/blockchain`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/anchors/:resource_id` | Get blockchain anchors for resource | Authenticated |
| GET | `/transaction/:tx_hash` | Get transaction details | Authenticated |
| GET | `/status` | Get blockchain connection status | Admin |

### 2.8 Integrity Blueprint (`/api/v1/integrity`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/verify/:record_id` | Verify single record integrity | Patient |
| POST | `/verify-batch` | Verify all own records | Patient |
| GET | `/status` | Get latest verification status | Patient |

---

## 3. Frontend Pages (MVP Scope)

| # | Page | Route | Role | Key Components |
|---|------|-------|------|----------------|
| 1 | Login | `/login` | Public | Email input, password, submit, error display |
| 2 | Register | `/register` | Public | Role select, details form, age verify |
| 3 | Patient Dashboard | `/dashboard` | Patient | Health summary card, active consents count, recent activity list, integrity status |
| 4 | Personal Data Center | `/my-data` | Patient | Tabbed category view, edit fields, download button, blockchain refs |
| 5 | Consent Center | `/consents` | Patient | 6 consent type cards, grant/withdraw/modify actions |
| 6 | Data Timeline | `/timeline` | Patient | Vertical timeline, filter controls, access cards |
| 7 | Audit Logs | `/audit-logs` | Patient | DataTable with search, filter, pagination |
| 8 | Integrity Verification | `/verify` | Patient | Record list, verify buttons, green/red badges |
| 9 | Doctor Dashboard | `/doctor` | Doctor | Patient list (consent-granted), recent consultations |
| 10 | Patient Access | `/doctor/patients/:id` | Doctor | Patient record view (consent-gated), break-glass option |
| 11 | Consultation Form | `/doctor/consultations/new` | Doctor | Diagnosis, symptoms, treatment, prescription create |
| 12 | Pharmacy Dashboard | `/pharmacy` | Pharmacy | Pending prescriptions, dispensing history |
| 13 | Dispense Form | `/pharmacy/dispense/:id` | Pharmacy | Prescription detail, confirm dispense, notes |

---

## 4. Database Collections (MVP Scope)

### 4.1 Required Collections (10 of 18)

| Collection | Purpose | Encrypted Fields |
|------------|---------|-----------------|
| `users` | Authentication, roles, session | email, mfa_secret, date_of_birth |
| `patients` | Patient profile, health data | full_name, phone, address, identity_number, blood_group, allergies |
| `doctors` | Doctor profile, specialization | full_name, license_number, phone |
| `pharmacy_staff` | Pharmacy profile | full_name, license_number, phone |
| `healthcare_records` | Consultations, diagnoses | title, description, diagnosis_codes, symptoms, treatment_notes |
| `prescriptions` | Medications, dispensing | medications, diagnosis_summary, instructions |
| `consents` | Consent lifecycle | None (no PII — only references) |
| `consent_receipts` | Consent proof documents | None |
| `audit_logs` | Immutable audit trail | None (no PII — hashed actor references) |
| `blockchain_anchors` | On-chain transaction references | None |

### 4.2 Excluded from MVP

`organizations`, `lab_reports`, `notifications`, `breach_incidents`, `grievance_requests`, `data_access_logs`, `integrity_verifications`, `version_history` — added post-MVP.

**Note**: `data_access_logs` functionality is simplified in MVP by querying `audit_logs` directly with patient_id filter for the timeline.

---

## 5. Smart Contracts (MVP Scope)

### 5.1 ConsentContract.sol

| Function | Purpose |
|----------|---------|
| `storeConsent(key, hash, patient, purpose, action, scope, expiry)` | Record consent event |
| `withdrawConsent(key, withdrawalHash)` | Record withdrawal |
| `verifyConsent(key)` | Return consent record |
| `getPatientConsents(patient)` | List patient's consent keys |

### 5.2 VerificationContract.sol

| Function | Purpose |
|----------|---------|
| `storeHash(key, hash, resourceType, resourceId)` | Store record verification hash |
| `verifyHash(key, providedHash)` | Compare hash (returns match boolean) |
| `getRecord(key)` | Return stored hash + metadata |
| `batchVerify(keys[], hashes[])` | Verify multiple in one call |

### 5.3 AuditContract.sol

| Function | Purpose |
|----------|---------|
| `storeAuditHash(key, logHash, previousHash, actionType)` | Store audit entry hash |
| `verifyAuditHash(key, providedHash)` | Verify audit entry |
| `getAnchor(key)` | Return anchor details |

---

## 6. Development Order (4-Week Plan)

### Week 1: Foundation + Auth + Models

| Day | Dev A (Backend) | Dev B (Frontend) |
|-----|-----------------|------------------|
| Day 1 | Flask app factory, config, Docker Compose | Vite + React + Tailwind + Shadcn setup |
| Day 2 | MongoDB connection, all 10 collections + indexes | Design tokens, AppShell, Sidebar, Header |
| Day 3 | User model, registration endpoint (bcrypt, UUID) | Login page UI, form validation |
| Day 4 | Login endpoint (JWT RS256), refresh token | Register page UI, role selection |
| Day 5 | JWT middleware, RBAC middleware | Auth context, protected routes, role-based nav |

**Week 1 Gate**: All roles can register/login. Role-appropriate navigation renders.

---

### Week 2: Healthcare Data + Consent

| Day | Dev A (Backend) | Dev B (Frontend) |
|-----|-----------------|------------------|
| Day 1 | Patient profile CRUD (create on register, read, update) | Patient Dashboard page (layout, widgets) |
| Day 2 | Healthcare records endpoints (create consultation, list) | Personal Data Center (tabbed categories) |
| Day 3 | Prescriptions endpoints (create, dispense) | Doctor Dashboard + patient list |
| Day 4 | Consent service (grant, withdraw, enforce) | Consultation form UI |
| Day 5 | Consent enforcement (pre-access check, category filter) | Consent Center UI (6 cards, grant/withdraw) |
| Day 6 | Consent receipt generation | Pharmacy Dashboard + dispense form |
| Day 7 | Doctor consent-gated access + break-glass endpoint | Active sharing view + consent receipts |

**Week 2 Gate**: Full clinical workflow. Consent gates access. Grant/withdraw functional.

---

### Week 3: Encryption + Audit + Blockchain

| Day | Dev A (Backend) | Dev B (Frontend) |
|-----|-----------------|------------------|
| Day 1 | Encryption service (AES-256-GCM encrypt/decrypt) | Data Usage Timeline page (vertical timeline) |
| Day 2 | Per-patient key generation + key store | Timeline event cards + filter controls |
| Day 3 | Repository-level transparent encryption | Audit Logs page (DataTable, search, filters) |
| Day 4 | Audit service (auto-log every operation) + middleware | Blockchain transaction reference component |
| Day 5 | ConsentContract.sol + VerificationContract.sol + AuditContract.sol | Integrity Verification page (record list) |
| Day 6 | Contract deployment script + Web3.py blockchain service | Verified/Violation badge components |
| Day 7 | Auto-anchoring (consent events + record creates → blockchain) | Connect frontend to blockchain APIs |

**Week 3 Gate**: PII encrypted in DB. Every operation audited. Blockchain anchoring works (<10s).

---

### Week 4: Integrity + Integration + Deploy

| Day | Dev A (Backend) | Dev B (Frontend) |
|-----|-----------------|------------------|
| Day 1 | Integrity service (single verify + batch verify) | Wire integrity verification UI to backend |
| Day 2 | Audit hash anchoring + hash chain (previous_log_hash) | Loading skeletons, error boundaries |
| Day 3 | API integration testing (auth, consent, blockchain flows) | E2E testing (login → consent → access → verify) |
| Day 4 | Unit tests (services: auth, consent, encryption, blockchain) | Mobile responsive fixes |
| Day 5 | Smart contract tests + integrity verification tests | Final UI polish, empty states |
| Day 6 | Demo data seeding (5 patients, 2 doctors, 1 pharmacy) | Demo walkthrough testing |
| Day 7 | Docker production config + README + deploy verification | Final integration verification |

**Week 4 Gate**: System deployed via Docker. Full demo executable. Tests passing.

---

## 7. Integration Checkpoints

| Checkpoint | When | Verify |
|------------|------|--------|
| Auth flow | End of Week 1 | Frontend login → backend JWT → protected route access |
| Consent-gated access | Mid Week 2 | Doctor access denied without consent, granted with consent |
| Encryption roundtrip | Day 1 Week 3 | Write encrypted → read decrypted → data matches |
| Blockchain anchor | Day 6 Week 3 | Grant consent → verify ConsentContract has hash on-chain |
| Integrity verification | Day 1 Week 4 | Verify record → compare hash → green badge |
| Full workflow | Day 6 Week 4 | Register → consent → doctor access → verify → timeline shows event |

---

## 8. Key Technical Decisions (MVP)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Key storage | Separate MongoDB collection (encrypted) | HSM out of MVP scope; key isolation still enforced |
| Session management | JWT + server-side session ID in DB | Simpler than full session binding for MVP |
| Blockchain anchoring | Synchronous (within request) | Ganache instant mining makes async unnecessary |
| Audit log hashing | SHA-256 with previous_log_hash chain | Establishes integrity without full blockchain anchor on every log (batch anchor daily) |
| Consent enforcement | Middleware-level pre-access check | Consistent enforcement across all data routes |
| Break-glass | Simplified (justification + time limit, no DPO approval flow) | Full workflow in post-MVP |
| Rate limiting | Deferred to post-MVP | Lower priority for academic demo context |

---

## 9. Definition of Done (MVP)

| Criteria | Verification |
|----------|--------------|
| All 5 roles can register and login | Manual test |
| Patient views all personal data (decrypted) | UI displays correctly |
| Doctor creates consultation (consent-gated) | Access denied without consent, granted with |
| Pharmacy dispenses prescription (consent-gated) | Dispensing recorded with audit |
| Patient grants/withdraws consent (6 types) | Immediate access effect |
| All PII encrypted in MongoDB | Raw DB inspection shows ciphertext |
| Every operation produces audit log | Timeline shows all events |
| Consent + record hashes anchored on blockchain | Ganache contains transactions |
| Patient can verify record integrity | Green/red badge displays |
| System deploys with `docker-compose up` | Single command, all services healthy |
| 15-minute demo executable without errors | End-to-end walkthrough |
