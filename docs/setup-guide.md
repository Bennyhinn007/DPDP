# Setup & Deployment Guide

## Local Development Setup

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 20+ | Frontend build |
| MongoDB | 7.x | Database |
| Ganache | Latest | Local blockchain (optional) |
| Git | Latest | Version control |

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd dpdp_kiro
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example)
cp .env.example .env

# Initialize database collections and indexes
python -m app.db_init

# Seed demo data (optional but recommended)
python seeds/seed_demo.py

# Start the server
python run.py
```

Backend available at: http://localhost:5000

### Step 3: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend available at: http://localhost:5173

### Step 4: Start Ganache (Optional)

```bash
npx ganache --deterministic --accounts 10 --chain.chainId 1337
```

Ganache available at: http://localhost:8545

Without Ganache, the system works but blockchain anchoring will show "failed" status. All other features function normally.

---

## Docker Deployment

```bash
# Start all services
docker-compose up --build

# Services:
# - MongoDB: localhost:27017
# - Ganache: localhost:8545
# - Backend: localhost:5000
# - Frontend: localhost:5173
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | Environment mode |
| `SECRET_KEY` | (required) | Flask secret key |
| `JWT_SECRET_KEY` | (required) | JWT signing key |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection |
| `MONGO_DB_NAME` | `dpdp_healthcare_dev` | Database name |
| `GANACHE_URL` | `http://localhost:8545` | Blockchain node |
| `ENCRYPTION_KEY` | (required) | AES-256 Fernet key |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins |

---

## Verification

```bash
# Backend health
curl http://localhost:5000/health
# Expected: {"status": "healthy", "service": "dpdp-healthcare-api"}

# API docs
open http://localhost:5000/api/docs/

# Frontend
open http://localhost:5173

# Run tests
cd backend && python -m pytest tests/ -v
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| MongoDB connection refused | Ensure `mongod` is running |
| ENCRYPTION_KEY error | Set key in `.env` file |
| Ganache timeout | Start Ganache or ignore (non-blocking) |
| CORS error in browser | Verify `CORS_ORIGINS` matches frontend URL |
| Empty dashboards | Run `python seeds/seed_demo.py` |
