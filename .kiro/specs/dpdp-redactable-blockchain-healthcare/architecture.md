# System Architecture

## DPDP Compliant Redactable Blockchain Based Healthcare and Pharmacy Management System

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                        │
│   React.js + TypeScript + Tailwind CSS + Shadcn UI (SPA)                        │
│   Role-Based Views: Patient | Doctor | Pharmacy | Admin | DPO | Guardian        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS / TLS 1.3
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                      │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐      │
│  │ Rate Limiter  │ │ JWT Validator │ │ Session Mgr   │ │ CORS / Helmet │      │
│  │ (Token Bucket)│ │ (RS256)      │ │ (Binding)     │ │ (Security Hdr)│      │
│  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER (Flask / Python)                           │
│                                                                                  │
│  ┌─── Blueprints (API Routing) ─────────────────────────────────────────────┐   │
│  │ auth │ patients │ consents │ doctors │ pharmacy │ audit │ blockchain     │   │
│  │ integrity │ dpo │ grievances │ processors │ notifications │ admin        │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─── Service Layer (Business Logic) ───────────────────────────────────────┐   │
│  │ AuthService         │ ConsentService       │ EncryptionService           │   │
│  │ BlockchainService   │ ChameleonHashService │ AuditService                │   │
│  │ BreachDetectorSvc   │ SessionService       │ RateLimitService            │   │
│  │ GrievanceService    │ ProcessorService     │ KeyEscrowService            │   │
│  │ NotificationService │ IntegrityService     │ VersionService              │   │
│  │ ResidencyService    │ PrivacyScoreService  │ MinorsProtectionService     │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─── Repository Layer (Data Access) ───────────────────────────────────────┐   │
│  │ UserRepo │ PatientRepo │ ConsentRepo │ AuditRepo │ SessionRepo           │   │
│  │ BlockchainRepo │ GrievanceRepo │ ProcessorRepo │ KeyRepo │ VersionRepo  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─── Middleware Pipeline ──────────────────────────────────────────────────┐   │
│  │ RequestID → RateLimit → JWT → Session → RBAC → AuditLog → Handler       │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │                    │                    │
                    ▼                    ▼                    ▼
┌────────────────────────┐ ┌─────────────────────┐ ┌────────────────────────────┐
│    DATA LAYER          │ │  BLOCKCHAIN LAYER   │ │    SECURITY LAYER          │
│                        │ │                     │ │                            │
│ ┌────────────────────┐ │ │ ┌─────────────────┐ │ │ ┌────────────────────────┐ │
│ │ MongoDB            │ │ │ │ Ganache Node    │ │ │ │ Chameleon Hash Engine  │ │
│ │ (Replica Set x3)  │ │ │ │ (Local Ethereum)│ │ │ │ CH(m,r)=g^m·y^r mod p │ │
│ │                    │ │ │ │                 │ │ │ └────────────────────────┘ │
│ │ - Patient Data     │ │ │ │ Smart Contracts:│ │ │                            │
│ │ - Health Records   │ │ │ │ - Consent.sol  │ │ │ ┌────────────────────────┐ │
│ │ - Consents         │ │ │ │ - Verify.sol   │ │ │ │ Encryption Engine      │ │
│ │ - Audit Logs       │ │ │ │ - Audit.sol    │ │ │ │ AES-256-GCM            │ │
│ │ - Sessions         │ │ │ │                 │ │ │ └────────────────────────┘ │
│ │ - Grievances       │ │ │ │ Web3.py Client │ │ │                            │
│ │ - Processors       │ │ │ └─────────────────┘ │ │ ┌────────────────────────┐ │
│ │ - Versions         │ │ │                     │ │ │ Key Management Store   │ │
│ └────────────────────┘ │ │ ┌─────────────────┐ │ │ │ + HSM Integration      │ │
│                        │ │ │ Backup Node     │ │ │ │ + Shamir Secret Share  │ │
│                        │ │ │ (India Region)  │ │ │ └────────────────────────┘ │
└────────────────────────┘ └─────────────────────┘ └────────────────────────────┘
```

---

## 2. Deployment Topology

### 2.1 Infrastructure Requirements

| Component | Specification | Location | Redundancy |
|-----------|--------------|----------|------------|
| Frontend CDN | Static assets (React build) | India edge nodes | Multi-region India |
| Flask Application | 2+ instances behind load balancer | India DC (Primary) | Active-Active |
| MongoDB | 3-node replica set | India DC | Primary + 2 Secondary |
| Ganache Node | Local Ethereum blockchain | India DC (Primary) | Primary + Backup |
| Key Management Store | Separate hardened server | India DC (Isolated) | HSM-backed |
| Backup Storage | Encrypted blockchain snapshots | India DC (Secondary region) | Cross-region |

### 2.2 Data Residency Enforcement

All infrastructure components are restricted to Indian data centers per DPDP Act requirements:
- MongoDB replica set nodes: India region only
- Ganache blockchain node: India region only
- Key Management Store with HSM: India region, physically isolated
- Backup replication: Within India, geographically separate data center
- CDN: India-region edge nodes only
- No data egress permitted without explicit DPO authorization

---

## 3. Component Communication Patterns

### 3.1 Synchronous Communication

| Source | Destination | Protocol | Auth Mechanism | Purpose |
|--------|-------------|----------|----------------|---------|
| Browser | API Gateway | HTTPS/TLS 1.3 | JWT Bearer Token | All API calls |
| Flask App | MongoDB | MongoDB Wire Protocol/TLS | X.509 Certificate | Data CRUD |
| Flask App | Ganache | JSON-RPC over HTTP | Signed Transactions (Private Key) | Smart contract calls |
| Flask App | Key Store | mTLS | Client Certificate | Key operations |
| Flask App | HSM | PKCS#11 | Hardware Token | Master key ops |

### 3.2 Internal Event Flow

```
User Action → Middleware Pipeline → Service Layer → Repository + Blockchain
                                         │
                                         ├── AuditService (every operation)
                                         ├── BlockchainService (hash anchoring)
                                         ├── NotificationService (alerts)
                                         └── BreachDetectorService (anomaly check)
```

### 3.3 Middleware Execution Order

```
1. RequestID Generation (correlation tracking)
2. Rate Limit Check (Token Bucket per role)
3. JWT Token Validation (signature, expiry, claims)
4. Session Binding Validation (IP, User-Agent, session state)
5. RBAC Permission Check (role × resource × action)
6. Request Body Validation (schema enforcement)
7. Audit Logging (pre-execution capture)
8. Route Handler Execution
9. Response Audit Logging (post-execution capture)
10. Response Headers (rate limit headers, security headers)
```

---

## 4. Application Layer Design

### 4.1 Flask Blueprint Organization

| Blueprint | URL Prefix | Description | Key Endpoints |
|-----------|-----------|-------------|---------------|
| `auth` | `/api/v1/auth` | Authentication, registration, MFA | login, register, refresh, logout |
| `patients` | `/api/v1/patients` | Patient data CRUD, download | profile, health-data, download, correct, delete |
| `consents` | `/api/v1/consents` | Consent lifecycle | grant, withdraw, modify, receipts, history |
| `doctors` | `/api/v1/doctors` | Doctor workflows | patients, consultations, break-glass |
| `pharmacy` | `/api/v1/pharmacy` | Pharmacy operations | prescriptions, dispense |
| `audit` | `/api/v1/audit` | Audit log access | logs, search, export |
| `blockchain` | `/api/v1/blockchain` | Blockchain operations | verify, transactions, status |
| `integrity` | `/api/v1/integrity` | Integrity verification | verify-record, batch-verify |
| `dpo` | `/api/v1/dpo` | DPO oversight | dashboard, redactions, compliance |
| `grievances` | `/api/v1/grievances` | Grievance workflow | submit, track, escalate |
| `processors` | `/api/v1/processors` | Processor management | register, audit, revoke |
| `notifications` | `/api/v1/notifications` | Notification management | list, mark-read, preferences |
| `admin` | `/api/v1/admin` | System administration | users, config, backup |

### 4.2 Service Layer Design Principles

1. **Single Responsibility**: Each service handles one domain concern
2. **Audit-by-Default**: Every service method triggers audit logging
3. **Encryption-Transparent**: Services work with plaintext; encryption handled at repository boundary
4. **Blockchain-Anchored**: All state-changing operations produce blockchain verification hashes
5. **Consent-Aware**: Data access services check consent before returning data

### 4.3 Cross-Cutting Concerns

| Concern | Implementation | Trigger |
|---------|---------------|---------|
| Audit Logging | AuditService called from middleware + service layer | Every request |
| Encryption/Decryption | EncryptionService at repository boundary | Data write/read |
| Blockchain Anchoring | BlockchainService from service layer | State changes |
| Consent Enforcement | ConsentService check before data access | Data retrieval |
| Breach Detection | BreachDetectorService analyzing access patterns | Periodic + per-request |
| Notification | NotificationService from service layer events | Consent/access/breach events |

---

## 5. Frontend Architecture

### 5.1 Application Shell

```
┌──────────────────────────────────────────────────────────────────┐
│  Header: Logo │ Platform Name │ Notifications │ Profile │ Logout │
├──────────┬───────────────────────────────────────────────────────┤
│          │                                                       │
│  Sidebar │              Main Content Area                        │
│  (Role-  │              (Route-based rendering)                  │
│  Based   │                                                       │
│  Nav)    │                                                       │
│          │                                                       │
│          │                                                       │
├──────────┴───────────────────────────────────────────────────────┤
│  Footer: DPDP Compliance Badge │ Data Residency │ Version        │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 State Management

| Store | Purpose | Technology |
|-------|---------|------------|
| Auth Store | User session, JWT, role | React Context + useReducer |
| Consent Store | Active consents, receipts | React Query (server state) |
| Notification Store | Real-time alerts | React Query + Polling (30s) |
| UI Store | Theme, sidebar, modals | React Context |

### 5.3 Role-Based Navigation

| Role | Primary Navigation Items |
|------|--------------------------|
| Patient | Dashboard, My Data, Consents, Timeline, Verify, Sharing, Grievances |
| Doctor | Dashboard, Patients, Consultations, Emergency Access |
| Pharmacy Staff | Dashboard, Prescriptions, Dispensing |
| Admin | Dashboard, Users, System Config, Backup, Chameleon Hash |
| DPO | Dashboard, Compliance, Breaches, Processors, Redactions, Grievances |
| Guardian | Dashboard, Minor's Data, Minor's Consents, Access Logs |

---

## 6. Folder Structure

### 6.1 Backend (Flask/Python)

```
backend/
├── app/
│   ├── __init__.py                    # Flask app factory
│   ├── config.py                      # Environment configuration
│   ├── extensions.py                  # MongoDB, Web3 init
│   ├── blueprints/
│   │   ├── __init__.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # Auth endpoints
│   │   │   └── schemas.py            # Request/response validation
│   │   ├── patients/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── consents/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── doctors/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── pharmacy/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── audit/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── blockchain/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── integrity/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── dpo/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── grievances/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── processors/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── notifications/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   └── admin/
│   │       ├── __init__.py
│   │       ├── routes.py
│   │       └── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── encryption_service.py
│   │   ├── consent_service.py
│   │   ├── blockchain_service.py
│   │   ├── chameleon_hash_service.py
│   │   ├── audit_service.py
│   │   ├── breach_service.py
│   │   ├── session_service.py
│   │   ├── rate_limit_service.py
│   │   ├── grievance_service.py
│   │   ├── processor_service.py
│   │   ├── key_escrow_service.py
│   │   ├── notification_service.py
│   │   ├── integrity_service.py
│   │   ├── version_service.py
│   │   ├── residency_service.py
│   │   ├── privacy_score_service.py
│   │   └── minors_service.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── patient_repository.py
│   │   ├── consent_repository.py
│   │   ├── audit_repository.py
│   │   ├── blockchain_repository.py
│   │   ├── session_repository.py
│   │   ├── grievance_repository.py
│   │   ├── processor_repository.py
│   │   ├── key_repository.py
│   │   └── version_repository.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth_middleware.py
│   │   ├── rate_limit_middleware.py
│   │   ├── session_middleware.py
│   │   ├── audit_middleware.py
│   │   ├── rbac_middleware.py
│   │   └── request_id_middleware.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── consent.py
│   │   ├── audit_log.py
│   │   ├── session.py
│   │   ├── grievance.py
│   │   ├── processor.py
│   │   ├── blockchain_ref.py
│   │   ├── chameleon_record.py
│   │   ├── notification.py
│   │   └── version.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── crypto.py
│   │   ├── validators.py
│   │   ├── constants.py
│   │   ├── errors.py
│   │   ├── decorators.py
│   │   └── helpers.py
│   └── contracts/
│       ├── ConsentContract.sol
│       ├── VerificationContract.sol
│       ├── AuditContract.sol
│       ├── compiled/                  # ABI + bytecode
│       └── deploy.py                  # Contract deployment script
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── property/                      # Property-based tests
│   └── conftest.py
├── migrations/
│   └── seed_data.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── run.py                             # Application entry point
```

### 6.2 Frontend (React/TypeScript)

```
frontend/
├── public/
│   ├── index.html
│   └── assets/
│       ├── icons/
│       └── images/
├── src/
│   ├── main.tsx                       # Entry point
│   ├── App.tsx                        # Root component + routing
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   └── MFAPage.tsx
│   │   ├── patient/
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── PersonalDataCenter.tsx
│   │   │   ├── ConsentCenter.tsx
│   │   │   ├── DataTimeline.tsx
│   │   │   ├── IntegrityVerification.tsx
│   │   │   ├── ActiveSharing.tsx
│   │   │   ├── AuditLogsPage.tsx
│   │   │   ├── GrievancePortal.tsx
│   │   │   └── VersionHistory.tsx
│   │   ├── doctor/
│   │   │   ├── DoctorDashboard.tsx
│   │   │   ├── PatientAccess.tsx
│   │   │   ├── ConsultationForm.tsx
│   │   │   └── EmergencyAccess.tsx
│   │   ├── pharmacy/
│   │   │   ├── PharmacyDashboard.tsx
│   │   │   ├── PrescriptionView.tsx
│   │   │   └── DispenseForm.tsx
│   │   ├── dpo/
│   │   │   ├── DPODashboard.tsx
│   │   │   ├── BreachCenter.tsx
│   │   │   ├── ProcessorManagement.tsx
│   │   │   ├── ChameleonHashView.tsx
│   │   │   ├── ComplianceReports.tsx
│   │   │   └── GrievanceManagement.tsx
│   │   ├── admin/
│   │   │   ├── AdminDashboard.tsx
│   │   │   ├── UserManagement.tsx
│   │   │   ├── BackupManagement.tsx
│   │   │   └── SystemConfig.tsx
│   │   ├── guardian/
│   │   │   ├── GuardianDashboard.tsx
│   │   │   └── MinorDataView.tsx
│   │   └── blockchain/
│   │       └── BlockchainExplorer.tsx
│   ├── components/
│   │   ├── ui/                        # Shadcn UI (auto-generated)
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── RoleBasedNav.tsx
│   │   ├── privacy/
│   │   │   ├── PrivacyScoreGauge.tsx
│   │   │   ├── ConsentCard.tsx
│   │   │   ├── IntegrityBadge.tsx
│   │   │   ├── DataCategoryChip.tsx
│   │   │   └── RetentionIndicator.tsx
│   │   ├── blockchain/
│   │   │   ├── TransactionRef.tsx
│   │   │   ├── HashComparison.tsx
│   │   │   ├── VerificationStatus.tsx
│   │   │   └── ChameleonVisual.tsx
│   │   ├── timeline/
│   │   │   ├── TimelineEvent.tsx
│   │   │   ├── TimelineFilter.tsx
│   │   │   └── TimelineSummary.tsx
│   │   ├── forms/
│   │   │   ├── ConsentForm.tsx
│   │   │   ├── GrievanceForm.tsx
│   │   │   ├── CorrectionForm.tsx
│   │   │   └── DeletionRequestForm.tsx
│   │   └── shared/
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── NotificationBell.tsx
│   │       └── ConfirmDialog.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useConsents.ts
│   │   ├── useBlockchain.ts
│   │   ├── useNotifications.ts
│   │   └── useAuditLogs.ts
│   ├── services/
│   │   ├── api.ts                     # Axios instance with interceptors
│   │   ├── authApi.ts
│   │   ├── patientApi.ts
│   │   ├── consentApi.ts
│   │   ├── blockchainApi.ts
│   │   ├── auditApi.ts
│   │   └── grievanceApi.ts
│   ├── store/
│   │   ├── AuthContext.tsx
│   │   └── UIContext.tsx
│   ├── types/
│   │   ├── user.ts
│   │   ├── consent.ts
│   │   ├── audit.ts
│   │   ├── blockchain.ts
│   │   ├── grievance.ts
│   │   └── api.ts
│   ├── utils/
│   │   ├── constants.ts
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── roleGuard.ts
│   └── styles/
│       └── globals.css                # Tailwind directives + custom
├── tailwind.config.ts
├── tsconfig.json
├── vite.config.ts
├── package.json
└── Dockerfile
```

---

## 7. Data Flow Patterns

### 7.1 Request Lifecycle (Standard Data Access)

```
Browser → HTTPS → API Gateway
  → Rate Limit Check (Token Bucket)
    → JWT Validation (signature + expiry)
      → Session Binding Check (IP + UA + concurrency)
        → RBAC Permission Check (role × resource)
          → Consent Verification (purpose × data category)
            → Service Layer (business logic)
              → Repository Layer (MongoDB read)
                → Encryption Engine (AES-256-GCM decrypt)
                  → Audit Log Generation
                    → Blockchain Hash Anchor (async, <10s)
                      → Response to Client
```

### 7.2 Blockchain Anchoring Pattern (Asynchronous)

```
State Change Event
  → Service completes operation
  → Compute SHA-256 hash of operation record
  → Queue blockchain anchor request
  → Web3.py sends transaction to Smart Contract
  → Contract emits event with hash + timestamp
  → Store transaction reference in MongoDB
  → SLA: Complete within 10 seconds
```

### 7.3 Chameleon Hash Collision Flow

```
Authorized Correction/Erasure Request
  → DPO/Admin multi-factor authentication
  → Verify authorization (Compliance_Personnel role)
  → Retrieve original: CH(m, r) = g^m · y^r mod p
  → Compute modified message m'
  → Using trapdoor key (sk): compute r' such that CH(m, r) = CH(m', r')
  → Store new (m', r') pair
  → Blockchain chain remains valid (same hash output)
  → Record collision in audit log
  → Archive previous version (encrypted)
```

### 7.4 Breach Detection Pattern

```
Every Request → BreachDetector Analysis
  ├── Check: IP recognized? (geo-fence India)
  ├── Check: Access within authorized hours?
  ├── Check: Data categories within consent scope?
  ├── Check: Request rate < threshold?
  └── Check: Session anomalies?
      │
      ├── Normal → Continue
      └── Anomaly Detected → Generate Incident Alert
          → Notify DPO (< 30 seconds)
          → Notify Affected Data_Principal (< 60 seconds)
          → Create incident record
          → Blockchain-anchor breach trail
```

---

## 8. Integration Points

### 8.1 External Integrations

| Integration | Purpose | Protocol | Notes |
|-------------|---------|----------|-------|
| HSM | Master key protection | PKCS#11 | Hardware-bound keys |
| Email Service | Notifications, alerts | SMTP/API | Breach alerts, consent expiry |
| PDF Generator | Consent receipts | Library (ReportLab) | In-process |

### 8.2 Internal Subsystem Dependencies

```
AuthService ──────────→ SessionService
     │                       │
     ▼                       ▼
ConsentService ────→ BlockchainService ←── IntegrityService
     │                       │
     ▼                       ▼
AuditService ←──── ChameleonHashService
     │
     ▼
BreachDetectorService ──→ NotificationService
```

---

## 9. Scalability Considerations

### 9.1 Horizontal Scaling

| Component | Scaling Strategy | Constraint |
|-----------|-----------------|------------|
| Flask App | Multiple instances behind load balancer | Stateless (session in DB) |
| MongoDB | Replica set (read scaling) + sharding (future) | Data residency: India only |
| Ganache | Single primary + backup (academic scope) | Local network |
| Rate Limiter | Shared counter (MongoDB-based for multi-instance) | Distributed consistency |

### 9.2 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p95) | < 500ms | All endpoints except blockchain |
| Blockchain Anchor Time | < 10 seconds | Hash storage SLA |
| Consent Revocation | < 5 seconds | Access removal |
| Batch Integrity Verification | < 60 seconds | All patient records |
| Data Export | < 30 seconds | Full patient data JSON |

---

## 10. Resilience and Recovery

### 10.1 Failure Modes

| Failure | Impact | Mitigation |
|---------|--------|------------|
| MongoDB primary down | Write unavailable | Auto-failover to secondary (replica set) |
| Ganache node crash | Blockchain writes fail | Backup node activation (RTO: 4h) |
| HSM unavailable | New key ops blocked | Cached operational keys (limited window) |
| Key Store down | Encryption/decryption fails | Graceful degradation, DPO alert |
| Network partition | Blockchain anchoring delayed | Queue with retry (10s SLA relaxed to 60s) |

### 10.2 Backup Schedule

| Data | Frequency | RPO | RTO | Location |
|------|-----------|-----|-----|----------|
| MongoDB | Continuous replication | 0 (replica) | < 30 min | India (3 sites) |
| Blockchain State | Every 1000 blocks or 24h | 1 hour | 4 hours | India (2 regions) |
| Encryption Keys | On every key event | 0 (synchronous) | 2 hours | Separate infra |
| Audit Logs | Continuous + daily export | 0 (replica) | < 30 min | India (3 sites) |

---

## 11. Technology Stack Summary

| Layer | Technology | Version (Target) | Purpose |
|-------|-----------|-------------------|---------|
| Frontend Framework | React.js | 18.x | UI rendering |
| Language (FE) | TypeScript | 5.x | Type safety |
| CSS Framework | Tailwind CSS | 3.x | Utility-first styling |
| Component Library | Shadcn UI | Latest | Professional components |
| Build Tool | Vite | 5.x | Fast builds |
| Backend Framework | Flask | 3.x | REST API server |
| Language (BE) | Python | 3.11+ | Backend logic |
| Database | MongoDB | 7.x | Document storage |
| ODM | PyMongo | 4.x | MongoDB interaction |
| Blockchain | Ethereum (Ganache) | Latest | Local blockchain |
| Smart Contracts | Solidity | 0.8.x | On-chain logic |
| Web3 Client | Web3.py | 6.x | Blockchain interaction |
| Encryption | PyCryptodome | 3.x | AES-256-GCM |
| Authentication | PyJWT | 2.x | Token management |
| Password Hashing | bcrypt | 4.x | Credential storage |
| Testing | pytest + Hypothesis | Latest | Unit + property-based |
| Containerization | Docker + Docker Compose | Latest | Development environment |
