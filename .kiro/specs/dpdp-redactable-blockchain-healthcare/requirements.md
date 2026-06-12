# Requirements Document

## Introduction

This document specifies the requirements for a DPDP (Digital Personal Data Protection Act, India) compliant healthcare and pharmacy management platform. The system employs a redactable blockchain architecture utilizing Chameleon Hashing to enable authorized collision generation preserving blockchain verification consistency while supporting lawful correction and erasure operations. Patients (Data Principals) retain full sovereignty over their personal and health data through consent management, data access transparency, integrity verification, and enforceable rights to access, correction, and erasure.

The platform is designed for enterprise-grade healthcare environments requiring government-level compliance, cryptographic auditability, and zero-trust data governance.

## Glossary

- **Platform**: The DPDP Compliant Redactable Blockchain Based Healthcare and Pharmacy Management System
- **Data_Principal**: A patient whose personal data is processed by the Platform (as defined by DPDP Act Section 2(j))
- **Data_Fiduciary**: The healthcare organization that determines the purpose and means of processing personal data (as defined by DPDP Act Section 2(i))
- **DPO**: Data Protection Officer responsible for overseeing DPDP compliance, breach management, and redaction authorization
- **Compliance_Personnel**: Authorized individuals including the DPO and approved auditors who may access compliance archives and redaction history
- **Consent_Manager**: The subsystem responsible for recording, tracking, enforcing, and generating receipts for consent decisions
- **Blockchain_Layer**: The Ethereum-based subsystem (deployed on Ganache) that stores verification hashes for consent, audit logs, and records via Solidity Smart Contracts
- **Chameleon_Hash_Engine**: The subsystem implementing authorized collision generation via Chameleon Hashing (CH(m,r) = g^m · y^r mod p) for redactable blockchain operations, preserving blockchain verification consistency while supporting lawful correction and erasure
- **Encryption_Engine**: The subsystem responsible for AES-256 encryption, decryption, and cryptographic key lifecycle management
- **Audit_Logger**: The subsystem that generates immutable, blockchain-anchored audit log entries for every data operation
- **Integrity_Verifier**: The subsystem that compares current record hashes against blockchain-stored hashes to detect unauthorized modifications
- **Breach_Detector**: The subsystem responsible for detecting unauthorized access patterns, generating breach alerts, and managing security incident workflows
- **Auth_Service**: The subsystem responsible for JWT-based authentication, role-based access control, and identity verification
- **Personal_Data_Center**: The interface where Data Principals view, edit, correct, request deletion, and download their personal and health data
- **Version_Store**: The subsystem that maintains complete version history for all personal and healthcare records with blockchain verification references
- **RBAC**: Role-Based Access Control governing access permissions for Patient, Doctor, Pharmacy Staff, Admin, and DPO roles
- **Smart_Contract**: A Solidity-based contract deployed on Ethereum (Ganache) that enforces consent, verification, or audit logic on-chain
- **Break_Glass_Access**: Emergency access protocol allowing time-limited override of consent restrictions for healthcare emergencies with mandatory justification and full audit logging
- **Consent_Receipt**: A verifiable document generated for every consent action containing unique identifier, purpose, scope, timestamp, expiry, and blockchain transaction reference
- **Privacy_Score**: A computed metric (0-100) reflecting the Data_Principal's data protection posture based on active consents, encryption coverage, and data minimization level
- **Session_Manager**: The subsystem responsible for secure session lifecycle management, concurrent session controls, and session security enforcement
- **Rate_Limiter**: The API gateway component that enforces request rate limits per role and endpoint, providing DDoS protection and graduated throttling
- **Grievance_Handler**: The subsystem managing DPDP Act grievance redressal workflows including submission, acknowledgment, escalation, and resolution tracking
- **Processor_Registry**: The subsystem tracking third-party data processors, their agreements, access permissions, and compliance status
- **Key_Escrow**: The secure key backup subsystem implementing Shamir's Secret Sharing for encryption key recovery with multi-party authorization
- **Data_Residency_Controller**: The subsystem enforcing data localization within Indian jurisdiction, verifying storage compliance, and managing cross-border transfer controls
- **Guardian**: The parent or legal guardian of a minor Data_Principal who provides verifiable consent and manages the minor's data on the Platform
- **HSM**: Hardware Security Module used for master key protection and cryptographic operations requiring tamper-resistant hardware

## Requirements

### Requirement 1: Patient Registration and Authentication

**User Story:** As a Data_Principal, I want to register and securely authenticate, so that I can access my healthcare data and manage my privacy preferences.

#### Acceptance Criteria

1. WHEN a new user submits registration details, THE Auth_Service SHALL create a Data_Principal account with a unique identifier, hashed password (bcrypt with cost factor 12), and default consent preferences set to deny-all
2. WHEN a registered Data_Principal submits valid credentials, THE Auth_Service SHALL issue a JWT token with a maximum validity of 24 hours containing the user role and account identifier
3. IF invalid credentials are submitted more than 5 times within 15 minutes, THEN THE Auth_Service SHALL lock the account for 30 minutes and notify the Data_Principal via registered email
4. THE Auth_Service SHALL enforce RBAC with five roles: Patient (Data_Principal), Doctor, Pharmacy Staff, Healthcare Organization Admin, and Data Protection Officer
5. WHEN a JWT token expires, THE Auth_Service SHALL reject all subsequent requests with HTTP 401 and require re-authentication
6. WHEN a Data_Principal registers, THE Audit_Logger SHALL record the registration event with timestamp, assigned identifier, and consent defaults

### Requirement 2: Personal Data Storage and Encryption

**User Story:** As a Data_Principal, I want my personal and health data encrypted at rest, so that unauthorized access to the database does not expose sensitive information.

#### Acceptance Criteria

1. THE Encryption_Engine SHALL encrypt all personal information, contact information, identity information, medical history, allergies, prescriptions, lab reports, and healthcare records using AES-256-GCM before storage in MongoDB
2. WHEN a Data_Principal or authorized user requests data retrieval, THE Encryption_Engine SHALL decrypt the requested data using the corresponding encryption key and verify the GCM authentication tag
3. THE Encryption_Engine SHALL store encryption keys in a dedicated key management store separate from the MongoDB database containing encrypted data
4. IF decryption fails due to key mismatch, tag verification failure, or key corruption, THEN THE Encryption_Engine SHALL log the failure with record identifier and failure reason, deny access, and alert the DPO within 60 seconds
5. THE Encryption_Engine SHALL rotate encryption keys every 90 days and re-encrypt affected records within 24 hours of rotation
6. THE Encryption_Engine SHALL generate a unique encryption key per Data_Principal to limit blast radius of key compromise

### Requirement 3: Personal Data Center - View and Download

**User Story:** As a Data_Principal, I want to view all my stored personal and health data categorized by type, so that I have full transparency into what information the Platform holds about me.

#### Acceptance Criteria

1. WHEN a Data_Principal accesses the Personal_Data_Center, THE Platform SHALL display all stored personal data organized by categories: Personal Information, Contact Information, Identity Information, Medical History, Allergies, Prescriptions, Lab Reports, and Healthcare Records
2. THE Platform SHALL display the data retention status and retention period remaining for each data category
3. WHEN a Data_Principal requests a data download, THE Platform SHALL generate a machine-readable export (JSON format) containing all personal and health data within 30 seconds
4. THE Platform SHALL display the last modification date, modification source, and blockchain verification reference for each data field
5. WHEN a Data_Principal views a data category, THE Audit_Logger SHALL record the view event with Data_Principal identifier, category viewed, and timestamp

### Requirement 4: Personal Data Correction

**User Story:** As a Data_Principal, I want to correct inaccurate personal data, so that my health records reflect accurate information as guaranteed by the DPDP Act.

#### Acceptance Criteria

1. WHEN a Data_Principal submits a correction request for a data field, THE Platform SHALL update the field value and store the previous value in the Version_Store with a correction reason
2. WHEN a correction is applied, THE Audit_Logger SHALL record the correction with actor identity, timestamp, field identifier, previous value hash, new value hash, and stated reason
3. WHEN a correction is applied, THE Chameleon_Hash_Engine SHALL perform authorized collision generation to compute an updated hash that reflects the corrected data while preserving blockchain verification consistency
4. WHEN a correction is applied, THE Blockchain_Layer SHALL store the new verification hash on-chain within 10 seconds and return the transaction reference
5. WHEN a correction is applied, THE Version_Store SHALL record: previous value, updated value, modified by, timestamp, reason for modification, and blockchain verification reference

### Requirement 5: Right to Erasure

**User Story:** As a Data_Principal, I want to request deletion of my personal data, so that the Platform removes my information as guaranteed by the DPDP Act.

#### Acceptance Criteria

1. WHEN a Data_Principal submits a deletion request, THE Auth_Service SHALL verify the identity of the requester through multi-factor authentication before proceeding
2. WHEN identity is verified, THE Audit_Logger SHALL create an audit entry documenting the deletion request with requester identity, timestamp, affected data categories, and legal basis
3. WHEN the audit entry is created, THE Chameleon_Hash_Engine SHALL redact the specified data fields and perform authorized collision generation to maintain blockchain verification consistency
4. WHEN redaction is complete, THE Blockchain_Layer SHALL record the redaction proof on-chain with transaction reference
5. WHEN redaction is complete, THE Platform SHALL preserve the audit trail documenting that data existed and was lawfully deleted, without exposing the deleted content
6. THE Platform SHALL complete the full erasure workflow within 72 hours of request submission
7. WHEN erasure is complete, THE Platform SHALL notify the Data_Principal with a confirmation containing the erasure timestamp and affected categories
8. THE Platform SHALL propagate erasure to all downstream data sharing recipients within 72 hours

### Requirement 6: Consent Management

**User Story:** As a Data_Principal, I want to grant, modify, and withdraw consent for specific data processing purposes, so that I maintain control over how my data is used.

#### Acceptance Criteria

1. THE Consent_Manager SHALL support six consent types: Healthcare Treatment, Pharmacy Access, Research Access, Insurance Access, Analytics Access, and Marketing Access
2. WHEN a Data_Principal grants consent, THE Consent_Manager SHALL record the consent purpose, data categories in scope, grant date, expiry date, and processing entity
3. WHEN a Data_Principal withdraws consent, THE Consent_Manager SHALL immediately revoke data access for the specified purpose, record the withdrawal timestamp, and notify affected data processors within 60 seconds
4. WHEN consent is granted or withdrawn, THE Blockchain_Layer SHALL store a consent hash on-chain as immutable proof and return the transaction reference
5. WHEN consent expires, THE Consent_Manager SHALL automatically revoke access for the expired consent type and notify the Data_Principal 7 days before expiry and on the expiry date
6. THE Consent_Manager SHALL display for each consent: purpose, current status, expiry date, access scope, processing entity, and blockchain transaction reference
7. WHEN a Data_Principal modifies consent scope, THE Consent_Manager SHALL record the modification with previous scope, new scope, modification timestamp, and reason

### Requirement 7: Consent Receipts

**User Story:** As a Data_Principal, I want to receive a verifiable receipt for every consent action, so that I have proof of my consent decisions.

#### Acceptance Criteria

1. WHEN any consent action (grant, modify, or withdraw) is performed, THE Consent_Manager SHALL generate a Consent_Receipt with a unique Consent ID (UUID v4)
2. THE Consent_Receipt SHALL contain: Consent ID, Data_Principal identifier, consent purpose, data categories in scope, action type (grant/modify/withdraw), timestamp, expiry date, and blockchain transaction reference
3. WHEN a Consent_Receipt is generated, THE Blockchain_Layer SHALL store the receipt hash on-chain within 10 seconds
4. WHEN a Data_Principal requests a consent receipt download, THE Platform SHALL provide the receipt in PDF format containing all receipt fields and a QR code linking to the blockchain transaction
5. THE Platform SHALL maintain a searchable history of all Consent_Receipts for each Data_Principal

### Requirement 8: Active Data Sharing Dashboard

**User Story:** As a Data_Principal, I want to see a real-time view of who currently has access to my data, why, what categories, and when access expires, so that I can revoke access instantly if needed.

#### Acceptance Criteria

1. WHEN a Data_Principal accesses the Active Data Sharing Dashboard, THE Platform SHALL display all entities currently authorized to access the Data_Principal's data
2. THE Platform SHALL display for each authorized entity: entity name, role, access reason (consent purpose), data categories accessible, access grant date, and access expiry date
3. WHEN a Data_Principal selects an entity and requests instant revocation, THE Consent_Manager SHALL revoke access for that entity within 5 seconds and record the revocation event
4. THE Platform SHALL update the Active Data Sharing Dashboard in real-time when consent changes occur
5. THE Platform SHALL visually distinguish between active, expiring-soon (within 7 days), and expired access entries

### Requirement 9: Data Access Transparency and Usage Timeline

**User Story:** As a Data_Principal, I want to see who accessed my data, when, why, and what was accessed, so that I have full transparency into data usage.

#### Acceptance Criteria

1. WHEN any user accesses a Data_Principal's data, THE Audit_Logger SHALL record the accessor identity, accessor role, timestamp, stated reason for access, data category accessed, and access duration
2. WHEN a Data_Principal views the Data Usage Timeline, THE Platform SHALL display access events in reverse chronological order with actor name, actor role, timestamp, reason, and data category
3. THE Platform SHALL support filtering access events by date range, accessor role, data category, and action type
4. THE Platform SHALL display the Data Usage Timeline in a visual card-based format similar to a banking transaction history with color-coded event categories
5. THE Platform SHALL display the total number of access events per time period (daily, weekly, monthly) as summary statistics

### Requirement 10: Personal Data Journey Timeline

**User Story:** As a Data_Principal, I want to see a complete visual timeline of my data lifecycle events, so that I can understand the full history of actions taken on my data.

#### Acceptance Criteria

1. THE Platform SHALL display a Personal Data Journey Timeline showing all lifecycle events in chronological order: registration, consent creation, data access, data sharing, record modification, consent withdrawal, erasure requests, integrity verification, and audit events
2. THE Platform SHALL render the Personal Data Journey Timeline as a vertical visual timeline with event icons, timestamps, actor details, and event descriptions similar to a banking transaction timeline
3. WHEN a Data_Principal selects a timeline event, THE Platform SHALL display full event details including blockchain verification reference
4. THE Platform SHALL support filtering the timeline by event type, date range, and involved actor
5. THE Platform SHALL display the timeline with color-coded event categories distinguishing consent events, access events, modification events, security events, and verification events

### Requirement 11: Immutable Audit Logging

**User Story:** As a DPO, I want every data action to generate an immutable audit log entry, so that the organization can demonstrate DPDP compliance.

#### Acceptance Criteria

1. THE Audit_Logger SHALL generate an audit log entry for every data creation, read, update, deletion, consent change, access event, breach event, and emergency access event
2. THE Audit_Logger SHALL record for each entry: actor identity, actor role, timestamp, action type, reason, affected data fields, source IP address, and blockchain reference hash
3. WHEN an audit log entry is created, THE Blockchain_Layer SHALL store the log hash on-chain within 10 seconds and return the transaction reference
4. THE Audit_Logger SHALL provide search and filter capabilities by actor, actor role, action type, date range, affected data category, and severity level
5. IF any audit log entry is modified after creation, THEN THE Integrity_Verifier SHALL detect the modification and flag the entry as compromised within 60 seconds
6. THE Audit_Logger SHALL retain all audit entries for a minimum of 8 years in compliance with healthcare record retention requirements

### Requirement 12: Blockchain Integrity Verification

**User Story:** As a Data_Principal, I want to verify the integrity of my records against blockchain-stored hashes, so that I can detect unauthorized modifications.

#### Acceptance Criteria

1. WHEN a Data_Principal requests integrity verification for a record, THE Integrity_Verifier SHALL compute the current hash of the record and compare it against the blockchain-stored hash
2. WHEN hashes match, THE Integrity_Verifier SHALL display a green "Verified" status indicator with the verification timestamp and blockchain transaction reference
3. WHEN hashes do not match, THE Integrity_Verifier SHALL display a red "Integrity Violation Detected" status indicator, alert the DPO within 30 seconds, and notify the Data_Principal
4. THE Blockchain_Layer SHALL store only verification hashes (consent hashes, audit log hashes, record verification hashes) and never store medical data directly on-chain
5. THE Platform SHALL provide a blockchain verification screen showing the on-chain transaction reference, block number, and timestamp for each stored hash
6. THE Platform SHALL support batch integrity verification allowing a Data_Principal to verify all records simultaneously

### Requirement 13: Chameleon Hashing for Redactable Blockchain

**User Story:** As a DPO, I want the blockchain to support authorized collision generation preserving blockchain verification consistency, so that the organization can fulfill right-to-erasure and correction requests without invalidating the chain.

#### Acceptance Criteria

1. THE Chameleon_Hash_Engine SHALL implement the Chameleon Hash function CH(m,r) = g^m · y^r mod p where g is the generator, m is the message, r is the randomness, y is the public key, and p is the prime modulus
2. WHEN a correction or erasure is authorized, THE Chameleon_Hash_Engine SHALL compute a new randomness value r' such that CH(m,r) = CH(m',r') for the modified message m', maintaining blockchain chain validity through authorized collision generation
3. THE Chameleon_Hash_Engine SHALL restrict collision generation to authorized Compliance_Personnel (DPO and Healthcare Organization Admin) after identity verification
4. THE Platform SHALL display a comparison view showing Traditional Hash behavior (any modification invalidates the chain) versus Chameleon Hash behavior (authorized modifications preserve chain validity) for educational transparency
5. WHEN an authorized collision is generated, THE Audit_Logger SHALL record: authorizing actor, authorization timestamp, affected record reference, modification reason, and legal basis for modification
6. THE Chameleon_Hash_Engine SHALL preserve all previous versions of redacted data in an encrypted compliance archive accessible only to authorized Compliance_Personnel
7. THE Chameleon_Hash_Engine SHALL generate cryptographic proof that the collision was authorized, linking the trapdoor key usage to the authorizing actor's identity
8. THE Platform SHALL maintain a Chameleon Hash operation log showing all collision generations with status, authorizer, and timestamp accessible to Compliance_Personnel

### Requirement 14: Smart Contract Enforcement

**User Story:** As a Data_Fiduciary, I want smart contracts to enforce consent and audit rules on-chain, so that compliance logic is tamper-proof and verifiable.

#### Acceptance Criteria

1. THE Blockchain_Layer SHALL deploy a Consent Smart_Contract that records consent grants, modifications, and withdrawals with Data_Principal address, purpose, scope, timestamp, and expiry
2. THE Blockchain_Layer SHALL deploy a Verification Smart_Contract that stores record hashes, provides on-chain comparison functions, and returns verification status
3. THE Blockchain_Layer SHALL deploy an Audit Smart_Contract that stores audit log hashes, provides immutability proof functions, and supports batch verification
4. WHEN a consent operation occurs, THE Consent Smart_Contract SHALL emit an event containing the Data_Principal identifier, action type, purpose, scope, and timestamp
5. WHEN a verification hash is stored, THE Verification Smart_Contract SHALL emit an event containing the record identifier, hash value, and block timestamp
6. THE Blockchain_Layer SHALL deploy all Smart Contracts on a local Ganache network using Web3.py for interaction

### Requirement 15: Data Breach Detection and Incident Management

**User Story:** As a DPO, I want the Platform to detect unauthorized access patterns, generate breach alerts, and manage incident workflows, so that breaches are identified and contained rapidly.

#### Acceptance Criteria

1. WHEN the Breach_Detector identifies an unauthorized access pattern (access from unrecognized IP, access outside authorized hours, access to data categories beyond consent scope, or access rate exceeding 50 requests per minute), THE Breach_Detector SHALL generate a security incident alert
2. WHEN a security incident is detected, THE Breach_Detector SHALL notify the DPO within 30 seconds with incident severity, affected Data_Principal identifiers, suspected actor, and incident type
3. WHEN a security incident is detected, THE Breach_Detector SHALL notify affected Data_Principals within 60 seconds with a summary of the incident (without exposing investigation details)
4. THE Breach_Detector SHALL generate an incident report containing: incident ID, detection timestamp, incident type, affected records count, affected Data_Principals, suspected actor, containment actions taken, and resolution status
5. THE Platform SHALL maintain a Security Incident History dashboard accessible to the DPO showing all incidents with status (Open, Investigating, Contained, Resolved), timeline, and resolution details
6. WHEN a breach is confirmed, THE Audit_Logger SHALL create an immutable breach audit trail containing all incident-related actions and blockchain-anchor the trail within 10 seconds
7. THE Breach_Detector SHALL support configurable detection rules that the DPO can adjust based on organizational risk assessment

### Requirement 16: Emergency Access (Break Glass Access)

**User Story:** As a Doctor, I want to access patient records in a medical emergency even without prior consent, so that I can provide life-saving care while maintaining full accountability.

#### Acceptance Criteria

1. WHEN a Doctor invokes Break_Glass_Access, THE Platform SHALL require a mandatory written justification (minimum 50 characters) specifying the emergency reason before granting access
2. WHEN Break_Glass_Access is granted, THE Platform SHALL provide time-limited access for a maximum of 4 hours from the moment of invocation
3. WHEN Break_Glass_Access is invoked, THE Audit_Logger SHALL record the emergency access event with: Doctor identity, patient identifier, justification text, access start time, access duration, and data categories accessed
4. WHEN Break_Glass_Access is invoked, THE Platform SHALL notify the DPO within 30 seconds with the Doctor identity, patient identifier, and stated justification
5. WHEN Break_Glass_Access is invoked, THE Platform SHALL notify the affected Data_Principal within 60 seconds that an emergency access has occurred, with the Doctor identity and stated reason
6. WHEN the Break_Glass_Access time limit expires, THE Platform SHALL immediately revoke all emergency access permissions
7. THE Platform SHALL generate an Emergency Access Report for each Break_Glass_Access event, accessible to the DPO and Compliance_Personnel, containing full access details and post-incident review status

### Requirement 17: Data Version History

**User Story:** As a Data_Principal, I want to view the complete version history of all my records, so that I can see every modification with full attribution and verification.

#### Acceptance Criteria

1. THE Version_Store SHALL maintain a complete version history for every field in personal and healthcare records
2. THE Version_Store SHALL record for each version: previous value (encrypted), updated value (encrypted), modified by (actor identity and role), timestamp, stated reason for modification, and blockchain verification reference
3. WHEN a Data_Principal requests version history for a record, THE Platform SHALL display all versions in reverse chronological order with previous value, new value, modifier identity, timestamp, and reason
4. THE Platform SHALL provide a visual diff view highlighting changes between consecutive versions
5. WHEN a version is stored, THE Blockchain_Layer SHALL anchor a verification hash for the version entry within 10 seconds
6. THE Version_Store SHALL retain version history for the full data retention period (minimum 8 years for healthcare records)

### Requirement 18: Patient Dashboard

**User Story:** As a Data_Principal, I want a centralized dashboard showing my health summary, privacy status, and recent activities, so that I can quickly assess my data status.

#### Acceptance Criteria

1. WHEN a Data_Principal logs in, THE Platform SHALL display a dashboard containing: Profile Summary, Health Summary, Active Consents count, Recent Activities list (last 10 events), Privacy_Score, Data Integrity Status, pending Access Requests count, and Notifications (unread count)
2. THE Platform SHALL compute and display a Privacy_Score (0-100) based on: percentage of consents actively managed, data minimization level (categories shared vs. available), encryption coverage, and time since last integrity verification
3. THE Platform SHALL display Data Integrity Status showing the result and timestamp of the most recent batch verification
4. WHEN new access requests, breach alerts, or consent expiry notifications arrive, THE Platform SHALL display them with a visual unread indicator and priority badge

### Requirement 19: Doctor Workflow

**User Story:** As a Doctor, I want to access patient health records and create consultations, so that I can provide medical care within the consent boundaries set by the patient.

#### Acceptance Criteria

1. WHEN a Doctor requests access to a patient's health record, THE Platform SHALL verify that the patient has granted Healthcare Treatment consent before displaying data
2. IF a patient has not granted Healthcare Treatment consent and no Break_Glass_Access is active, THEN THE Platform SHALL deny access and display a "Consent Not Granted" message to the Doctor with an option to invoke Break_Glass_Access
3. WHEN a Doctor creates a consultation record, THE Encryption_Engine SHALL encrypt the record before storage and THE Blockchain_Layer SHALL store a verification hash within 10 seconds
4. THE Audit_Logger SHALL record every Doctor access and modification with the Doctor's identity, timestamp, patient identifier, data categories accessed, and access duration
5. WHEN a Doctor's access session exceeds 60 minutes, THE Platform SHALL require re-authentication

### Requirement 20: Pharmacy Workflow

**User Story:** As Pharmacy Staff, I want to access prescriptions and dispense medications, so that I can fulfill patient prescriptions within consent boundaries.

#### Acceptance Criteria

1. WHEN Pharmacy Staff requests access to a patient's prescriptions, THE Platform SHALL verify that the patient has granted Pharmacy Access consent before displaying data
2. IF a patient has not granted Pharmacy Access consent, THEN THE Platform SHALL deny access and display a "Consent Not Granted" message to the Pharmacy Staff
3. WHEN a prescription is dispensed, THE Audit_Logger SHALL record the dispensing event with Pharmacy Staff identity, patient identifier, prescription reference, medication details, and timestamp
4. WHEN a prescription is dispensed, THE Blockchain_Layer SHALL store a verification hash for the dispensing record within 10 seconds
5. THE Platform SHALL restrict Pharmacy Staff access to prescription and allergy data categories only, enforcing purpose limitation

### Requirement 21: Data Protection Officer Oversight

**User Story:** As a DPO, I want to oversee all data operations, manage compliance, and authorize redactions, so that the organization maintains DPDP compliance.

#### Acceptance Criteria

1. WHEN the DPO accesses the oversight dashboard, THE Platform SHALL display: total data access events (24h/7d/30d), pending erasure requests with SLA countdown, active integrity violation alerts, consent statistics (grants/withdrawals/expirations), breach incident status, and compliance metrics
2. THE Platform SHALL restrict Chameleon Hash collision generation authorization to Compliance_Personnel (DPO and Healthcare Organization Admin) after multi-factor identity verification
3. WHEN an integrity violation is detected, THE Platform SHALL send a real-time alert to the DPO within 30 seconds with the affected record identifier, Data_Principal, violation type, and detection timestamp
4. THE Platform SHALL provide Compliance_Personnel with access to the encrypted compliance archive of redacted data versions for audit purposes
5. THE Platform SHALL generate weekly compliance summary reports for the DPO containing: consent activity metrics, access event counts, breach incidents, erasure request status, and integrity verification results

### Requirement 22: Purpose Limitation and Data Minimization

**User Story:** As a Data_Principal, I want the Platform to collect and process only the minimum data necessary for each stated purpose, so that my data exposure is limited.

#### Acceptance Criteria

1. THE Platform SHALL define and enforce a data category mapping for each processing purpose: Healthcare Treatment (Medical History, Allergies, Prescriptions, Lab Reports), Pharmacy Access (Prescriptions, Allergies), Research Access (Anonymized Medical History, Anonymized Lab Reports), Insurance Access (Medical History, Prescriptions), Analytics Access (Anonymized aggregate data only), Marketing Access (Contact Information only)
2. WHEN data is accessed for a specific purpose, THE Platform SHALL provide only the data categories mapped to that purpose and deny access to all other categories
3. THE Platform SHALL display to the Data_Principal which data categories are shared for each active consent with visual category indicators
4. IF an access request includes data categories outside the authorized scope, THEN THE Platform SHALL deny the request, log the violation, and alert the DPO

### Requirement 23: Notification and Alert System

**User Story:** As a Data_Principal, I want to receive notifications about data access, consent changes, breach events, and integrity issues, so that I remain informed about all activities involving my data.

#### Acceptance Criteria

1. WHEN a new data access event occurs on a Data_Principal's records, THE Platform SHALL generate a notification to the Data_Principal within 60 seconds containing accessor role, data category, and timestamp
2. WHEN consent is about to expire (7 days before expiry), THE Platform SHALL notify the Data_Principal with the consent type, expiry date, and action options (renew or let expire)
3. WHEN an integrity violation is detected on a Data_Principal's records, THE Platform SHALL immediately notify the Data_Principal and the DPO with violation details
4. WHEN a security breach affecting a Data_Principal is detected, THE Platform SHALL notify the Data_Principal within 60 seconds with a non-technical summary of the incident
5. THE Platform SHALL maintain a notification history accessible to the Data_Principal with read/unread status and notification category filters
6. THE Platform SHALL support notification priority levels: Critical (breach, integrity violation), High (emergency access, erasure completion), Medium (data access, consent expiry), Low (routine updates)

### Requirement 24: User Interface Standards

**User Story:** As a Data_Principal, I want a professional, accessible, and responsive interface, so that I can manage my healthcare data across devices.

#### Acceptance Criteria

1. THE Platform SHALL render a professional light theme using white (#FFFFFF) as background, blue (#1E40AF) for primary actions, saffron (#FF9933) for highlights and warnings, and green (#16A34A) for success states
2. THE Platform SHALL provide a responsive layout that adapts to desktop (1200px+), tablet (768px-1199px), and mobile (320px-767px) viewport sizes
3. THE Platform SHALL use modern card-based layouts with interactive dashboard components, professional iconography, and data visualization charts
4. THE Platform SHALL not provide a dark theme option
5. THE Platform SHALL meet WCAG 2.1 Level AA accessibility standards for color contrast, keyboard navigation, and screen reader compatibility
6. THE Platform SHALL display loading states and progress indicators for all asynchronous operations exceeding 500 milliseconds

### Requirement 25: Session Management

**User Story:** As a Data_Principal, I want my sessions to be securely managed with appropriate timeouts and protections, so that unauthorized users cannot hijack or reuse my authenticated sessions.

#### Acceptance Criteria

1. WHEN a user authenticates successfully, THE Session_Manager SHALL create a cryptographically secure session with a unique session identifier (256-bit random token) and bind it to the authenticated user identity
2. THE Session_Manager SHALL validate session integrity on every request by verifying the session token, checking expiry, and confirming binding to the originating user agent and IP address range
3. WHILE a clinical role (Doctor, Pharmacy Staff) session is idle for 15 minutes, THE Session_Manager SHALL terminate the session and require re-authentication
4. WHILE a Data_Principal session is idle for 30 minutes, THE Session_Manager SHALL terminate the session and require re-authentication
5. THE Session_Manager SHALL enforce concurrent session limits: Data_Principal maximum 3 sessions, Doctor maximum 2 sessions, Pharmacy Staff maximum 2 sessions, Healthcare Organization Admin maximum 1 session, DPO maximum 2 sessions
6. IF a session fixation attempt is detected (session identifier reuse after authentication), THEN THE Session_Manager SHALL invalidate the compromised session, generate a new session identifier, and alert the Breach_Detector within 5 seconds
7. IF suspicious activity is detected during an active session (IP address change to different geographic region, or concurrent access from multiple distinct devices exceeding the session limit), THEN THE Session_Manager SHALL force-terminate all sessions for the affected user and require re-authentication with multi-factor verification
8. WHEN a session is created, terminated, or force-terminated, THE Audit_Logger SHALL record the session event with user identity, session identifier hash, event type, timestamp, source IP address, and user agent

### Requirement 26: API Rate Limiting

**User Story:** As a Data_Fiduciary, I want the Platform to enforce API rate limits per user role, so that the system is protected from abuse, denial-of-service attacks, and excessive resource consumption.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL enforce request rate limits per authenticated user role: Data_Principal 100 requests per minute, Doctor 200 requests per minute, Pharmacy Staff 200 requests per minute, Healthcare Organization Admin 300 requests per minute, DPO 300 requests per minute
2. WHEN a user exceeds 80 percent of their rate limit within a sliding 60-second window, THE Rate_Limiter SHALL include a warning indicator in the response headers (X-RateLimit-Warning: approaching-limit)
3. WHEN a user exceeds their rate limit, THE Rate_Limiter SHALL reject requests with HTTP 429 status and apply a temporary block of 60 seconds before accepting new requests from that user
4. IF a user triggers rate limit violations 5 times within a 1-hour period, THEN THE Rate_Limiter SHALL escalate to account review by notifying the DPO and temporarily suspending API access for that user until manual review is completed
5. THE Rate_Limiter SHALL include rate limit headers in every API response: X-RateLimit-Limit (maximum requests allowed), X-RateLimit-Remaining (requests remaining in current window), and X-RateLimit-Reset (seconds until the rate limit window resets)
6. THE Rate_Limiter SHALL implement DDoS protection at the API gateway level by detecting and blocking traffic patterns exceeding 1000 requests per second from a single IP address or subnet
7. WHEN a rate limit violation occurs, THE Audit_Logger SHALL record the violation with user identity, endpoint accessed, request count, time window, and escalation level applied
8. THE Rate_Limiter SHALL apply separate rate limit counters per endpoint category (authentication endpoints: 20 requests per minute, data retrieval: role-based limits, data modification: 50 percent of role-based limits)

### Requirement 27: Data Residency and Localization

**User Story:** As a Data_Fiduciary, I want all personal data to be stored within Indian jurisdiction with verifiable proof, so that the Platform complies with DPDP Act data localization requirements.

#### Acceptance Criteria

1. THE Data_Residency_Controller SHALL ensure all personal data (including encrypted data, backups, and audit logs) is stored exclusively within data centers located in India
2. WHEN data is written to any storage layer, THE Data_Residency_Controller SHALL verify that the target storage infrastructure is located within Indian jurisdiction using geolocation metadata and infrastructure provider attestation
3. THE Platform SHALL block all cross-border data transfers by default and require explicit DPO authorization with documented legal basis before any personal data is transferred outside India
4. IF cross-border transfer authorization is granted by the DPO, THEN THE Audit_Logger SHALL record the authorization with DPO identity, legal basis, data categories, destination jurisdiction, transfer purpose, and authorized duration
5. THE Data_Residency_Controller SHALL restrict infrastructure deployment to Indian data center regions only, rejecting deployment configurations targeting non-Indian regions
6. THE Data_Residency_Controller SHALL perform automated data residency compliance verification monthly, scanning all storage locations and generating a compliance report for the DPO
7. WHEN a residency compliance verification detects data stored outside Indian jurisdiction, THE Data_Residency_Controller SHALL alert the DPO within 30 seconds with the affected data identifiers, storage location, and recommended remediation actions

### Requirement 28: Grievance Redressal Workflow

**User Story:** As a Data_Principal, I want to submit grievances about data processing and receive timely resolution, so that my rights under DPDP Act Section 13 are enforceable.

#### Acceptance Criteria

1. WHEN a Data_Principal submits a grievance, THE Grievance_Handler SHALL accept the submission with mandatory fields: grievance category (Consent Violation, Unauthorized Access, Erasure Failure, Data Inaccuracy, Breach Notification Failure, Other), description (minimum 100 characters), and affected data categories
2. WHEN a grievance is submitted, THE Grievance_Handler SHALL generate a unique grievance identifier (UUID v4) and send an acknowledgment to the Data_Principal within 24 hours containing the grievance identifier, submission timestamp, assigned category, and expected resolution timeline
3. THE Grievance_Handler SHALL resolve grievances within 15 business days from submission date
4. WHEN 15 business days elapse without resolution, THE Grievance_Handler SHALL automatically escalate the grievance to Level 2 (DPO review) and notify both the Data_Principal and DPO of the escalation
5. THE Grievance_Handler SHALL support a three-level escalation workflow: Level 1 (Support Team, initial handling within 5 business days), Level 2 (DPO review and decision within 10 business days), Level 3 (External Authority referral with full documentation package)
6. WHEN a grievance status changes (Submitted, Acknowledged, Under Investigation, Escalated, Resolved, Closed), THE Grievance_Handler SHALL notify the Data_Principal within 60 seconds with the updated status and any action taken
7. THE Grievance_Handler SHALL maintain a complete audit trail for each grievance containing: submission details, all status transitions with timestamps, assigned handlers, communications sent, resolution details, and Data_Principal satisfaction feedback
8. WHEN a grievance is resolved, THE Blockchain_Layer SHALL store a resolution record hash on-chain containing the grievance identifier, resolution timestamp, resolution category, and resolution summary hash within 10 seconds

### Requirement 29: Minors' Data Protection

**User Story:** As a Guardian, I want to manage my child's health data with enhanced protections, so that the Platform complies with DPDP Act Section 9 regarding processing of children's personal data.

#### Acceptance Criteria

1. WHEN a user registers as a minor (below 18 years of age), THE Auth_Service SHALL require verifiable parental or guardian consent before activating the account and processing any personal data
2. THE Auth_Service SHALL verify age during registration using date of birth and block account activation for minors without linked Guardian consent
3. WHEN Guardian consent is provided, THE Platform SHALL link the Guardian account to the minor's account and grant the Guardian full management access over the minor's data, consents, and access logs
4. THE Platform SHALL prohibit behavioral tracking, profiling, and targeted advertising for all accounts identified as belonging to minors
5. WHILE a Data_Principal is identified as a minor, THE Platform SHALL apply enhanced data minimization by collecting only data categories strictly necessary for healthcare treatment (Medical History, Allergies, Prescriptions, and Lab Reports) and denying consent grants for Research Access, Insurance Access, Analytics Access, and Marketing Access
6. THE Platform SHALL provide a Guardian Dashboard displaying: minor's active consents, data access logs, data categories stored, integrity verification status, and pending notifications
7. WHEN a minor reaches 18 years of age, THE Platform SHALL initiate an automatic consent transfer workflow: notify the Guardian and the now-adult Data_Principal, require the Data_Principal to review and confirm or revoke all active consents within 30 days, and transfer full account control to the Data_Principal
8. WHEN Guardian consent is granted or modified for a minor, THE Audit_Logger SHALL record the Guardian identity, minor identifier, consent action, timestamp, and THE Blockchain_Layer SHALL anchor the consent hash within 10 seconds

### Requirement 30: Blockchain Backup and Recovery

**User Story:** As a Healthcare Organization Admin, I want the blockchain data to be regularly backed up with recovery capabilities, so that the Platform can recover from data loss without compromising audit integrity.

#### Acceptance Criteria

1. THE Platform SHALL create blockchain state snapshots at the earlier of every 1000 blocks or every 24 hours
2. THE Platform SHALL encrypt all blockchain backup data using AES-256-GCM before storage with encryption keys managed by the Encryption_Engine
3. THE Platform SHALL provide point-in-time recovery capability allowing restoration of blockchain state to any snapshot within the retention period
4. WHEN a blockchain backup is created, THE Platform SHALL verify backup integrity by computing a hash chain of the backup contents and comparing against the live chain state
5. THE Platform SHALL replicate blockchain backups to a geographically separate data center within India within 1 hour of backup creation
6. THE Platform SHALL maintain a Maximum Recovery Point Objective (RPO) of 1 hour, ensuring no more than 1 hour of blockchain transactions are lost in a disaster scenario
7. THE Platform SHALL maintain a Maximum Recovery Time Objective (RTO) of 4 hours, ensuring full blockchain restoration within 4 hours of disaster declaration
8. THE Platform SHALL restrict blockchain backup access to Healthcare Organization Admin and DPO roles only, requiring multi-factor authentication for backup operations
9. THE Platform SHALL execute recovery testing quarterly, documenting test results including recovery duration, data integrity verification, and any discrepancies found

### Requirement 31: Encryption Key Backup and Recovery

**User Story:** As a DPO, I want encryption keys to be securely backed up with multi-party recovery, so that key loss does not result in permanent data inaccessibility.

#### Acceptance Criteria

1. THE Key_Escrow SHALL implement Shamir's Secret Sharing with a 3-of-5 threshold for backup of all Data_Principal encryption keys, distributing key shares to five designated key custodians
2. THE Key_Escrow SHALL store encrypted key backup shares in infrastructure physically and logically separate from the data storage infrastructure
3. WHEN key recovery is required, THE Key_Escrow SHALL enforce multi-party authorization requiring both the DPO and Healthcare Organization Admin to approve the recovery request before share reconstruction begins
4. THE Key_Escrow SHALL complete key recovery within 2 hours of multi-party authorization approval
5. IF a key compromise is detected (unauthorized key usage, key material exposure, or anomalous decryption patterns), THEN THE Key_Escrow SHALL trigger automatic key rotation for all affected keys within 30 minutes and notify the DPO with compromise details
6. THE Key_Escrow SHALL integrate with a Hardware Security Module (HSM) for master key protection, ensuring master keys never exist in plaintext outside the HSM boundary
7. THE Audit_Logger SHALL record all key lifecycle events (generation, rotation, backup, recovery, destruction) with actor identity, timestamp, affected key identifier, operation type, and authorization reference
8. WHEN a key backup share is accessed or reconstructed, THE Audit_Logger SHALL record the access with custodian identities, authorization reference, and THE Blockchain_Layer SHALL anchor the event hash within 10 seconds

### Requirement 32: Third-Party Data Processor Management

**User Story:** As a DPO, I want to manage third-party data processors with full oversight and control, so that the organization complies with DPDP Act Section 8(2) regarding data processor obligations.

#### Acceptance Criteria

1. WHEN a third-party data processor is onboarded, THE Processor_Registry SHALL register the processor with: processor name, processing purpose, authorized data categories, processing start date, processing end date, and responsible DPO contact
2. THE Processor_Registry SHALL maintain digital Data Processing Agreement (DPA) records for each registered processor containing: agreement terms, authorized processing activities, data categories, retention limits, security obligations, and breach notification requirements
3. THE Processor_Registry SHALL restrict each processor's data access to the data categories and duration specified in their registered DPA
4. WHILE a processor accesses personal data, THE Audit_Logger SHALL record real-time access events with processor identity, data category accessed, Data_Principal affected, access timestamp, and access duration
5. WHEN a DPA expiry date is reached, THE Processor_Registry SHALL automatically revoke all access permissions for the expired processor within 60 seconds and notify the DPO
6. WHEN the DPO triggers a processor compliance audit, THE Processor_Registry SHALL generate an audit report containing: all access events by the processor, data categories accessed, Data_Principals affected, consent verification status, and any policy violations detected
7. THE Platform SHALL provide Data_Principals with visibility into which registered processors have accessed their data, displaying processor name, access purpose, data categories, and last access timestamp
8. IF a processor reports a data breach, THEN THE Processor_Registry SHALL initiate the breach notification chain: record the processor breach report, notify the Data_Fiduciary (Healthcare Organization Admin and DPO) within 1 hour, and notify affected Data_Principals within 72 hours of the processor's breach report
9. WHEN a processor is registered or a DPA is created, THE Blockchain_Layer SHALL anchor the processor authorization record hash on-chain within 10 seconds as immutable proof of the processing agreement
10. WHEN a processor's access is revoked (due to DPA expiry, breach, or DPO action), THE Audit_Logger SHALL record the revocation with reason, revoking authority, timestamp, and THE Blockchain_Layer SHALL anchor the revocation record within 10 seconds

## Gap Analysis and Readiness Assessment

### Gap Analysis Summary

| Gap Category | Identified Gap | Addressed By | Status |
|---|---|---|---|
| **Session Security** | No session lifecycle management or timeout enforcement | Requirement 25 (Session Management) | Addressed |
| **API Protection** | No rate limiting or DDoS protection mechanisms | Requirement 26 (API Rate Limiting) | Addressed |
| **Data Sovereignty** | No explicit data residency controls or localization verification | Requirement 27 (Data Residency and Localization) | Addressed |
| **Grievance Handling** | No DPDP Act Section 13 grievance redressal workflow | Requirement 28 (Grievance Redressal Workflow) | Addressed |
| **Minors' Protection** | No DPDP Act Section 9 children's data protection | Requirement 29 (Minors' Data Protection) | Addressed |
| **Blockchain Continuity** | No blockchain backup, recovery, or disaster recovery plan | Requirement 30 (Blockchain Backup and Recovery) | Addressed |
| **Key Recovery** | No key backup or recovery mechanism for encryption keys | Requirement 31 (Encryption Key Backup and Recovery) | Addressed |
| **Processor Oversight** | No third-party data processor management or DPDP Act Section 8(2) compliance | Requirement 32 (Third-Party Data Processor Management) | Addressed |
| **Authentication Strength** | Basic JWT authentication without session binding | Requirements 1, 25 (combined session + auth) | Addressed |
| **Consent Granularity** | Consent for minors not differentiated from adults | Requirements 6, 29 (combined consent + minors) | Addressed |
| **Compliance Reporting** | No automated compliance verification for data localization | Requirements 21, 27 (combined DPO oversight + residency) | Addressed |
| **Incident Response** | Rate limit violations not integrated with breach detection | Requirements 15, 26 (combined breach + rate limiting) | Addressed |
| **Backup Security** | No encryption key recovery in disaster scenarios | Requirements 2, 31 (combined encryption + key escrow) | Addressed |

### Readiness Scores

#### 1. DPDP Compliance Readiness: 92/100

The Platform addresses all major DPDP Act provisions: consent management (Section 6, Requirement 6-7), right to access (Section 11, Requirement 3), right to correction (Section 12, Requirement 4), right to erasure (Section 12, Requirement 5), grievance redressal (Section 13, Requirement 28), minors' protection (Section 9, Requirement 29), data processor obligations (Section 8(2), Requirement 32), data localization (Section 16-17, Requirement 27), and breach notification (Section 8(6), Requirement 15). Minor gap: Explicit Data Protection Impact Assessment (DPIA) workflow is not formalized as a standalone requirement but is partially covered through DPO oversight and compliance reporting.

#### 2. Security Readiness: 90/100

Comprehensive security coverage includes: AES-256-GCM encryption at rest (Requirement 2), key lifecycle management with HSM integration (Requirements 2, 31), role-based access control (Requirement 1), session management with idle timeouts and fixation protection (Requirement 25), API rate limiting with DDoS protection (Requirement 26), breach detection with configurable rules (Requirement 15), emergency access controls (Requirement 16), and immutable audit logging (Requirement 11). Minor gap: Network-level security (TLS configuration, certificate management, mutual TLS for inter-service communication) is not explicitly specified. Penetration testing schedule is not defined.

#### 3. Blockchain Design Readiness: 91/100

Blockchain architecture is well-specified: Chameleon Hashing with mathematical specification (Requirement 13), three dedicated Smart Contracts (Requirement 14), integrity verification with on-chain comparison (Requirement 12), blockchain backup with RPO/RTO targets (Requirement 30), hash anchoring for all critical events within 10-second SLA, and compliance archive for redacted versions. Minor gap: Blockchain scalability planning (block size limits, transaction throughput targets, chain pruning strategy) is not explicitly addressed. Ganache-to-production migration path is not specified.

#### 4. Healthcare Workflow Readiness: 88/100

Clinical workflows are covered: Doctor workflow with consent verification (Requirement 19), Pharmacy workflow with purpose limitation (Requirement 20), Break Glass Access for emergencies (Requirement 16), minors' data protection with guardian management (Requirement 29), and comprehensive version history for medical records (Requirement 17). Minor gaps: Lab report workflow (ordering, receiving, attaching to patient record) is not explicitly specified. Referral workflow between doctors is not addressed. Appointment scheduling and telemedicine integration are not in scope.

#### 5. Production Readiness: 87/100

Production infrastructure is addressed: data residency within India with monthly verification (Requirement 27), blockchain backup with 1-hour RPO and 4-hour RTO (Requirement 30), encryption key backup with Shamir's Secret Sharing and 2-hour recovery (Requirement 31), API rate limiting with DDoS protection (Requirement 26), grievance handling with SLA enforcement (Requirement 28), session management (Requirement 25), and comprehensive audit logging with 8-year retention (Requirement 11). Minor gaps: Horizontal scaling strategy and load balancing are not specified. Monitoring and observability stack (metrics, alerting, dashboards) is not defined. CI/CD pipeline and deployment automation are not in scope. Service Level Agreements (SLAs) for API response times and availability (uptime targets) are not formalized.

