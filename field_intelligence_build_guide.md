# Field Intelligence System — Build Guide

A detailed, Jira-style reference for building the Field Visit Debrief Tool across three stages. Use this document at every step of the build — each ticket is self-contained with acceptance criteria, file paths, and dependencies.

**Deadline:** All three stages complete before Monday (local build + AWS deployment).

**AI provider:** Google **Gemini API** (`google-genai` SDK) for transcription, debrief extraction, and stretch voice memo features.

**Environment files:** Only [`.env.example`](.env.example) is maintained in the repo. Copy it to `.env.local` locally for secrets — `.env.local` is gitignored and must not be read or written by build tooling.

**Related docs:** [field_visit_debrief_tool_build_plan.md](field_visit_debrief_tool_build_plan.md) (original high-level plan)

**Implementation status (June 2026):** Stage 1 worker flow is **complete**. Stage 2 **S0201–S0202** (insights + manager visit APIs) are **complete**. Manager dashboard UI (S0204+) not started.

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Architecture](#2-architecture)
3. [Repository Structure](#3-repository-structure)
4. [Database Schema](#4-database-schema)
5. [API Contract Reference](#5-api-contract-reference)
6. [AI Prompt Contracts](#6-ai-prompt-contracts)
7. [Figma Design Workflow](#7-figma-design-workflow)
8. [Stage 1 Tickets (S01xx)](#8-stage-1-tickets-s01xx)
9. [Stage 2 Tickets (S02xx)](#9-stage-2-tickets-s02xx)
10. [Stage 3 Tickets (S03xx)](#10-stage-3-tickets-s03xx)
11. [Build Timeline (All Stages Before Monday)](#11-build-timeline-all-stages-before-monday)
12. [Environment Variables](#12-environment-variables)
13. [Demo Script](#13-demo-script)
14. [Stretch Goals](#14-stretch-goals)

---

## 1. Product Overview

### What we are building

NGO field workers conduct programs, speak with communities about problems, and meet stakeholders. Every visit produces rich but **unstructured** data. This tool lets them:

1. **Log** structured metadata (location, date, program area, stakeholders) plus unstructured input (free-form notes, photos of handwritten notes; voice memos = stretch).
2. **Review** AI-generated transcription and a structured **debrief summary** built from **both structured form data and unstructured notes**. The debrief has four sections — key findings, blockers observed, community sentiment, suggested follow-ups — which the field worker confirms before saving.
3. **Surface patterns** on a manager dashboard — the four debrief sections map directly to dashboard metrics (sentiment trends, recurring blockers, follow-up themes) via SQL aggregation, not ML.

### Debrief summary contract (drives dashboard)

The AI debrief is **not** generated from notes alone. Gemini receives:

| Input type | Fields |
|---|---|
| **Structured** | location, visit_date, program_area, stakeholders |
| **Unstructured** | free-form notes, photo transcription (voice = stretch) |

And returns four sections:

| Debrief section (UI) | API / JSON field | Stored for analytics |
|---|---|---|
| Key findings | `findings[]` | `findings` rows (`type=finding`) |
| Blockers observed | `blockers[]` | `findings` rows (`type=blocker`) — powers recurring blocker charts |
| Community sentiment | `sentiment` | `visits.sentiment` — powers sentiment trend line |
| Suggested follow-ups | `follow_ups[]` | `findings` rows (`type=follow_up`) |

Structured visit fields (`location`, `program_area`, `visit_date`) are also used directly for dashboard **filters and grouping** alongside debrief outputs.

### User roles

| Role | Access |
|---|---|
| `field_worker` | Log visits, review AI output, save debriefs |
| `manager` | Dashboard, filters, analytics, visit drill-down |

### Evaluation criteria

- **Frictionless logging** — mobile-first, thumb-reachable controls.
- **Hero moment** — messy input in, clean structured debrief out.
- **Pattern surfacing** — dashboard shows recurring issues without reading every note.
- **Working prototype** — deployed on AWS by Monday, demoable via production URL.

---

## 2. Architecture

### System diagram

```mermaid
flowchart TB
  subgraph client [React Frontend - Vite]
    Login[Login]
    LogVisit[Log Visit]
    TransReview[Transcription Review]
    DebriefReview[Debrief Review]
    Dashboard[Manager Dashboard]
  end

  subgraph api [FastAPI Backend]
    Auth[JWT Auth]
    Visits[Visit Routes]
    Insights[Insight Routes]
    AI[Gemini AI Service]
    Storage[StorageBackend]
  end

  subgraph data [Data Layer]
    PG[(PostgreSQL)]
    Media[Local disk or S3]
  end

  Login --> Auth
  LogVisit --> Visits
  TransReview --> Visits
  DebriefReview --> Visits
  Dashboard --> Insights

  Visits --> AI
  Visits --> Storage
  Visits --> PG
  Insights --> PG
  Storage --> Media
```

### Environment split

| Concern | Stages 1–2 (Local) | Stage 3 (AWS Production) |
|---|---|---|
| Database | PostgreSQL via Docker Compose | AWS RDS PostgreSQL |
| Media files | `./uploads/images/`, `./uploads/audio/` | S3 bucket (keys in DB, not bytes) |
| API | `uvicorn` on `localhost:8000` | AWS App Runner or Elastic Beanstalk |
| Frontend | Vite dev server `localhost:5173` | S3 + CloudFront or Amplify Hosting |
| Secrets | `.env.local` (user-managed, gitignored) | AWS Secrets Manager or SSM |

### Storage abstraction (critical for Stage 3)

Implement a `StorageBackend` interface from day one so Stage 3 only swaps the backend:

```python
# backend/app/storage/base.py
class StorageBackend(ABC):
    async def save(self, file: UploadFile, folder: str) -> str: ...
    async def get_url(self, path: str) -> str: ...
    async def delete(self, path: str) -> None: ...

# backend/app/storage/local.py   — Stages 1–2
# backend/app/storage/s3.py      — Stage 3
```

Selected via `STORAGE_BACKEND=local|s3` env var.

### Upload flows

**Local:** Client → `POST /visits/preprocess` (structured + notes) → optional edit when `needs_review` → `POST /visits/debrief` (`session_id` + context photos/voice) → review → `POST /visits/save` (`session_id`). Frontend passes `session_id` between steps — no manual copy/paste.

**Production:** Same API → FastAPI `put_object` to S3 → stores object key (e.g. `images/{uuid}.jpg`) in DB.

### Auth flow

1. `POST /auth/login` → returns JWT with `{ sub: user_id, role: "field_worker"|"manager" }`.
2. Frontend stores token in `localStorage` (or `sessionStorage`).
3. All protected routes send `Authorization: Bearer <token>`.
4. Backend middleware decodes JWT, attaches `current_user` to request.
5. Manager-only routes return `403` if role ≠ `manager`.

---

## 3. Repository Structure

```
Field-Intelligence-System/
├── docker-compose.yml          # Local Postgres
├── .env.example
├── .gitignore
├── backend/
│   ├── Dockerfile              # Stage 3
│   ├── requirements.txt
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/
│       │   ├── user.py
│       │   ├── visit.py
│       │   ├── visit_session.py   # in-progress workflow (Stage 1)
│       │   └── finding.py
│       ├── schemas/
│       │   ├── auth.py
│       │   ├── visit.py
│       │   ├── debrief.py
│       │   └── insight.py         # Stage 2 (S0201)
│       ├── routers/
│       │   ├── auth.py
│       │   ├── visits.py
│       │   ├── insights.py        # Stage 2 (S0201)
│       │   └── media.py
│       ├── services/
│       │   ├── ai.py
│       │   ├── auth.py
│       │   ├── visit_processor.py
│       │   ├── visit_session.py
│       │   └── insights.py        # Stage 2 (S0201)
│       ├── storage/
│       │   ├── base.py
│       │   ├── local.py
│       │   └── s3.py           # Stage 3
│       └── middleware/
│           └── auth.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/                   # client.ts, auth.ts, visits.ts
│       ├── context/               # AuthContext, VisitFlowContext
│       ├── layouts/               # WorkerLayout + bottom nav shell
│       ├── pages/
│       │   ├── LandingPage.tsx
│       │   ├── LoginPage.tsx, SignupPage.tsx
│       │   ├── LogVisitPage.tsx
│       │   ├── ReviewNotesPage.tsx
│       │   ├── DebriefGeneratePage.tsx
│       │   ├── DebriefReviewPage.tsx
│       │   ├── PreviousVisitsPage.tsx
│       │   ├── VisitDetailPage.tsx
│       │   ├── GalleryPage.tsx, RecordingsPage.tsx
│       │   ├── SettingsPage.tsx
│       │   └── ManagerPage.tsx    # Stage 2 placeholder
│       └── components/
│           ├── VisitFlowGuard.tsx
│           ├── SentimentBadge.tsx
│           └── …
├── scripts/
│   ├── seed_data.py
│   ├── test_visit_flow.py
│   ├── test_insights.py           # S0201 smoke test
│   └── migrate_to_rds.py          # Stage 3
└── uploads/                    # Local media (gitignored)
    ├── images/
    └── audio/
```

---

## 4. Database Schema

### Design principles

- **Row-per-finding** (not JSON blob) — enables trivial `GROUP BY` for dashboard queries.
- **Media paths only** — never store image/audio bytes in Postgres.
- **Same schema** locally and on RDS — Alembic migrations apply to both.

### Full DDL

```sql
-- Enum-like constraints via CHECK (or use PostgreSQL ENUM types if preferred)

CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role        VARCHAR(50) NOT NULL CHECK (role IN ('field_worker', 'manager')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE visits (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    location        VARCHAR(255) NOT NULL,
    visit_date      DATE NOT NULL,
    program_area    VARCHAR(255) NOT NULL,
    stakeholders    TEXT NOT NULL DEFAULT '',
    raw_notes       TEXT NOT NULL DEFAULT '',
    note_image_paths JSONB NOT NULL DEFAULT '[]',   -- images/notes/…
    field_photo_paths JSONB NOT NULL DEFAULT '[]',  -- images/field/…
    voice_memo_paths JSONB NOT NULL DEFAULT '[]',   -- audio/…
    sentiment       VARCHAR(50) CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- In-progress workflow (preprocess → debrief → save); migration 002
CREATE TABLE visit_sessions (
    session_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    location          VARCHAR(255) NOT NULL,
    visit_date        DATE NOT NULL,
    program_area      VARCHAR(255) NOT NULL,
    stakeholders      TEXT NOT NULL DEFAULT '',
    raw_notes         TEXT NOT NULL DEFAULT '',
    note_image_paths  JSONB NOT NULL DEFAULT '[]',
    field_photo_paths JSONB NOT NULL DEFAULT '[]',
    voice_memo_paths  JSONB NOT NULL DEFAULT '[]',
    debrief           JSONB,
    status            VARCHAR(50) NOT NULL DEFAULT 'preprocessed',  -- preprocessed | debrief_ready | saved
    visit_id          INTEGER REFERENCES visits(id) ON DELETE SET NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE findings (
    id          SERIAL PRIMARY KEY,
    visit_id    INTEGER NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
    type        VARCHAR(50) NOT NULL CHECK (type IN ('finding', 'blocker', 'follow_up')),
    text        TEXT NOT NULL,
    category    VARCHAR(100),              -- stretch: normalized tag
    source      VARCHAR(50) NOT NULL DEFAULT 'text' CHECK (source IN ('text', 'photo', 'voice'))
);

-- Indexes for dashboard queries
CREATE INDEX idx_visits_visit_date ON visits(visit_date);
CREATE INDEX idx_visits_program_area ON visits(program_area);
CREATE INDEX idx_visits_location ON visits(location);
CREATE INDEX idx_visits_sentiment ON visits(sentiment);
CREATE INDEX idx_findings_type ON findings(type);
CREATE INDEX idx_findings_category ON findings(category);
CREATE INDEX idx_findings_visit_id ON findings(visit_id);
```

### Seed users (for local dev and demo)

| Email | Password | Role |
|---|---|---|
| `worker@ngo.org` | `demo1234` | `field_worker` |
| `manager@ngo.org` | `demo1234` | `manager` |

---

## 5. API Contract Reference

Base URL: `http://localhost:8000` (local) or `https://<api-domain>` (production).

### Auth

#### `POST /auth/login`

**Auth:** Public

**Request:**
```json
{
  "email": "worker@ngo.org",
  "password": "demo1234"
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "worker@ngo.org",
    "role": "field_worker"
  }
}
```

**Errors:** `401` invalid credentials

---

#### `POST /auth/register`

**Auth:** Public (disable in production or restrict to admin)

**Request:**
```json
{
  "email": "new@ngo.org",
  "password": "securepass",
  "role": "field_worker"
}
```

**Response 201:** Same shape as login.

---

### Visits (field_worker)

#### `POST /visits/preprocess` *(step 1)*

**Auth:** `field_worker`

**Request:** `multipart/form-data`

| Field | Type | Required |
|---|---|---|
| `location` | string | yes |
| `visit_date` | date | yes |
| `program_area` | string | yes |
| `stakeholders` | string | yes |
| `raw_notes` | string | no* |
| `note_images` | file[] | no* |

\* At least one of `raw_notes` or `note_images` required. Field context photos and voice memos are **not** uploaded here.

**Response 200:**
```json
{
  "session_id": "uuid",
  "raw_notes": "Typed and/or transcribed note text",
  "needs_review": true
}
```

`needs_review` is `true` when note images were transcribed (show edit screen). `false` when the worker typed notes directly (skip edit, go to debrief on Next).

Creates a `visit_sessions` row — frontend stores `session_id` and passes it on every subsequent step.

---

#### `POST /visits/debrief` *(step 2)*

**Auth:** `field_worker`

**Request:** `multipart/form-data`

| Field | Type | Required |
|---|---|---|
| `session_id` | string | yes |
| `raw_notes` | string | no (omit to use session value; send when edited) |
| `field_photos` | file[] | no |
| `voice_memos` | file[] | no |

Field photos and voice memos are sent **directly to Gemini** — not transcribed to text.

**Response 200:**
```json
{
  "session_id": "uuid",
  "debrief": {
    "sentiment": "negative",
    "findings": [{ "type": "finding", "text": "...", "source": "photo" }],
    "blockers": [{ "type": "blocker", "text": "...", "source": "voice" }],
    "follow_ups": [{ "type": "follow_up", "text": "...", "source": "text" }]
  }
}
```

---

#### `POST /visits/save` *(step 3)*

**Auth:** `field_worker`

**Request:**
```json
{
  "session_id": "uuid-from-workflow",
  "raw_notes": "Optional final edit to notes",
  "debrief": {
    "sentiment": "negative",
    "findings": [{ "type": "finding", "text": "...", "source": "text" }],
    "blockers": [{ "type": "blocker", "text": "...", "source": "photo" }],
    "follow_ups": [{ "type": "follow_up", "text": "...", "source": "text" }]
  }
}
```

Structured fields and media paths are loaded from the session — frontend only sends `session_id` plus any edits.

**Response 201:**
```json
{
  "visit_id": 42,
  "message": "Visit saved successfully"
}
```

**Debrief idempotency:** If session status is already `debrief_ready`, repeat `POST /visits/debrief` returns cached debrief without calling Gemini.

---

#### `GET /visits/sessions/{session_id}` *(recovery)*

**Auth:** `field_worker` (own session)

**Response 200:** `{ session_id, status, raw_notes, debrief | null }`

---

#### Worker read APIs *(as-built)*

| Method | Path | Description |
|---|---|---|
| `GET` | `/visits/mine` | Saved visits for current worker |
| `GET` | `/visits/mine/{visit_id}` | Full visit + findings |
| `GET` | `/visits/mine/gallery` | Context (field) photos only |
| `GET` | `/visits/mine/recordings` | Voice memo paths |

---

### Visits (manager)

#### `GET /visits`

**Auth:** `manager`

**Query params:**

| Param | Type | Description |
|---|---|---|
| `date_from` | date | Filter start |
| `date_to` | date | Filter end |
| `program_area` | string | Exact match |
| `location` | string | Partial match |
| `page` | int | Default 1 |
| `page_size` | int | Default 20 |

**Response 200:**
```json
{
  "items": [
    {
      "id": 42,
      "location": "Region Y - Village A",
      "visit_date": "2026-06-18",
      "program_area": "Water Access",
      "sentiment": "negative",
      "blocker_count": 2,
      "created_at": "2026-06-18T14:30:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

#### `GET /visits/{id}`

**Auth:** `manager`

**Response 200:**
```json
{
  "id": 42,
  "location": "Region Y - Village A",
  "visit_date": "2026-06-18",
  "program_area": "Water Access",
  "stakeholders": "Village council, local farmer cooperative",
  "raw_notes": "Full confirmed notes...",
  "note_image_path": "images/a1b2c3.jpg",
  "note_image_url": "http://localhost:8000/media/images/a1b2c3.jpg",
  "sentiment": "negative",
  "findings": [
    { "id": 1, "type": "finding", "text": "...", "source": "text", "category": null },
    { "id": 2, "type": "blocker", "text": "...", "source": "photo", "category": null }
  ],
  "created_at": "2026-06-18T14:30:00Z"
}
```

---

### Insights (manager)

#### `GET /insights/summary`

**Auth:** `manager`

**Query params:** Same filters as `GET /visits`

**Response 200:**
```json
{
  "total_visits": 10,
  "negative_sentiment_pct": 40.0,
  "most_common_blocker": "Broken irrigation canal",
  "most_common_blocker_count": 6
}
```

---

#### `GET /insights/blockers`

**Auth:** `manager`

**Query params:** `date_from`, `date_to`, `program_area`, `location`, `group_by` (`location`|`program_area`|`text`)

**Response 200:**
```json
{
  "items": [
    { "group": "Region Y", "blocker_text": "Broken irrigation canal", "count": 6 },
    { "group": "Region X", "blocker_text": "Land access dispute", "count": 3 }
  ]
}
```

**SQL pattern:**
```sql
SELECT v.location, f.text, COUNT(*) AS count
FROM findings f
JOIN visits v ON f.visit_id = v.id
WHERE f.type = 'blocker'
  AND v.visit_date BETWEEN :date_from AND :date_to
GROUP BY v.location, f.text
ORDER BY count DESC;
```

---

#### `GET /insights/sentiment-trend`

**Auth:** `manager`

**Query params:** `date_from`, `date_to`, `program_area`, `location`, `interval` (`day`|`week`)

**Response 200:**
```json
{
  "items": [
    { "period": "2026-06-01", "positive": 2, "neutral": 1, "negative": 3 },
    { "period": "2026-06-08", "positive": 1, "neutral": 2, "negative": 4 }
  ]
}
```

---

## 6. AI Prompt Contracts

### Transcription (multimodal — when image present)

**System prompt:**
```
You are transcribing handwritten field notes from an NGO worker's site visit.
Transcribe all legible text exactly. Preserve bullet points and structure.
If text is illegible, mark as [illegible]. Do not invent content.
Return only the transcribed text, no preamble.
```

**User message:** Image attachment + optional context: location, program area, stakeholders.

---

### Debrief extraction (structured + unstructured → four sections)

**Inputs sent to Gemini:**

1. **Structured visit data:** location, visit_date, program_area, stakeholders
2. **Unstructured notes:** confirmed raw_notes (typed and/or transcribed from photos)

**System prompt:**
```
You are an NGO field intelligence assistant. Produce a structured debrief summary
from BOTH structured visit metadata AND unstructured field notes.

Your output has exactly four sections (these drive the manager analytics dashboard):
1. Key findings — important observations, community feedback, program outcomes
2. Blockers observed — obstacles preventing progress (infrastructure, bureaucracy, funding, access)
3. Community sentiment — overall community mood: positive, neutral, or negative
4. Suggested follow-ups — concrete next actions with owners/timeframes when mentioned

Rules:
- Use structured metadata to contextualize items
- Use unstructured notes as primary evidence; do not invent facts
- Keep each list item to one clear sentence
- source: "photo" if mainly from transcribed handwriting, else "text"
```

**JSON schema (API field names):**
```json
{
  "sentiment": "positive | neutral | negative",
  "findings": [{ "type": "finding", "text": "...", "source": "text|photo" }],
  "blockers": [{ "type": "blocker", "text": "...", "source": "text|photo" }],
  "follow_ups": [{ "type": "follow_up", "text": "...", "source": "text|photo" }]
}
```

**Model:** `gemini-2.5-flash` (default; override via `GEMINI_MODEL`) via the [Google Gen AI SDK](https://googleapis.github.io/python-genai/) (`google-genai`).

**SDK setup:**
```python
from google import genai
client = genai.Client(api_key=settings.GEMINI_API_KEY)
```

**Structured output:** Use Gemini JSON mode / `response_schema` for debrief extraction where supported; fall back to prompt-enforced JSON with parse retry.

**Validation:** Parse JSON response; retry once on parse failure.

---

## 7. Figma Design Workflow

All UI design work uses **Figma MCP**. React implementation handles API wiring only.

### Per-ticket Figma checklist

1. Load the `figma-use` skill before any Figma MCP tool call.
2. Create or update frames in the project's Figma file.
3. Apply design tokens from S0110 (colors, typography, spacing).
4. Name components consistently: `Button/Primary`, `Input/Text`, `Card/DebriefFinding`.
5. Document states: default, hover, disabled, loading, error, empty.
6. Mobile-first frame width: **375px**. Optional tablet: 768px.
7. Note the React route in the frame description for handoff.

### Design tokens (starting point — customize via prompts)

| Token | Value | Usage |
|---|---|---|
| Primary | `#d4480a` | CTAs, links (Nudge orange) |
| Secondary | `#1b4332` | Accents |
| Success | `#2d6a4f` | Positive sentiment |
| Danger | `#b91c1c` | Errors, negative sentiment |
| Background | `#faf9f6` | Page background |
| Surface | `#ffffff` | Cards, forms |
| Header | `#1a1a1a` | Worker app header |
| Text primary | `#1a1a1a` / `#4a2c20` | Body / landing cream section |
| Font display | Playfair Display | Headings |
| Font body | DM Sans | UI text |
| Spacing unit | 4px base | `--space-*` tokens in `tokens.css` |

### Screens by stage (as-built routes)

| Screen | Ticket | React route |
|---|---|---|
| Landing | — | `/` |
| Login / Signup | S0116 | `/login`, `/signup` |
| Log Visit | S0117 | `/app/log` |
| Notes review | S0118 | `/app/log/review` (when `needs_review`) |
| Debrief generate | S0119 | `/app/log/debrief/generate` |
| Debrief review + save | S0119 | `/app/log/debrief` |
| Save success | S0119 | `/app/log/success` |
| Previous visits | S0119+ | `/app/visits` (sort/filter) |
| Visit summary | S0119+ | `/app/visits/:visitId` |
| Context photo gallery | S0119+ | `/app/gallery` |
| Voice recordings | S0119+ | `/app/recordings` |
| Settings | S0119+ | `/app/settings` |
| Manager placeholder | S0207 | `/manager` |
| Dashboard | S0204–S0211 | `/manager` or `/dashboard` *(Stage 2)* |

**Flow guard:** `VisitFlowGuard` + `VisitFlowContext` enforce step order; after save, debrief routes redirect to `/app/log`. Session id persisted in `sessionStorage` for recovery.

### Screens by stage (original Figma ticket names)

| Screen | Figma ticket | React route |
|---|---|---|
| Login | S0111 | `/login` |
| Log Visit | S0112 | `/app/log` |
| Transcription Review | S0113 | `/app/log/review` |
| Debrief Review | S0114 | `/app/log/debrief` |
| Save Success | S0114 (variant) | `/app/log/success` |
| Dashboard | S0204, S0205 | `/manager` *(Stage 2)* |
| Visit Detail | S0206 | `/app/visits/:id` (worker) · manager drill-down Stage 2 |

---

## 8. Stage 1 Tickets (S01xx)

**Goal:** Field worker logs a visit, reviews AI transcription and debrief, saves to Postgres.

---

### 8.1 Stage 1 As-Built (June 2026)

What was actually shipped vs. original ticket names:

| Area | Planned (tickets) | As-built |
|---|---|---|
| Visit capture API | S0107 unified `/visits/analyze` | **3-step session API:** `POST /visits/preprocess` → `POST /visits/debrief` → `POST /visits/save` with `visit_sessions` |
| Note photos | Transcribed in step 1 | Transcribed at **preprocess** only |
| Field photos + voice | Stretch S0121 | Uploaded at **debrief**; sent **directly to Gemini** (not transcribed to text first) |
| Debrief AI | Text + optional photo notes flag | Multimodal: text + field photos + voice memos in one Gemini call |
| Frontend design | Figma-first (S0110–S0114) | **Code-first** Nudge-inspired UI in `frontend/src/styles/tokens.css` (Figma tickets optional) |
| Worker nav | Single log flow | Bottom nav: Log · Visits · Photos · Audio · Settings |
| Manager UI | Stage 2 | `/manager` placeholder only |
| Resilience | — | Idempotent debrief, `GET /visits/sessions/{id}`, Strict Mode–safe generate page |
| Tests | S0120 E2E script | `scripts/test_visit_flow.py`; manual E2E via UI |

**Gemini calls per visit:** 1× `transcribe_image` per note photo (preprocess) + 1× `generate_debrief` (debrief; +1 retry if JSON invalid). Voice uses debrief multimodal path, not separate transcription.

**Stage 1 ticket status:** S0101–S0119 ✅ · S0120 partial (script exists, formal checklist pending) · S0121 partial (voice at debrief, no separate transcribe_audio in flow)

---

### S0101 — Local Dev Environment Setup

| Field | Value |
|---|---|
| **Type** | Infra |
| **Estimate** | M |
| **Depends on** | — |

**Description**

Bootstrap the monorepo so backend and frontend can run on your PC. PostgreSQL runs in Docker; no AWS required yet.

**Acceptance Criteria**

- [ ] `docker compose up -d` starts Postgres on host port **5433** (avoids conflict with local Postgres on 5432)
- [ ] `.env.example` committed; `.env.local` gitignored (user copies example locally — agents do not edit `.env.local`)
- [ ] `backend/` and `frontend/` directories exist per repo structure
- [ ] `uploads/images/` and `uploads/audio/` exist and are gitignored
- [ ] README section: "Quick Start" with 5 commands to run locally

**Technical Notes**

`docker-compose.yml`:
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: fieldintel
      POSTGRES_PASSWORD: fieldintel
      POSTGRES_DB: fieldintel
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

**Files to create**

- `docker-compose.yml`
- `.env.example`
- `uploads/.gitkeep`
- Update `README.md`

**Definition of Done**

`psql postgresql://fieldintel:fieldintel@localhost:5433/fieldintel -c "SELECT 1"` succeeds.

---

### S0102 — PostgreSQL Schema + Alembic Migrations

| Field | Value |
|---|---|
| **Type** | Backend/DB |
| **Estimate** | M |
| **Depends on** | S0101 |

**Description**

Define SQLAlchemy models and initial Alembic migration for `users`, `visits`, `findings`.

**Acceptance Criteria**

- [ ] Models match DDL in Section 4
- [ ] `alembic upgrade head` creates all tables and indexes
- [ ] `alembic downgrade -1` rolls back cleanly
- [ ] Foreign keys and CHECK constraints enforced

**Files to create**

- `backend/app/models/user.py`, `visit.py`, `finding.py`
- `backend/app/database.py`
- `backend/alembic/versions/001_initial_schema.py`

**Definition of Done**

Tables visible in Postgres; `\d visits` and `\d findings` show correct columns.

---

### S0103 — FastAPI Project Skeleton

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | S |
| **Depends on** | S0101 |

**Description**

FastAPI app with CORS, health check, config loading, and router mounting.

**Acceptance Criteria**

- [ ] `GET /health` returns `{ "status": "ok" }`
- [ ] CORS allows `http://localhost:5173`
- [ ] Config loads from environment via `pydantic-settings` (reads `.env.local` at runtime when present; template changes go in `.env.example` only)
- [ ] `uvicorn app.main:app --reload` starts on port 8000

**Files to create**

- `backend/app/main.py`
- `backend/app/config.py`
- `backend/requirements.txt`

**Definition of Done**

`curl http://localhost:8000/health` returns 200.

---

### S0104 — Auth: JWT Login + Role Middleware

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | M |
| **Depends on** | S0102, S0103 |

**Description**

Implement user registration/login with bcrypt password hashing and JWT tokens. Role-based dependency for route protection.

**Acceptance Criteria**

- [ ] `POST /auth/login` returns JWT for valid credentials
- [ ] `POST /auth/register` creates user with hashed password
- [ ] `get_current_user` dependency extracts user from Bearer token
- [ ] `require_role("manager")` returns 403 for field workers
- [ ] Seed script creates demo users (see Section 4)

**Files to create**

- `backend/app/routers/auth.py`
- `backend/app/services/auth.py`
- `backend/app/schemas/auth.py`
- `backend/app/middleware/auth.py`
- `scripts/seed_users.py`

**Definition of Done**

Login as `manager@ngo.org` returns token with `role: "manager"`.

---

### S0105 — Local File Upload Service

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | M |
| **Depends on** | S0103 |

**Description**

Implement `StorageBackend` with `LocalStorageBackend`. Save uploaded images to `./uploads/images/`. Serve files via static route for local preview.

**Acceptance Criteria**

- [ ] `StorageBackend` ABC defined with `save`, `get_url`, `delete`
- [ ] `LocalStorageBackend` writes files with UUID filenames
- [ ] Returns relative path (e.g. `images/uuid.jpg`)
- [ ] `GET /media/{path}` serves local files (dev only)
- [ ] Max file size enforced (e.g. 10 MB)
- [ ] Allowed types: `image/jpeg`, `image/png`

**Files to create**

- `backend/app/storage/base.py`
- `backend/app/storage/local.py`
- `backend/app/storage/__init__.py` (factory: `get_storage_backend()`)

**Definition of Done**

Upload a test image; file exists on disk; URL returns the image in browser.

---

### S0106 — Gemini AI Service

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | M |
| **Depends on** | S0103 |

**Description**

Isolated AI service using the **Gemini API** with two functions: `transcribe_image()` and `generate_debrief()`. Test with a sample note before wiring to routes.

**Acceptance Criteria**

- [ ] Uses `google-genai` SDK with `GEMINI_API_KEY` from config
- [ ] `transcribe_image(image_bytes, context)` sends image + structured context to Gemini; returns plain text
- [ ] `generate_debrief(raw_notes, structured, has_photo_notes)` uses **both** structured metadata and unstructured notes
- [ ] Returns four sections: key findings, blockers observed, community sentiment, suggested follow-ups
- [ ] JSON parse failure triggers one retry with repair prompt
- [ ] Standalone test script runs successfully with sample input

**Technical Notes**

- Package: `google-genai` (add to `requirements.txt`)
- Model: `gemini-2.0-flash` for both transcription (vision) and debrief (text)
- Image input: pass bytes as `types.Part.from_bytes(data=..., mime_type="image/jpeg")`

**Files to create**

- `backend/app/services/ai.py`
- `scripts/test_ai.py`

**Definition of Done**

`python scripts/test_ai.py` prints structured debrief JSON for a sample paragraph.

---

### S0107 — POST /visits/analyze (unified capture)

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | M |
| **Depends on** | S0104, S0105, S0106 |

**Description**

Single multipart endpoint: structured fields + typed notes + note photos + field photos + voice memos. Transcribe notes/audio, use field photos as debrief context, return combined `raw_notes` + four-section debrief preview.

**Acceptance Criteria**

- [ ] Multipart form with multiple file arrays (`note_images`, `field_photos`, `voice_memos`)
- [ ] Note images saved to `images/notes/`, field photos to `images/field/`, audio to `audio/`
- [ ] Returns `raw_notes`, all media paths, and full `debrief` JSON
- [ ] Field photos included in Gemini multimodal debrief call
- [ ] Requires `field_worker` role
- [ ] `/visits/draft` and `/visits/debrief` kept as deprecated wrappers

**Files**

- `backend/app/routers/visits.py` — `POST /visits/analyze`
- `backend/app/services/visit_processor.py`
- `backend/app/schemas/visit.py` — `AnalyzeVisitResponse`
- `scripts/test_analyze.py`

**Definition of Done**

`python scripts/test_analyze.py` passes; Swagger upload of note + field photos produces debrief using both text and visuals.

---

### S0108 — POST /visits/debrief *(deprecated)*

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | S |
| **Depends on** | S0104, S0106 |

**Description**

Legacy JSON debrief preview without field photos. Superseded by `POST /visits/analyze`.

**Acceptance Criteria**

- [ ] Still callable for backward compatibility
- [ ] Marked deprecated in OpenAPI

**Definition of Done**

POST sample notes → receive valid debrief JSON (text-only path).

---

### S0109 — POST /visits/save

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | M |
| **Depends on** | S0104, S0102 |

**Description**

Persist confirmed visit and all findings to Postgres in a single transaction.

**Acceptance Criteria**

- [ ] Creates `visits` row with all metadata + sentiment
- [ ] Creates `findings` rows for each finding/blocker/follow_up
- [ ] Sets `source` field correctly on each finding
- [ ] Returns `visit_id` on success
- [ ] Transaction rolls back on any error

**Definition of Done**

Save a visit; query DB confirms 1 visit row + N finding rows.

---

### S0110 — Figma: Design System + Mobile Layout Grid

| Field | Value |
|---|---|
| **Type** | Design |
| **Estimate** | M |
| **Depends on** | — |

**Description**

Create Figma design tokens page: colors, typography, spacing, component primitives (buttons, inputs, cards).

**Acceptance Criteria**

- [ ] Color styles defined per token table in Section 7
- [ ] Text styles: H1, H2, Body, Label, Caption
- [ ] Component set: Button (primary/secondary/disabled), TextInput, TextArea, Card
- [ ] 375px mobile frame template with safe-area padding
- [ ] All components use auto-layout

**Figma MCP steps**

1. Load `figma-use` skill
2. Create page "Design System"
3. Build token swatches and text styles from user-provided color/font preferences
4. Build reusable components with variants

**Handoff**

React implements tokens as CSS variables in `frontend/src/styles/tokens.css`.

**Definition of Done**

Design system page complete; components reusable across screen tickets.

---

### S0111 — Figma: Login Screen

| Field | Value |
|---|---|
| **Type** | Design |
| **Estimate** | S |
| **Depends on** | S0110 |

**Description**

Mobile login screen: NGO logo/title, email + password fields, login button, error state.

**Acceptance Criteria**

- [ ] Default, loading, and error states designed
- [ ] Thumb-reachable login button (bottom third of screen)
- [ ] Role hint text: "Field workers and managers sign in here"

**Handoff:** `frontend/src/pages/LoginPage.tsx`

---

### S0112 — Figma: Log Visit Screen

| Field | Value |
|---|---|
| **Type** | Design |
| **Estimate** | M |
| **Depends on** | S0110 |

**Description**

Main data entry screen: location, date picker, program area dropdown, stakeholders, notes textarea, photo upload button.

**Acceptance Criteria**

- [ ] All structured fields present with labels
- [ ] Photo upload area with preview thumbnail state
- [ ] "Continue" CTA fixed at bottom
- [ ] Empty and filled states

**Handoff:** `frontend/src/pages/LogVisitPage.tsx`

---

### S0113 — Figma: Transcription Review Screen

| Field | Value |
|---|---|
| **Type** | Design |
| **Estimate** | S |
| **Depends on** | S0110 |

**Description**

Editable textarea showing AI transcription. User confirms or corrects before debrief generation.

**Acceptance Criteria**

- [ ] Large editable text area
- [ ] Helper text: "Review and correct the transcription before continuing"
- [ ] Back and Continue buttons
- [ ] Loading state while AI transcribes

**Handoff:** `frontend/src/pages/TranscriptionReviewPage.tsx`

---

### S0114 — Figma: Debrief Review Screen

| Field | Value |
|---|---|
| **Type** | Design |
| **Estimate** | M |
| **Depends on** | S0110 |

**Description**

Structured debrief cards: sentiment badge, editable finding/blocker/follow-up lists, save button, success confirmation variant.

**Acceptance Criteria**

- [ ] Sentiment shown as color-coded badge (green/gray/red)
- [ ] Three card sections: Findings, Blockers, Follow-ups
- [ ] Each item editable (inline or tap-to-edit)
- [ ] Add/remove item affordance
- [ ] Save + Success states

**Handoff:** `frontend/src/pages/DebriefReviewPage.tsx`

---

### S0115 — React App Scaffold

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | M |
| **Depends on** | S0110 |

**Description**

Vite + React + TypeScript + React Router. API client with auth header injection. Base layout with mobile viewport.

**Acceptance Criteria**

- [ ] `npm run dev` starts on port 5173
- [ ] React Router routes stubbed for all pages
- [ ] `api/client.ts` wraps fetch with base URL + JWT header
- [ ] CSS tokens file mirrors Figma tokens
- [ ] Vite proxy: `/api` → `localhost:8000` (optional)

**Files to create**

- `frontend/package.json`, `vite.config.ts`, `src/main.tsx`, `src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/styles/tokens.css`

**Definition of Done**

App loads; router navigates between stub pages.

---

### S0116 — React: Login Page

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | S |
| **Depends on** | S0111, S0104, S0115 |

**Description**

Implement login UI from Figma. Store JWT; redirect by role.

**Acceptance Criteria**

- [ ] Matches Figma design (colors, spacing, typography)
- [ ] Calls `POST /auth/login`
- [ ] Stores token in localStorage
- [ ] Redirects `field_worker` → `/visits/new`
- [ ] Redirects `manager` → `/dashboard`
- [ ] Shows error message on 401

**Definition of Done**

Login as worker and manager; each lands on correct route.

---

### S0117 — React: Log Visit Page

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | M |
| **Depends on** | S0112, S0107, S0116 |

**Description**

Wire log form to `POST /visits/draft`. Pass form state + transcription to next step via React context or router state.

**Acceptance Criteria**

- [ ] All form fields validated before submit
- [ ] Image file picker works on mobile
- [ ] Loading spinner during AI transcription
- [ ] On success, navigate to transcription review with data

**Definition of Done**

Submit form with photo → land on transcription review with AI text.

---

### S0118 — React: Transcription Review Page

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | S |
| **Depends on** | S0113, S0117 |

**Description**

Display editable transcription. On confirm, call `POST /visits/debrief` and navigate to debrief review.

**Acceptance Criteria**

- [ ] Textarea pre-filled with transcription
- [ ] User edits persist in component state
- [ ] Continue calls debrief endpoint with confirmed notes
- [ ] Loading state during debrief generation

**Definition of Done**

Edit transcription → continue → debrief cards appear on next screen.

---

### S0119 — React: Debrief Review + Save Flow

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | M |
| **Depends on** | S0114, S0108, S0109, S0118 |

**Description**

Render editable debrief cards. Save calls `POST /visits/save`. Show success screen.

**Acceptance Criteria**

- [ ] Sentiment badge displayed and editable (dropdown)
- [ ] Findings/blockers/follow-ups editable, add/remove works
- [ ] Save calls API with full payload
- [ ] Success screen with "Log another visit" CTA
- [ ] Error handling on save failure

**Definition of Done**

Full Stage 1 flow works end-to-end on localhost.

---

### S0120 — Stage 1 E2E Test + Demo Script

| Field | Value |
|---|---|
| **Type** | QA |
| **Estimate** | S |
| **Depends on** | S0119 |

**Description**

Manual test checklist for Stage 1. Document demo steps for field worker flow.

**Acceptance Criteria**

- [ ] Test: typed notes only path
- [ ] Test: photo upload path
- [ ] Test: edit transcription + debrief before save
- [ ] Test: verify DB rows after save
- [ ] Demo script written (see Section 13, Steps 1–3)

**Definition of Done**

All checklist items pass; demo script ready.

---

### S0121 — (Stretch) Voice Memo Upload + Transcription

| Field | Value |
|---|---|
| **Type** | Backend + Frontend |
| **Estimate** | L |
| **Depends on** | S0105, S0106 |

**Description**

Allow audio file upload (or browser recording). Transcribe via Gemini multimodal audio (or Gemini transcription). Merge transcription into notes flow.

**Acceptance Criteria**

- [ ] Accept `audio/mpeg`, `audio/wav`, `audio/webm`
- [ ] Save to `./uploads/audio/`
- [ ] Transcription appended to or replaces notes
- [ ] `source: "voice"` on findings from audio content

**Defer if:** Monday deadline is tight; text + photo path is sufficient for demo.

---

## 9. Stage 2 Tickets (S02xx)

**Goal:** Manager dashboard surfaces patterns across visits via SQL aggregation.

---

### S0201 — Insight Endpoints ✅

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | M |
| **Depends on** | S0109 |
| **Status** | **Done** |

**Description**

Implement `/insights/summary`, `/insights/blockers`, `/insights/sentiment-trend` with filter params.

**Acceptance Criteria**

- [x] All three endpoints require `manager` role
- [x] Filters: `date_from`, `date_to`, `program_area`, `location`
- [x] Blockers endpoint supports `group_by` param (`location` \| `program_area` \| `text`)
- [x] Sentiment trend groups by week by default (`interval=week`; `day` optional)
- [x] Raw SQL or SQLAlchemy queries — no ML

**Files created**

- `backend/app/routers/insights.py`
- `backend/app/schemas/insight.py`
- `backend/app/services/insights.py`
- `scripts/test_insights.py`

**Definition of Done**

`python scripts/test_insights.py` passes; manager token returns aggregations; field worker gets `403`.

---

### S0202 — GET /visits List + Detail ✅

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | S |
| **Depends on** | S0109 |
| **Status** | **Done** |
| **Note** | Worker equivalents: `GET /visits/mine`, `GET /visits/mine/{id}`. Manager routes: `GET /visits`, `GET /visits/{id}`. |

**Description**

Paginated visit list with filters and full visit detail for drill-down.

**Acceptance Criteria**

- [x] List returns summary fields + blocker count
- [x] Detail includes all findings + media URLs (`note_image_urls`, `field_photo_urls`, `voice_memo_urls`)
- [x] Pagination works (`page`, `page_size`)
- [x] Manager role required

**Files created**

- `backend/app/services/manager_visits.py`
- `scripts/test_manager_visits.py`

**Definition of Done**

`python scripts/test_manager_visits.py` passes; `GET /visits/{id}` returns full visit with findings array.

---

### S0203 — Seed Data Script

| Field | Value |
|---|---|
| **Type** | Data |
| **Estimate** | M |
| **Depends on** | S0102 |

**Description**

Insert 8–10 realistic NGO visits with varied locations, program areas, sentiments, and recurring blockers (e.g. irrigation appears in 6/9 Region Y visits).

**Acceptance Criteria**

- [x] At least 3 distinct locations
- [x] At least 3 program areas
- [x] Mix of positive/neutral/negative sentiment
- [x] 2–3 recurring blocker themes for dashboard impact
- [x] `python scripts/seed_data.py` is idempotent (clears + reseeds or skips if exists)

**Sample blocker themes**

- "Broken irrigation canal" — Region Y, Water Access
- "Land access dispute" — Region X, Agriculture
- "Delayed fund disbursement" — multiple regions

**Definition of Done**

Dashboard queries against seed data show meaningful patterns.

---

### S0204 — Figma: Dashboard Layout + Filter Bar

| Field | Value |
|---|---|
| **Type** | Design |
| **Estimate** | M |
| **Depends on** | S0110 |

**Description**

Desktop-primary dashboard shell (768px+) with sidebar or top nav, filter bar, content grid area.

**Acceptance Criteria**

- [ ] Filter bar: date range, program area dropdown, location dropdown
- [ ] "Apply filters" and "Clear" buttons
- [ ] Responsive: usable on tablet; mobile shows stacked filters
- [ ] Manager nav: Dashboard, Logout

**Handoff:** `frontend/src/pages/DashboardPage.tsx`, `FilterBar.tsx`

---

### S0205 — Figma: Metrics, Blockers Table, Charts

| Field | Value |
|---|---|
| **Type** | Design |
| **Estimate** | M |
| **Depends on** | S0204 |

**Description**

Design metric cards row, recurring blockers table, bar chart (blockers by region), line chart (sentiment over time).

**Acceptance Criteria**

- [ ] 3 metric cards: Total Visits, % Negative Sentiment, Top Blocker
- [ ] Sortable blockers table with columns: Blocker, Region, Count
- [ ] Bar chart and line chart placeholder frames with sample data
- [ ] Empty state when no data matches filters

**Handoff:** `MetricCards.tsx`, `BlockersTable.tsx`, chart components

---

### S0206 — Figma: Visit Detail Drill-Down

| Field | Value |
|---|---|
| **Type** | Design |
| **Estimate** | S |
| **Depends on** | S0204 |

**Description**

Drawer or modal showing full visit: metadata, raw notes, image preview, all findings/blockers/follow-ups.

**Acceptance Criteria**

- [ ] Opens from table row click
- [ ] Shows original notes + debrief side by side or stacked
- [ ] Image preview if `note_image_path` exists
- [ ] Close/back affordance

**Handoff:** `frontend/src/components/VisitDetailDrawer.tsx`

---

### S0207 — React: Dashboard Route + Role Guard

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | S |
| **Depends on** | S0204, S0201, S0116 |

**Description**

Add `/dashboard` route. Redirect non-managers to login or 403 page.

**Acceptance Criteria**

- [x] Only `manager` role can access `/dashboard`
- [x] Field worker redirected to `/visits/new`
- [x] Unauthenticated user redirected to `/login`
- [x] Dashboard shell renders with filter bar placeholder

**Definition of Done**

Role guard works for all three cases.

---

### S0208 — React: Filter Bar + Metric Cards

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | M |
| **Depends on** | S0205, S0207 |

**Description**

Wire filters to API query params. Fetch and display `/insights/summary`.

**Acceptance Criteria**

- [x] Date pickers, program area and location dropdowns populated from data
- [x] Apply filters refetches summary + downstream components
- [x] Metric cards match Figma design *(implemented from design tokens; Figma S0204–S0205 pending)*
- [x] Loading and empty states

**Definition of Done**

Change filters → metric cards update.

---

### S0209 — React: Recurring Blockers Table

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | M |
| **Depends on** | S0205, S0207 |

**Description**

Fetch `/insights/blockers`. Render sortable table.

**Acceptance Criteria**

- [x] Columns: Blocker text, Region/Group, Count
- [x] Sort by count descending by default
- [x] Click row opens visit detail (if mapped) or shows related visits *(via All visits table)*
- [x] Responds to filter bar state

**Definition of Done**

Seed data shows "irrigation" blocker ranked high for Region Y.

---

### S0210 — React: Charts (Recharts)

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | M |
| **Depends on** | S0205, S0207 |

**Description**

Bar chart: blockers by region. Line chart: sentiment trend over time.

**Acceptance Criteria**

- [x] Recharts installed and configured
- [x] Bar chart uses `/insights/blockers?group_by=location`
- [x] Line chart uses `/insights/sentiment-trend?interval=week`
- [x] Charts resize responsively
- [x] Tooltips on hover

**Definition of Done**

Both charts render with seed data; update when filters change.

---

### S0211 — React: Visit Detail Drill-Down

| Field | Value |
|---|---|
| **Type** | Frontend |
| **Estimate** | M |
| **Depends on** | S0206, S0202, S0207 |

**Description**

Drawer/modal fetches `GET /visits/{id}` and displays full visit.

**Acceptance Criteria**

- [x] Opens from blockers table or visit list row
- [x] Shows raw notes, sentiment, all findings by type
- [x] Image preview loads from `/media/` or signed URL
- [x] Close returns to dashboard state (filters preserved)

**Definition of Done**

Click visit → see full debrief without leaving dashboard context.

---

### S0212 — (Stretch) Category Tags on Findings

| Field | Value |
|---|---|
| **Type** | Backend + AI |
| **Estimate** | M |
| **Depends on** | S0108 |

**Description**

Extend debrief prompt to assign normalized `category` to each finding (e.g. "irrigation", "land_access", "funding"). Enables cleaner blocker grouping.

**Acceptance Criteria**

- [ ] AI prompt returns `category` field per item
- [ ] Saved to `findings.category`
- [ ] Blockers endpoint can `group_by=category`

---

### S0213 — Full Local E2E Demo Rehearsal

| Field | Value |
|---|---|
| **Type** | QA/Docs |
| **Estimate** | S |
| **Depends on** | S0120, S0211 |

**Description**

Run complete demo locally: field worker flow + manager dashboard. Fix any blocking bugs before Stage 3 deployment.

**Acceptance Criteria**

- [ ] Full demo script (Section 13) passes on localhost
- [ ] No console errors in browser
- [ ] Seed data produces compelling dashboard patterns
- [ ] Write-up outline drafted (architecture, data model, AI design choices)

**Definition of Done**

Ready to deploy; demo rehearsed once locally.

---

## 10. Stage 3 Tickets (S03xx)

**Goal:** Deploy working local build to AWS. All tickets must complete before Monday.

---

### S0301 — AWS Infrastructure Provisioning

| Field | Value |
|---|---|
| **Type** | Infra |
| **Estimate** | L |
| **Depends on** | S0213 |

**Description**

Provision AWS resources: RDS PostgreSQL, S3 bucket, IAM roles, Secrets Manager entries.

**Acceptance Criteria**

- [ ] RDS PostgreSQL instance running (db.t3.micro or free tier)
- [ ] Security group allows API server access to RDS port 5432
- [ ] S3 bucket created with blocked public access (files served via API or CloudFront)
- [ ] IAM role for App Runner/EB with S3 read/write permissions
- [ ] Secrets stored: `DATABASE_URL`, `GEMINI_API_KEY`, `JWT_SECRET`
- [ ] S3 bucket CORS configured for frontend origin

**AWS resources checklist**

| Resource | Purpose |
|---|---|
| RDS PostgreSQL 16 | Production database |
| S3 bucket | Image/audio file storage |
| IAM role + policies | API access to S3 and Secrets Manager |
| Secrets Manager | Environment secrets |
| (Optional) VPC + subnets | If RDS in private subnet |

**Definition of Done**

Can connect to RDS from local machine (temp security group rule). S3 put/get works via AWS CLI.

---

### S0302 — S3StorageBackend + Env Switch

| Field | Value |
|---|---|
| **Type** | Backend |
| **Estimate** | M |
| **Depends on** | S0105, S0301 |

**Description**

Implement `S3StorageBackend`. Factory selects backend via `STORAGE_BACKEND` env var.

**Acceptance Criteria**

- [ ] `S3StorageBackend.save()` uploads to bucket with UUID key
- [ ] `get_url()` returns presigned URL (or CloudFront URL)
- [ ] `STORAGE_BACKEND=s3` activates S3 backend without code changes elsewhere
- [ ] Local dev still works with `STORAGE_BACKEND=local`
- [ ] Unit test or manual test for both backends

**Files to create**

- `backend/app/storage/s3.py`
- Update `backend/app/storage/__init__.py`

**Definition of Done**

Same `/visits/draft` endpoint stores to S3 when env var set.

---

### S0303 — Migrate Database to RDS

| Field | Value |
|---|---|
| **Type** | Infra/DB |
| **Estimate** | M |
| **Depends on** | S0301, S0102 |

**Description**

Apply Alembic migrations to RDS. Import seed data from local or re-run seed script against RDS.

**Acceptance Criteria**

- [ ] `alembic upgrade head` succeeds against RDS `DATABASE_URL`
- [ ] Seed users and sample visits loaded
- [ ] Local `.env.production` or Secrets Manager has correct connection string
- [ ] No schema drift between local and production

**Files to create**

- `scripts/migrate_to_rds.py` (optional helper)

**Definition of Done**

RDS has same tables and seed data as local.

---

### S0304 — Deploy FastAPI to AWS

| Field | Value |
|---|---|
| **Type** | Infra |
| **Estimate** | L |
| **Depends on** | S0301, S0302 |

**Description**

Containerize FastAPI and deploy to AWS App Runner (recommended) or Elastic Beanstalk.

**Acceptance Criteria**

- [ ] `backend/Dockerfile` builds successfully
- [ ] Container starts with production env vars from Secrets Manager
- [ ] `GET /health` returns 200 on production URL
- [ ] API connects to RDS and S3
- [ ] HTTPS enabled on API endpoint

**Dockerfile outline:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**App Runner steps (summary)**

1. Push image to ECR (or connect GitHub repo)
2. Create App Runner service with env vars / secrets
3. Configure health check on `/health`
4. Note production API URL

**Definition of Done**

Production API URL responds to health check and login.

---

### S0305 — Deploy React Frontend

| Field | Value |
|---|---|
| **Type** | Infra |
| **Estimate** | M |
| **Depends on** | S0304 |

**Description**

Build React app with production API URL. Deploy to S3 + CloudFront or AWS Amplify Hosting.

**Acceptance Criteria**

- [ ] `VITE_API_URL` set to production API at build time
- [ ] Static build deployed and accessible via HTTPS
- [ ] CloudFront (or Amplify) serves `index.html` for SPA routes
- [ ] CORS on API allows frontend origin

**Amplify alternative (faster)**

1. Connect GitHub repo
2. Set build settings: `npm run build`, output `dist/`
3. Set env var `VITE_API_URL`

**Definition of Done**

Production frontend URL loads login page and reaches API.

---

### S0306 — Production Smoke Test + Cutover

| Field | Value |
|---|---|
| **Type** | QA/Infra |
| **Estimate** | M |
| **Depends on** | S0303, S0304, S0305 |

**Description**

Run full demo script against production URLs. Document production URLs for submission.

**Acceptance Criteria**

- [ ] Login as field worker on production → log visit with photo → save
- [ ] Login as manager on production → dashboard shows seed patterns
- [ ] Image upload stores in S3; preview loads in visit detail
- [ ] All API endpoints respond over HTTPS
- [ ] Rollback plan documented (revert to local demo if production fails)

**Pre-flight checklist**

- [ ] RDS security group locked down (API only)
- [ ] S3 bucket not publicly listable
- [ ] Secrets not in git or frontend bundle
- [ ] CORS origins restricted to production frontend URL
- [ ] Demo credentials documented for evaluators

**Definition of Done**

Full Section 13 demo passes on production URL. URLs recorded in README.

---

## 11. Build Timeline (All Stages Before Monday)

All three stages must be complete before Monday submission. Build locally first (Sat–Sun), deploy Sunday evening.

| When | Stage | Tickets | Focus |
|---|---|---|---|
| **Sat AM** | S01 | S0101 → S0102 → S0103 → S0106 | Docker Postgres, schema, API skeleton, **AI test in isolation first** |
| **Sat PM** | S01 | S0104, S0105, S0107–S0109 | Auth, uploads, all visit endpoints |
| **Sat PM** (parallel) | S01 | S0110 → S0114 | Figma design system + all Stage 1 screens |
| **Sun AM** | S01 + S02 | S0115–S0119, S0201–S0203 | Wire frontend E2E; insights API + seed data |
| **Sun PM** | S02 | S0204–S0211, S0213 | Figma dashboard + React dashboard + local demo rehearsal |
| **Sun Evening** | S03 | S0301 → S0302 → S0303 | AWS infra, S3 backend, RDS migration |
| **Sun Night / Mon AM** | S03 | S0304 → S0305 → S0306 | Deploy API + frontend, production smoke test |

### Critical path

```
S0106 (AI works) → S0107-S0109 (API) → S0119 (frontend E2E)
                                              ↓
S0203 (seed data) → S0211 (dashboard) → S0213 (local demo)
                                              ↓
S0301 (AWS) → S0304 (API deploy) → S0305 (frontend deploy) → S0306 (smoke test)
```

### Time-boxing advice

- If behind on Sunday PM: skip S0212 (category tags) and S0121 (voice memos).
- If AWS provisioning is slow: start S0301 in parallel with S0204 (Figma dashboard) on Sunday AM.
- Keep local demo working as fallback; production is additive.

---

## 12. Environment Variables

> **Policy:** Only `.env.example` is edited in the repo. Copy to `.env.local` on your machine and fill in secrets there. Do not commit `.env.local`. Build agents must not read or write `.env.local`.

### Local (copy to `.env.local` — user-managed)

```bash
DATABASE_URL=postgresql://fieldintel:fieldintel@localhost:5433/fieldintel
STORAGE_BACKEND=local
UPLOAD_DIR=./uploads
GEMINI_API_KEY=...
JWT_SECRET=change-me-in-production
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:5173
```

### Production (AWS Secrets Manager / App Runner env)

```bash
DATABASE_URL=postgresql://fieldintel:<password>@<rds-endpoint>:5432/fieldintel
STORAGE_BACKEND=s3
AWS_REGION=ap-south-1
S3_BUCKET_NAME=field-intelligence-uploads
GEMINI_API_KEY=...
JWT_SECRET=<strong-random-secret>
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=https://<cloudfront-or-amplify-domain>
```

### Frontend

```bash
# frontend/.env.local
VITE_API_URL=http://localhost:8000

# frontend/.env.production
VITE_API_URL=https://<api-domain>
```

---

## 13. Demo Script

Run this on **production URL** for final submission (or localhost if deployment blocked).

### Step 1 — Field worker logs a visit (3 min)

1. Open app → Login as `worker@ngo.org` / `demo1234`
2. Fill form: Location "Region Y - Village A", Program "Water Access", Stakeholders "Village council"
3. Upload photo of handwritten notes (have sample ready)
4. Wait for AI transcription → correct one word intentionally
5. Continue → review debrief cards (point out auto-extracted blockers)
6. Save → confirm success

### Step 2 — Manager sees patterns (3 min)

1. Logout → Login as `manager@ngo.org` / `demo1234`
2. Open Dashboard
3. Filter: Program "Water Access", Location "Region Y"
4. Point to metric cards: "6 of 9 visits flagged negative sentiment"
5. Show recurring blockers table: "Broken irrigation canal — 6 occurrences"
6. Show sentiment trend chart over time
7. Click a row → visit detail drawer with original notes + debrief

### Step 3 — Architecture talking points (2 min)

- Data model designed for analytics from day one (row-per-finding, not JSON blob)
- AI handles transcription + extraction; user confirms before save
- Dashboard uses plain SQL aggregation — no ML needed for patterns
- Storage abstraction allows local dev → S3 production without API changes

---

## 14. Stretch Goals

Prioritize only if ahead of schedule:

| Ticket | Feature | Value |
|---|---|---|
| S0121 | Voice memo upload + transcription | Richer unstructured input |
| S0212 | Category tags on findings | Cleaner blocker grouping |
| — | Presigned S3 upload from browser | Bypass API for large files |
| — | Export dashboard to CSV | Manager reporting |

---

## Ticket Index (Quick Reference)

### Stage 1 — S01xx
S0101–S0119 ✅ worker flow · S0120 partial · S0121 partial (voice at debrief)

### Stage 2 — S02xx
S0201 ✅ Insight endpoints · S0202 ✅ Visit list/detail (manager) · S0203 ✅ Seed data · S0207–S0211 ✅ Manager dashboard (React) · S0204–S0206 Figma dashboard *(pending)* · S0213 local demo *(pending)*

### Stage 3 — S03xx
S0301 AWS infra · S0302 S3 storage backend · S0303 RDS migration · S0304 Deploy API · S0305 Deploy frontend · S0306 Production smoke test

---

*Last updated: June 2026 — Stage 1 complete; Stage 2 S0201–S0203, S0207–S0211 complete.*
