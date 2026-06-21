# Field Intelligence System

AI-powered field visit debrief tool for NGO field workers. Log visits with notes, photos, and voice memos; **Gemini** produces a structured debrief; managers see cross-visit patterns on a dashboard.

Built for **The/Nudge Institute** field operations context.

---

## Tech stack

| Layer | Technologies |
|-------|----------------|
| Frontend | React, TypeScript, Vite, Recharts |
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| AI | Google Gemini 2.5 Flash (transcription + debrief) |
| Storage | Local filesystem (dev) · DigitalOcean Spaces (prod) |
| Hosting | Vercel (frontend) · DigitalOcean App Platform (API) |
| Dev tools | Cursor IDE + agent, Docker Compose |

---

## Workflow

**Field worker**

1. Sign in → **Log Visit** (location, date, program, stakeholders).
2. Add typed notes, note photos, context photos, and/or voice memos.
3. Review AI transcription of handwritten notes (if any).
4. Generate debrief → review findings, blockers, sentiment, follow-ups → **Save**.

**Manager**

1. Sign in → **Dashboard** for summary metrics, charts, and recurring blockers.
2. **Visits** — filter, sort, export CSV, open visit detail.
3. **Workers** — select a field worker for per-person analytics and visit history.

---

**Demo logins** (after seeding): `worker@ngo.org`, `manager@ngo.org` — passwords from `FieldIntel-Worker-2026!` / `FieldIntel-Manager-2026!` .

---

## Quick start guide

### Prerequisites

- Docker Desktop (PostgreSQL)
- Python 3.12+
- Node.js 20+
- [Gemini API key](https://aistudio.google.com/apikey)

### Setup

```bash
git clone <repo-url>
cd Field-Intelligence-System
copy .env.example .env.local          # Windows
# cp .env.example .env.local            # macOS/Linux
```

Edit `.env.local`: set `GEMINI_TRANSCRIBE_API_KEY`, `GEMINI_DEBRIEF_API_KEY` (or `GEMINI_API_KEY`), and `JWT_SECRET`.

```bash
docker compose up -d

cd backend
python -m venv .venv
.venv\Scripts\activate                  # Windows
pip install -r requirements.txt
alembic upgrade head
python ../scripts/seed_users.py
uvicorn app.main:app --reload --port 8000

cd ../frontend
copy .env.example .env.local
npm install
npm run dev
```

Open http://localhost:5173 and sign in as `worker@ngo.org`.

> Postgres runs on host port **5433** (see `DATABASE_URL` in `.env.example`).
