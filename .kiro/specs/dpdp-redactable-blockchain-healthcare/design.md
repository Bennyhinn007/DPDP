# Technical Design Document

## DPDP Compliant Redactable Blockchain Based Healthcare and Pharmacy Management System

---

## 1. System Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  React.js + TypeScript + Tailwind CSS + Shadcn UI                   │    │
│  │  (SPA with Role-Based Views)                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │ HTTPS/TLS 1.3
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Rate Limiter │  │ JWT Validator│  │Session Mgr   │  │ CORS/Headers │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER (Flask)                              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ Auth       │ │ Patient    │ │ Consent    │ │ Blockchain │              │
│  │ Blueprint  │ │ Blueprint  │ │ Blueprint  │ │ Blueprint  │              │
│  ├────────────┤ ├────────────┤ ├────────────┤ ├────────────┤              │
│  │ Doctor     │ │ Pharmacy   │ │ Audit      │ │ DPO        │              │
│  │ Blueprint  │ │ Blueprint  │ │ Blueprint  │ │ Blueprint  │              │
│  ├────────────┤ ├────────────┤ ├────────────┤ ├────────────┤              │
│  │ Grievance  │ │ Processor  │ │ Notification│ │ Integrity │              │
│  │ Blueprint  │ │ Blueprint  │ │ Blueprint  │ │ Blueprint  │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        SERVICE LAYER                                  │   │
│  │  AuthService │ ConsentService │ EncryptionService │ BlockchainService│   │
│  │  AuditService│ ChameleonHashService│ BreachDetector│ SessionService  │   │
│  │  GrievanceService│ ProcessorService│ NotificationService│ KeyEscrow  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      REPOSITORY LAYER                                 │   │
│  │  UserRepo│PatientRepo│ConsentRepo│AuditRepo│BlockchainRepo│SessionRepo│  │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                          │                              │
                          ▼                              ▼
┌──────────────────────────────────┐  ┌──────────────────────────────────────┐
│        DATA LAYER                 │  │       BLOCKCHAIN LAYER                │
│  ┌────────────────────────────┐  │  │  ┌────────────────────────────────┐  │
│  │   MongoDB (Encrypted)      │  │  │  │  Ganache (Local Ethereum)      │  │
│  │   - Patient Data           │  │  │  │  - ConsentContract.sol         │  │
│  │   - Health Records         │  │  │  │  - VerificationContract.sol    │  │
│  │   - Consents               │  │  │  │  - AuditContract.sol           │  │
│  │   - Audit Logs             │  │  │  │                                │  │
│  │   - Sessions               │  │  │  │  Web3.py Integration           │  │
│  │   - Grievances             │  │  │  └────────────────────────────────┘  │
│  └────────────────────────────┘  │  └──────────────────────────────────────┘
│                                   │
│  ┌────────────────────────────┐  │  ┌──────────────────────────────────────┐
│  │  Key Management Store      │  │  │     SECURITY LAYER                    │
│  │  (Separate Infrastructure) │  │  │  ┌──────────────────────────────┐    │
│  │  - AES-256 Keys            │  │  │  │  Chameleon Hash Engine        │    │
│  │  - HSM Integration         │  │  │  │  CH(m,r) = g^m · y^r mod p   │    │
│  │  - Shamir Shares           │  │  │  └──────────────────────────────┘    │
│  └────────────────────────────┘  │  │  ┌──────────────────────────────┐    │
└──────────────────────────────────┘  │  │  Breach Detection Engine      │    │
                                       │  └──────────────────────────────┘    │
                                       └──────────────────────────────────────┘
```

### 1.2 Deployment Topology

- **All infrastructure deployed within Indian data centers** (DPDP Act compliance)
- Frontend: Static assets served via CDN (India-region)
- Backend: Flask application server (2+ instances for availability)
- Database: MongoDB replica set (3 nodes, India region)
- Blockchain: Ganache node (primary + backup within India)
- Key Store: Separate hardened infrastructure with HSM
- Backup: Cross-region replication within India

### 1.3 Communication Patterns

| From | To | Protocol | Security |
|------|-----|----------|----------|
| Client | API Gateway | HTTPS/TLS 1.3 | JWT Bearer Token |
| API Gateway | Flask App | Internal HTTP | Session validation |
| Flask App | MongoDB | MongoDB Wire Protocol | TLS + Auth |
| Flask App | Ganache | JSON-RPC | Signed transactions |
| Flask App | Key Store | mTLS | Certificate auth |
| Flask App | HSM | PKCS#11 | Hardware-bound |

---

## 2. Component Architecture

### 2.1 Frontend Architecture (React + TypeScript)

#### Page Components

| Page | Route | Role Access | Description |
|------|-------|-------------|-------------|
| LoginPage | `/login` | Public | Authentication with MFA |
| RegisterPage | `/register` | Public | Patient registration with age verification |
| PatientDashboard | `/dashboard` | Patient | Health summary, privacy score, notifications |
| PersonalDataCenter | `/my-data` | Patient | View/edit/download personal data |
| ConsentCenter | `/consents` | Patient | Manage all consent types |
| DataTimeline | `/timeline` | Patient | Visual data access timeline |
| IntegrityVerification | `/verify` | Patient | Blockchain hash verification |
| AuditLogs | `/audit-logs` | Patient, DPO | Searchable audit history |
| ActiveSharing | `/sharing` | Patient | Real-time data sharing view |
| GrievancePortal | `/grievances` | Patient | Submit and track grievances |
| GuardianDashboard | `/guardian` | Guardian | Manage minor's data |
| DoctorDashboard | `/doctor` | Doctor | Patient access, consultations |
| PharmacyDashboard | `/pharmacy` | Pharmacy Staff | Prescription dispensing |
| DPODashboard | `/dpo` | DPO | Compliance oversight |
| AdminDashboard | `/admin` | Admin | System management |
| BreachCenter | `/dpo/breaches` | DPO | Incident management |
| ProcessorManagement | `/dpo/processors` | DPO | Third-party oversight |
| ChameleonHashView | `/dpo/chameleon` | DPO, Admin | Redaction operations |
| BlockchainExplorer | `/blockchain` | All authenticated | Transaction verification |

#### Shared Components

```
components/
├── ui/                          # Shadcn UI components
│   ├── Button, Card, Dialog, Badge, Table, Tabs, Toast
│   ├── DataTable (sortable, filterable, paginated)
│   └── Timeline (vertical event timeline)
├── layout/
│   ├── AppShell (sidebar + header + content)
│   ├── RoleBasedNav (dynamic navigation per role)
│   └── NotificationBell (real-time notifications)
├── privacy/
│   ├── PrivacyScoreGauge (0-100 visual meter)
│   ├── ConsentCard (consent status with actions)
│   ├── IntegrityBadge (green/red verification status)
│   └── DataCategoryChip (visual category indicator)
├── blockchain/
│   ├── TransactionReference (clickable tx hash display)
│   ├── HashComparison (traditional vs chameleon visual)
│   └── VerificationStatus (animated check/alert)
├── timeline/
│   ├── TimelineEvent (individual event card)
│   ├── TimelineFilter (date, type, actor filters)
│   └── TimelineSummary (aggregate statistics)
└── forms/
    ├── ConsentForm (grant/modify with scope selection)
    ├── GrievanceForm (submission with category)
    ├── CorrectionForm (field edit with reason)
    └── DeletionRequestForm (category selection + MFA)
```

### 2.2 Backend Architecture (Flask)

#### Blueprint Organization

```python
# Flask application factory pattern
app/
├── __init__.py              # create_app() factory
├── config.py                # Environment configuration
├── extensions.py            # MongoDB, Web3 initialization
├── blueprints/
│   ├── auth/                # Authentication & registration
│   ├── patients/            # Patient data operations
│   ├── consents/            # Consent management
│   ├── doctors/             # Doctor workflow
│   ├── pharmacy/            # Pharmacy workflow
│   ├── audit/               # Audit log access
│   ├── blockchain/          # Blockchain verification
│   ├── integrity/           # Integrity verification
│   ├── dpo/                 # DPO oversight operations
│   ├── grievances/          # Grievance handling
│   ├── processors/          # Third-party processor mgmt
│   ├── notifications/       # Notification management
│   └── admin/               # Admin operations
├── services/
│   ├── auth_service.py      # JWT, RBAC, MFA
│   ├── encryption_service.py # AES-256-GCM operations
│   ├── consent_service.py   # Consent lifecycle
│   ├── blockchain_service.py # Web3.py interactions
│   ├── chameleon_hash_service.py # CH(m,r) implementation
│   ├── audit_service.py     # Audit log generation
│   ├── breach_service.py    # Breach detection
│   ├── session_service.py   # Session management
│   ├── rate_limit_service.py # Rate limiting
│   ├── grievance_service.py # Grievance workflow
│   ├── processor_service.py # Processor management
│   ├── key_escrow_service.py # Shamir's Secret Sharing
│   ├── notification_service.py # Notification dispatch
│   ├── integrity_service.py # Hash comparison
│   ├── version_service.py   # Version history
│   └── residency_service.py # Data localization
├── repositories/
│   ├── user_repository.py
│   ├── patient_repository.py
│   ├── consent_repository.py
│   ├── audit_repository.py
│   ├── blockchain_repository.py
│   ├── session_repository.py
│   ├── grievance_repository.py
│   └── processor_repository.py
├── middleware/
│   ├── auth_middleware.py   # JWT validation
│   ├── rate_limit_middleware.py # Request throttling
│   ├── session_middleware.py # Session validation
│   ├── audit_middleware.py  # Automatic audit logging
│   └── rbac_middleware.py   # Permission checking
├── models/
│   ├── user.py, patient.py, consent.py, audit_log.py
│   ├── grievance.py, processor.py, session.py
│   └── blockchain_ref.py, chameleon_record.py
└── utils/
    ├── crypto.py            # Encryption utilities
    ├── validators.py        # Input validation
    ├── constants.py         # System constants
    └── errors.py            # Custom exceptions
```

### 2.3 Service Layer Responsibilities

| Service | Responsibility | Dependencies |
|---------|---------------|--------------|
| AuthService | JWT issuance, RBAC enforcement, MFA, account lockout | MongoDB, SessionService |
| EncryptionService | AES-256-GCM encrypt/decrypt, key rotation | Key Store, HSM |
| ConsentService | Grant/withdraw/modify consent, receipt generation | MongoDB, BlockchainService, AuditService |
| BlockchainService | Web3.py interaction, contract calls, tx management | Ganache, Smart Contracts |
| ChameleonHashService | CH(m,r) computation, collision generation, trapdoor mgmt | Blockchain, Audit |
| AuditService | Log generation, blockchain anchoring, search | MongoDB, BlockchainService |
| BreachService | Pattern detection, incident creation, alerting | AuditService, NotificationService |
| SessionService | Session creation/validation/termination | MongoDB (sessions collection) |
| RateLimitService | Token bucket per user/role, DDoS detection | Redis-like in-memory counter |
| GrievanceService | Submission, escalation, SLA tracking | MongoDB, NotificationService |
| ProcessorService | Registration, DPA tracking, access control | MongoDB, BlockchainService |
| KeyEscrowService | Shamir split/reconstruct, HSM operations | Key Store, HSM |
| IntegrityService | Hash computation, blockchain comparison | BlockchainService |
| VersionService | Version creation, history retrieval | MongoDB, BlockchainService |

---

## 3. Database Schema (MongoDB Collections)

### 3.1 users
