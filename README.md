# Field Intelligence System

A lightweight, AI-powered field visit debrief tool for NGO field workers. Log structured visit metadata plus unstructured notes and photos; **Gemini** transcribes and extracts a structured debrief; managers see cross-visit patterns on a dashboard.

**Build reference:** [field_intelligence_build_guide.md](field_intelligence_build_guide.md)

---

## Quick Start (Local)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for PostgreSQL)
- Python 3.12+
- Node.js 20+ (frontend — Stage 1 later tickets)
- [Gemini API key](https://aistudio.google.com/apikey)

### 1. Clone and configure

```bash
git clone <repo-url>
cd Field-Intelligence-System
copy .env.example .env.local   # Windows
# cp .env.example .env.local   # macOS/Linux
```

Edit **`.env.local` yourself** (this file is gitignored and is not modified by project tooling). Set at minimum `GEMINI_API_KEY` and a strong `JWT_SECRET`.

### 2. Start PostgreSQL

```bash
docker compose up -d
```

Verify the database is ready:

```bash
docker compose ps
docker compose exec postgres psql -U fieldintel -d fieldintel -c "SELECT 1"
```

> **Note:** Postgres is exposed on host port **5433** (not 5432) to avoid conflicts with a local PostgreSQL install. Ensure `DATABASE_URL` in your `.env.local` uses port `5433`.

### 3. Backend (from S0103 onward)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If you see `WinError 10013` or "address already in use", another server is bound to port 8000 (often a prior `uvicorn` session). Stop it first:

```powershell
# Find process on port 8000 (Windows)
netstat -ano | findstr ":8000"
# Then stop the PID from the rightmost column:
Stop-Process -Id <PID> -Force
```

Or use a different port: `uvicorn app.main:app --reload --port 8001`

### 4. Frontend (from S0115 onward)

```bash
cd frontend
npm install
npm run dev
```

### 5. Run database migrations (S0102+)

```bash
cd backend
.venv\Scripts\activate          # Windows
alembic upgrade head
```

### 6. Seed demo users (S0104+)

```bash
python scripts/seed_users.py
```

Demo logins: `worker@ngo.org` / `manager@ngo.org` — password `demo1234`

### 7. Verify Postgres connection

With Docker running:

```bash
docker compose exec postgres psql -U fieldintel -d fieldintel -c "SELECT 1"
```

Expected output: a single row with `1`.

---

## Project Structure

```
Field-Intelligence-System/
├── docker-compose.yml      # Local PostgreSQL
├── .env.example            # Environment template
├── backend/                # FastAPI + Gemini AI
├── frontend/               # React (Vite)
├── scripts/                # Seed data, migrations helpers
└── uploads/                # Local media (gitignored contents)
    ├── images/
    └── audio/
```

---

## Demo Users (after S0104)

| Email | Password | Role |
|---|---|---|
| `worker@ngo.org` | `demo1234` | field_worker |
| `manager@ngo.org` | `demo1234` | manager |

---

## License

See [LICENSE](LICENSE).
