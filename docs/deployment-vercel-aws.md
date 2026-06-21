# Deployment Guide — Vercel (Frontend) + AWS (Backend + Database)

This guide adapts Stage 3 (S03xx) for your chosen stack:

| Layer | Platform |
|-------|----------|
| React frontend | **Vercel** |
| FastAPI API | **AWS App Runner** (recommended) or ECS/Fargate |
| PostgreSQL | **AWS RDS** |
| Media (images/audio) | **AWS S3** |

---

## Overview & ticket order

```
S0213  Local E2E demo rehearsal          ← you are here
S0301  AWS infrastructure (RDS + S3 + secrets)
S0302  Code: S3StorageBackend + media on S3
S0303  Alembic + seed on RDS
S0304  Code: Dockerfile + deploy API to App Runner
S0305  Code: Vercel config + deploy frontend
S0306  Production smoke test
```

### Code tickets (must complete before go-live)

| ID | Ticket | Files / action |
|----|--------|----------------|
| **S0302** | S3 storage backend | Done — `backend/app/storage/s3.py`, `boto3`, auth media works with S3 |
| **S0302b** | Media + visit processor | Done — reads via `StorageBackend.read_bytes()` |
| **S0304** | Containerize API | Done — `backend/Dockerfile` |
| **S0305a** | Vercel proxy (cookies) | `frontend/vercel.json` — rewrite `/auth`, `/visits`, `/insights`, `/workers`, `/media`, `/health` to AWS API |
| **S0305b** | Production env | Vercel: leave `VITE_API_URL` **empty** (same-origin via rewrites). AWS: all secrets below |
| **S0305c** | Cross-origin fallback | If not using rewrites: set `COOKIE_SAMESITE=none`, `COOKIE_SECURE=true`, add Vercel URL to `CORS_ORIGINS` |
| **S0306** | Smoke test | Run Section 13 demo on production URLs |

> **Why Vercel rewrites?** Auth uses **httpOnly cookies**. Frontend on `*.vercel.app` and API on `*.awsapprunner.com` are different sites — cookies won't send with `SameSite=Lax`. Proxying API paths through Vercel keeps everything same-origin.

---

## Part A — S0213 Local demo (do first)

### A1. Start services

```powershell
# Terminal 1 — database
cd Field-Intelligence-System
docker compose up -d

# Terminal 2 — API
cd backend
.venv\Scripts\activate
alembic upgrade head
cd ..
python scripts/seed_users.py --force
python scripts/seed_data.py --force
uvicorn app.main:app --reload --port 8000

# Terminal 3 — frontend
cd frontend
npm run dev
```

### A2. Run automated rehearsal

```powershell
cd Field-Intelligence-System
python scripts/demo_rehearsal.py
python scripts/demo_rehearsal.py --with-gemini   # optional: live AI debrief
python scripts/demo_rehearsal.py --live http://127.0.0.1:8000
```

### A3. Manual browser demo

Open http://localhost:5173 and follow the checklist printed by `demo_rehearsal.py`.

**Demo credentials** (from `.env.local`):

| Email | Password env var |
|-------|------------------|
| `worker@ngo.org` | `DEMO_WORKER_PASSWORD` |
| `manager@ngo.org` | `DEMO_MANAGER_PASSWORD` |

**Manager demo filters:** Program = `Water Access`, Location contains `Region Y`  
**Expected pattern:** Recurring blocker *"Broken irrigation canal…"* across multiple visits.

---

## Part B — S0301 AWS infrastructure

### B1. RDS PostgreSQL

1. AWS Console → **RDS** → Create database  
2. Engine: **PostgreSQL 16**  
3. Template: Free tier (or Dev/Test)  
4. DB identifier: `fieldintel-prod`  
5. Master username / password: save securely  
6. Public access: **Yes** (simplest for App Runner; lock SG later)  
7. VPC security group: create new → allow **inbound 5432** from your IP (migration) and from App Runner later  

**Connection string:**

```
postgresql://fieldintel:<PASSWORD>@<RDS_ENDPOINT>:5432/fieldintel
```

Create DB name `fieldintel` if using default postgres DB, or set during creation.

### B2. S3 bucket

1. S3 → Create bucket → e.g. `fieldintel-media-prod-<account-id>`  
2. Block all public access: **ON**  
3. CORS configuration:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedOrigins": ["https://your-app.vercel.app", "https://yourdomain.com"],
    "ExposeHeaders": ["ETag"]
  }
]
```

### B3. Secrets (AWS Secrets Manager or App Runner env)

Store these — **never commit**:

| Secret | Example |
|--------|---------|
| `DATABASE_URL` | RDS connection string |
| `JWT_SECRET` | 32+ random chars |
| `GEMINI_TRANSCRIBE_API_KEY` | Google AI Studio key |
| `GEMINI_DEBRIEF_API_KEY` | Second key |
| `S3_BUCKET` | bucket name |
| `AWS_REGION` | `ap-south-1` |

App Runner gets S3 access via **instance role** (see B4).

### B4. IAM role for App Runner (can defer until Part D)

**If you cannot create a custom IAM role yet**, you can still complete Part C:

1. **RDS migration (C2)** — only needs `DATABASE_URL` and your IP allowed on port 5432.
2. **S3 testing locally** — create an IAM **user** with programmatic access and S3 policy (see below). Set `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` in `.env.local` with `STORAGE_BACKEND=s3`.
3. **App Runner (Part D)** — when creating the service, AWS can auto-create an **instance role** with ECR access. Add an inline S3 policy then (no separate role creation required).

**Option A — App Runner auto role (easiest at deploy time)**

When you create the App Runner service in Part D, choose **Create new service role**. After the service exists:

1. IAM → Roles → find the App Runner access role (name like `AppRunnerECRAccessRole` or the role you created).
2. Add inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
    "Resource": [
      "arn:aws:s3:::YOUR_BUCKET_NAME",
      "arn:aws:s3:::YOUR_BUCKET_NAME/*"
    ]
  }]
}
```

Do **not** set `AWS_ACCESS_KEY_ID` on App Runner — the instance role supplies credentials.

**Option B — IAM user access keys (for migration / local S3 testing only)**

1. IAM → Users → Create user → **Programmatic access**
2. Attach policy (custom):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
    "Resource": [
      "arn:aws:s3:::YOUR_BUCKET_NAME",
      "arn:aws:s3:::YOUR_BUCKET_NAME/*"
    ]
  }]
}
```

3. Save access key + secret in `.env.local` (never commit).

---

## Part C — S0302 + S0303 Code & database

### C1. S3 backend (S0302) — implemented

Code is in the repo:

- `backend/app/storage/s3.py`
- `STORAGE_BACKEND=s3` + `S3_BUCKET` + `AWS_REGION`
- Media served via authenticated `GET /media/...` (works for local and S3)

**Test S3 from your machine** (after bucket + IAM user keys):

```powershell
# In .env.local temporarily:
# STORAGE_BACKEND=s3
# S3_BUCKET=your-bucket-name
# AWS_REGION=ap-south-1
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...

cd backend
.venv\Scripts\pip install boto3
.venv\Scripts\python ..\scripts\test_storage.py
```

Switch back to `STORAGE_BACKEND=local` for everyday dev.

### C2. Migrate RDS (S0303)

From your machine (temp SG rule allowing your IP):

**Recommended** (password with `@` or special chars — URL-encoded automatically):

```powershell
$env:RDS_HOST="fieldintel-prod.cluster-xxxx.ap-southeast-2.rds.amazonaws.com"
$env:RDS_USER="your_master_user"
$env:RDS_PASSWORD=$passwordFromSecretsManager
$env:RDS_DB="postgres"
python scripts/migrate_to_rds.py --from-env --seed
```

**If you see `PAM authentication failed`:** the DB user is IAM-only. The Secrets Manager password will not work. Either:

1. **One-time migration with IAM token** (needs AWS credentials with `rds-db:connect`):

Use the **IAM DB user** and **hostname** shown in RDS Console → Connect (often `fieldintel`, not your AWS account name). The hostname in the token must match the connection hostname exactly:

```powershell
$env:RDS_HOST="fieldintel-prod-instance-1.c7iosy2wsyq4.ap-southeast-2.rds.amazonaws.com"
$env:RDS_USER="fieldintel"
$env:RDS_DB="postgres"
$env:AWS_ACCESS_KEY_ID="..."
$env:AWS_SECRET_ACCESS_KEY="..."
python scripts/migrate_to_rds.py --from-env --iam-auth --seed
```

2. **Fix for App Runner (recommended long-term):** In RDS Console → your Aurora cluster → **Modify** → ensure you have a **password-based master user** for the app. If IAM DB authentication is enabled and the user has the `rds_iam` role, either disable IAM DB auth or create a new user with password only (no `rds_iam` grant). Store that password in Secrets Manager and use it in App Runner `DATABASE_URL`.

Do **not** use IAM tokens for App Runner at runtime — they expire every ~15 minutes.

Or manually:

```powershell
cd backend
.venv\Scripts\activate
$env:DATABASE_URL="postgresql://USER:URL_ENCODED_PASSWORD@RDS_HOST:5432/postgres?sslmode=require"
alembic upgrade head
cd ..
python scripts/seed_users.py --force
python scripts/seed_data.py --force
```

Remove temporary 5432 rule from your IP after migration.

---

## Part D — S0304 Deploy API (App Runner)

### D1. Dockerfile

`backend/Dockerfile` is in the repo. Build locally to verify:

```powershell
cd backend
docker build -t fieldintel-api .
```

### D2. Push to ECR & create App Runner service

1. Create ECR repository `fieldintel-api`  
2. Build & push:

```powershell
cd backend
aws ecr get-login-password --region ap-south-1 | docker login ...
docker build -t fieldintel-api .
docker tag fieldintel-api:latest <account>.dkr.ecr.ap-south-1.amazonaws.com/fieldintel-api:latest
docker push ...
```

3. App Runner → Create service → Container registry → ECR image  
4. Port: **8000**  
5. Health check: `/health`  
6. Environment variables (production):

```env
ENVIRONMENT=production
COOKIE_SECURE=true
STORAGE_BACKEND=s3
S3_BUCKET=fieldintel-media-prod-...
AWS_REGION=ap-south-1
DATABASE_URL=postgresql://...
JWT_SECRET=...
GEMINI_TRANSCRIBE_API_KEY=...
GEMINI_DEBRIEF_API_KEY=...
CORS_ORIGINS=https://your-app.vercel.app
ALLOW_MANAGER_REGISTRATION=false
```

7. Note the App Runner URL: `https://xxxxx.ap-south-1.awsapprunner.com`

### D3. RDS security group

Allow inbound **5432** from the App Runner service security group (not 0.0.0.0/0).

---

## Part E — S0305 Deploy frontend (Vercel)

### E1. Connect repository

1. [vercel.com](https://vercel.com) → Import Git repo  
2. Root directory: **`frontend`**  
3. Framework: Vite  
4. Build command: `npm run build`  
5. Output directory: `dist`

### E2. Environment variables (Vercel)

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | **Leave empty** if using rewrites (recommended) |

### E3. `frontend/vercel.json` (S0305a — create before deploy)

Replace `YOUR_APP_RUNNER_URL` with your App Runner hostname (no trailing slash):

```json
{
  "rewrites": [
    { "source": "/auth/:path*", "destination": "https://YOUR_APP_RUNNER_URL/auth/:path*" },
    { "source": "/visits/:path*", "destination": "https://YOUR_APP_RUNNER_URL/visits/:path*" },
    { "source": "/insights/:path*", "destination": "https://YOUR_APP_RUNNER_URL/insights/:path*" },
    { "source": "/workers/:path*", "destination": "https://YOUR_APP_RUNNER_URL/workers/:path*" },
    { "source": "/media/:path*", "destination": "https://YOUR_APP_RUNNER_URL/media/:path*" },
    { "source": "/health", "destination": "https://YOUR_APP_RUNNER_URL/health" },
    { "source": "/((?!assets/).*)", "destination": "/index.html" }
  ]
}
```

This makes the browser call `https://your-app.vercel.app/auth/login` → proxied to AWS → cookies work on the Vercel domain.

### E4. Update AWS CORS

After first Vercel deploy, set:

```env
CORS_ORIGINS=https://your-project.vercel.app
```

Redeploy App Runner if needed.

### E5. SPA routing

The last rewrite sends all non-asset routes to `index.html` for React Router.

---

## Part F — S0306 Production smoke test

Run on **production URLs** (same steps as S0213 manual checklist):

1. `https://your-app.vercel.app/health` → `{"status":"ok"}`  
2. Worker login → log visit with photo → debrief → save  
3. Manager login → dashboard filters → recurring blockers → CSV export  
4. Media loads on visit detail (S3 + auth cookie via Vercel proxy)  

Record URLs in README:

```markdown
## Production
- Frontend: https://your-app.vercel.app
- API: https://xxxxx.awsapprunner.com (internal; use Vercel proxy in browser)
```

---

## Architecture talking points (demo Step 3)

1. **Analytics-ready data model** — findings stored as rows (type, text, source), not one JSON blob.  
2. **AI at the edge of the workflow** — transcription + debrief generation; human confirms before save.  
3. **Dashboard = SQL aggregation** — recurring blockers, sentiment trend; no ML for patterns.  
4. **Storage abstraction** — `StorageBackend` switches local → S3 without changing visit endpoints.  
5. **Security** — httpOnly JWT cookies, auth-gated `/media`, role-based routes, split Gemini API keys.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Login works locally, fails on Vercel | Add `vercel.json` rewrites; check `CORS_ORIGINS` |
| 401 on `/media` | Cookie not sent — same-origin rewrites required |
| Debrief 502 | Check Gemini keys on App Runner |
| RDS connection refused | Security group: allow App Runner SG on 5432 |
| Empty manager dashboard | Run seed script against RDS `DATABASE_URL` |

---

## Quick reference — env comparison

| Variable | Local | Production |
|----------|-------|------------|
| `ENVIRONMENT` | `development` | `production` |
| `COOKIE_SECURE` | `false` | `true` |
| `STORAGE_BACKEND` | `local` | `s3` |
| `DATABASE_URL` | `localhost:5433` | RDS endpoint |
| `CORS_ORIGINS` | `http://localhost:5173` | Vercel URL |
| `VITE_API_URL` | empty (Vite proxy) | empty (Vercel rewrites) |
