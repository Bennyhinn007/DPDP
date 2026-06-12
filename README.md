# DPDP Compliant Redactable Blockchain Based Healthcare & Pharmacy Management System

A production-grade healthcare platform demonstrating compliance with India's Digital Personal Data Protection Act (DPDP Act, 2023) through privacy-first design, consent management, AES-256 encryption, blockchain verification, and Chameleon Hash-based redaction.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- MongoDB 7.x (or use Docker)
- Ganache (or use Docker)

### Option 1: Docker (Recommended)

```bash
docker-compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- MongoDB: localhost:27017
- Ganache: localhost:8545

### Option 2: Local Development

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python -m app.db_init        # Initialize MongoDB collections
python run.py                # Start Flask server on :5000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev                  # Start Vite dev server on :5173
```

**Infrastructure:**
```bash
# MongoDB (if not using Docker)
mongod --dbpath ./data/mongodb

# Ganache (if not using Docker)
npx ganache --deterministic --accounts 10 --chain.chainId 1337
```

## Architecture

```
Client (React + TypeScript + Tailwind + Shadcn UI)
    ↓ HTTPS
API Gateway (Rate Limiting + JWT + Session + RBAC)
    ↓
Flask Application (Blueprints → Services → Repositories)
    ↓                    ↓
MongoDB (Encrypted)    Ganache (Hash Anchors)
    ↓
Key Management Store (AES-256 Keys)
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Tailwind CSS, Shadcn UI |
| Backend | Flask 3, Python 3.11 |
| Database | MongoDB 7 |
| Blockchain | Ethereum (Ganache), Solidity, Web3.py |
| Encryption | AES-256-GCM (PyCryptodome) |
| Auth | JWT (PyJWT), bcrypt |

## Project Structure

```
dpdp_kiro/
├── backend/           # Flask API server
├── frontend/          # React SPA
├── docker-compose.yml # Full stack orchestration
└── .kiro/specs/       # Design documentation
```

## API Health Check

```bash
curl http://localhost:5000/health
# {"status": "healthy", "service": "dpdp-healthcare-api"}
```

## License

Academic project — All rights reserved.
