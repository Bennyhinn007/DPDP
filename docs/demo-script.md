# Demo Script (15 Minutes)

## Pre-Demo Setup

```bash
# Start MongoDB
mongod

# Start Ganache (optional but recommended for blockchain features)
npx ganache --deterministic --chain.chainId 1337

# Seed demo data
cd backend && python seeds/seed_demo.py

# Start backend
python run.py

# Start frontend (new terminal)
cd frontend && npm run dev
```

Open: http://localhost:5173

---

## Demo Flow

### 1. System Overview (1 min)

- Show the login page (professional healthcare portal design)
- Mention: DPDP Act compliance, blockchain anchoring, consent management
- Show API docs: http://localhost:5000/api/docs/

### 2. Patient Registration & Login (2 min)

- Click "Register" link
- Register new patient OR login with: `rajesh.kumar@gmail.com` / `Patient@123`
- Show the patient dashboard with:
  - Privacy Score
  - Active Consents (4)
  - Blockchain Anchors (10)
  - Healthcare Records (4)
  - Recent Activity timeline
  - Consent distribution chart

### 3. Personal Data Center (2 min)

- Navigate to "My Data Center"
- Show encrypted profile data (decrypted for display)
- Show "Download Data" (JSON export)
- Show healthcare records list
- Demonstrate "Correct" button → correction dialog
- Demonstrate "Erase" button → erasure dialog
- Point out: version tracking, blockchain references

### 4. Consent Management (2 min)

- Navigate to "Consent Center"
- Show 6 consent types with status badges
- Grant a new consent (e.g., Analytics Access)
  - Show blockchain transaction created
- Withdraw a consent
  - Show immediate access revocation

### 5. Integrity Verification (2 min)

- Navigate to "Integrity Verification"
- Show blockchain network status (Ganache connected)
- Click "Verify All Records"
- Show green "VERIFIED" badges
- Explain: current hash vs blockchain hash comparison

### 6. Chameleon Hash Center (3 min) ← KEY RESEARCH PAGE

- Navigate to "Chameleon Hash"
- Show side-by-side comparison:
  - Traditional Hash: modification breaks chain
  - Chameleon Hash: authorized modification preserves chain
- Show the mathematical formula: CH(m,r) = g^m · y^r mod p
- Walk through DPDP Right to Correction workflow (8 steps)
- Walk through DPDP Right to Erasure workflow (8 steps)
- Show proof history table (if corrections/erasures exist)
- Explain research contribution panel

### 7. Doctor Consent-Gated Access (2 min)

- Login as doctor (register one via API if needed)
- Search for "Rajesh"
- Show consent status indicator (green = consent active)
- Access patient records → show "Access Granted" with consent verification
- Try accessing patient without consent → show "Access Denied" with DPDP explanation
- Mention: both attempts are audit-logged

### 8. DPO/Admin Dashboard (1 min)

- Login as admin: `admin@dpdp-health.in` / `Admin@Secure123`
- Show Compliance & Governance Center:
  - Compliance Score gauge
  - System metrics (patients, records, anchors)
  - Rights requests (corrections/erasures count)
  - System integrity status
- Navigate to Compliance Breakdown:
  - Radar chart (5 categories)
  - Progress bars per category
  - Risk indicators

---

## Key Talking Points

- "Data never leaves Indian jurisdiction — DPDP Act Section 16-17"
- "Every action is audited with a blockchain-anchored hash chain"
- "Patients have full visibility into who accessed their data"
- "Chameleon hashing solves the conflict between blockchain immutability and DPDP erasure rights"
- "The system scored 97/100 on DPDP compliance scorecard"

## Viva Questions Preparation

| Question | Answer Location |
|----------|----------------|
| How does encryption work? | Personal Data Center → MongoDB stores ciphertext |
| How is blockchain used? | Integrity Verification → hash comparison |
| What if data needs to be deleted? | Chameleon Hash Center → erasure workflow |
| How is consent enforced? | Doctor Dashboard → Access Denied without consent |
| How do you audit? | Audit Timeline → hash-chained events |
| What is your research contribution? | Chameleon Hash Center → comparison + formula |
