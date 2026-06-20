# Field Visit Debrief Tool — Two-Stage Build Plan

A lightweight, AI-powered field intelligence system. Field workers log visits and get an instant structured debrief; managers see patterns across visits without reading every note manually.

---

## Stage 1 — The Debrief

**Goal:** capture a visit, transcribe/extract info via AI, let the user confirm it, save it. This is the demo's hero moment — messy input in, clean structure out.

### Frontend

- **Log form**: location, date, program area, stakeholders met (structured inputs), plus a free-text notes area.
- **Image upload**: single file input for a photo of handwritten notes. No camera capture or crop/rotate tooling — keep this simple for the weekend.
- **Transcription review screen**: shows the model's transcribed text in an editable textarea. The user confirms or corrects it before it's treated as ground truth.
- **Debrief review screen**: structured cards for key findings, blockers, sentiment, and follow-ups — editable before save.
- **Stack**: React, mobile-first layout with thumb-reachable controls. Plain HTML/CSS is an acceptable fallback if time is tight.

### Backend

- `POST /visits/draft` — accepts form fields plus an optional note image; if an image is present, returns the AI's transcription for review.
- `POST /visits/debrief` — takes the confirmed `raw_notes` text and calls Claude with a structured-output prompt; returns a JSON debrief.
- `POST /visits/save` — persists the confirmed visit and its debrief items to the database.
- **AI call design**: one multimodal call when an image is present (transcribe + extract in the same call); a text-only call otherwise. No separate OCR engine needed — Claude/GPT-4o handle handwriting transcription directly.
- **Stack**: FastAPI (Python) — pairs cleanly with the Claude SDK and with SQLite/pandas in Stage 2.

### Database

**Engine**: SQLite — no server setup, file-based, fully capable of the aggregation queries Stage 2 needs.

**`visits`**

| Column | Type |
|---|---|
| id | integer, PK |
| location | text |
| date | date |
| program_area | text |
| stakeholders | text |
| raw_notes | text |
| note_image_url | text, nullable |
| sentiment | text |
| created_at | timestamp |

**`findings`**

| Column | Type |
|---|---|
| id | integer, PK |
| visit_id | integer, FK → visits.id |
| type | text (`finding` / `blocker` / `follow_up`) |
| text | text |
| source | text (`text` / `photo`) |

> Row-per-finding (rather than a JSON blob) is what makes Stage 2's pattern queries trivial — it's just `GROUP BY`.

### Stage 1 Deliverable

A field worker opens the app, fills the form, either types notes or uploads a photo of handwritten ones, reviews and fixes the AI's transcription, reviews the structured debrief, and saves it.

---

## Stage 2 — Manager Dashboard

**Goal:** aggregate, filter, and surface recurring patterns across visits — without any ML.

### Frontend

- **Filter bar**: date range, program area, region/location dropdown.
- **Metric cards**: total visits, % negative sentiment, most common blocker type.
- **Recurring issues table**: blocker text grouped and counted, sortable by frequency.
- **Charts**: visits or blockers by region (bar chart), sentiment over time (line chart).
- **Visit detail drill-down**: click any row to see the original note plus the full debrief.
- **Stack**: same React app, new route. Recharts for the two charts.

### Backend

- `GET /visits` — list and filter visits by date range, program area, region.
- `GET /insights/blockers` — SQL `GROUP BY` on findings where `type = blocker`, grouped by `program_area` or `location`.
- `GET /insights/sentiment-trend` — sentiment counts grouped by week or date.
- **No ML needed** — every "pattern" endpoint is plain SQL aggregation (`COUNT`, `GROUP BY`, `ORDER BY`).
- **Optional stretch**: have the Stage 1 debrief call also assign a normalized category tag to each finding (e.g. "irrigation," "land access") so similar-but-differently-worded blockers group cleanly.

### Database

- No schema changes required — Stage 2 reads from the same `visits` and `findings` tables Stage 1 writes.
- If adding the category-tag stretch goal: add a `category` column to `findings`, populated at extraction time.

### Stage 2 Deliverable

A manager opens the dashboard, filters to a program or region, and immediately sees what's recurring — e.g. "irrigation blockers in 6 of 9 visits to Region Y this month" — without reading a single note manually.

---

## Suggested Weekend Timeline

| When | Focus | Details |
|---|---|---|
| Sat AM | Schema + backend skeleton | SQLite tables, FastAPI routes stubbed, Claude API call working in isolation (test with one sample note before touching anything else) |
| Sat PM | Stage 1 frontend | Log form, transcription review, debrief review screens wired to backend; save flow working end to end |
| Sun AM | Seed data + Stage 2 backend | Write 8–10 realistic sample visits directly to the DB so the dashboard has something to show; build insight endpoints |
| Sun PM | Dashboard frontend + polish | Filters, charts, drill-down. Leave the last 1–2 hours for demo rehearsal and write-up |

**Two notes worth keeping in mind:**

1. The schema is identical across both stages by design — Stage 2 doesn't add new tables, it queries what Stage 1 already wrote. Worth stating explicitly in your write-up, since it shows the data model was designed for the dashboard from the start rather than bolted on afterward.
2. Don't skip the Sunday-morning seed data step. Without varied, realistic sample visits, your dashboard charts will look empty or fake during the demo. Twenty minutes spent here is what makes the pattern-surfacing actually look like it's surfacing something real.
