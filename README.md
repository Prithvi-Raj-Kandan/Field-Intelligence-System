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

### 4. Frontend

```bash
cd frontend
copy .env.example .env.local   # Windows — sets VITE_API_URL
npm install
npm run dev
```

Open http://localhost:5173 — landing page → sign in as `worker@ngo.org` with the demo password from `.env.local` (`DEMO_WORKER_PASSWORD`).

**Worker app:** Log Visit · Previous Visits · Gallery · Settings (bottom nav).  
**Flow:** Log form → review notes (if photo uploaded) → AI debrief → save.

### 5. Run database migrations

```bash
cd backend
.venv\Scripts\activate          # Windows
alembic upgrade head
```

### 6. Seed demo users (S0104+)

```bash
python scripts/seed_users.py
```

Demo logins: `worker@ngo.org` / `manager@ngo.org` — passwords set via `DEMO_WORKER_PASSWORD` and `DEMO_MANAGER_PASSWORD` in `.env.local` (see `.env.example`).

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
| `worker@ngo.org` | `DEMO_WORKER_PASSWORD` | field_worker |
| `manager@ngo.org` | `DEMO_MANAGER_PASSWORD` | manager |

---

## Security & production

- **Dual Gemini keys:** Set `GEMINI_TRANSCRIBE_API_KEY` (note images + voice) and `GEMINI_DEBRIEF_API_KEY` (debrief JSON) in `.env.local` to split API quotas.
- **Auth cookies:** JWT is stored in an httpOnly cookie (not accessible from browser console). Sign out via Profile/Settings.
- **Media:** `/media/*` requires authentication; workers only see their own visit files, managers see all.
- **HTTPS:** Set `ENVIRONMENT=production` and `COOKIE_SECURE=true`; terminate TLS at your load balancer (App Runner / ALB). The API redirects HTTP→HTTPS when `X-Forwarded-Proto: http`.
- **Registration:** Public signup creates field workers only. Set `ALLOW_MANAGER_REGISTRATION=true` only for local admin setup.
- **Demo passwords:** Use strong values in `DEMO_WORKER_PASSWORD` / `DEMO_MANAGER_PASSWORD` — avoid breached passwords like `demo1234`.

---

## License

See [LICENSE](LICENSE).
