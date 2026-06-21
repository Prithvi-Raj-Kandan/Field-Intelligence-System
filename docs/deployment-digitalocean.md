# Deployment Guide — Vercel (Frontend) + DigitalOcean (Backend + Database)

Simpler alternative to AWS ECS/RDS/S3. Recommended stack:

| Layer | Platform |
|-------|----------|
| React frontend | **Vercel** (keep existing) |
| FastAPI API | **DigitalOcean App Platform** (Docker) |
| PostgreSQL | **DO Managed Database** |
| Media | **DO Spaces** (S3-compatible) |

---

## Code prerequisites (done in repo)

- `backend/Dockerfile` — container for App Platform
- `S3_ENDPOINT_URL` — required for Spaces (AWS S3 omits this)
- `frontend/vercel.json` — replace `YOUR_DO_APP_URL` with App Platform hostname

---

## Part 1 — DigitalOcean resources to create

| Resource | DO product | Starter size |
|----------|------------|--------------|
| Database | **Databases → PostgreSQL** | Basic ($15/mo) |
| Object storage | **Spaces** | ~$5/mo |
| API | **App Platform → Web Service** | Basic ($5–12/mo) |

Region tip: pick one region (e.g. **Singapore `sgp1`**) and use it for DB, Spaces, and App Platform.

---

## Part 2 — Managed PostgreSQL

1. **DigitalOcean Console** → **Databases** → **Create Database Cluster**
2. Engine: **PostgreSQL 16**
3. Plan: Basic (1 GB RAM is fine for demo)
4. Region: e.g. **Singapore**
5. Database name: `defaultdb` (default) or create `fieldintel`
6. Create cluster → wait until **Online**

### Connection details (save these)

From the **Connection Details** tab:

- Host, port (usually **25060**), user, password, database
- **Connection string** with SSL:

```
postgresql://doadmin:PASSWORD@HOST:25060/defaultdb?sslmode=require
```

URL-encode special characters in the password (`@` → `%40`).

### Trusted sources

- For migration from your PC: add your **local IP**
- For App Platform: add the App Platform app as a **trusted source** (or allow App Platform VPC — DO can auto-link when you attach DB to the app in Part 4)

---

## Part 3 — Spaces (media storage)

1. **Spaces Object Storage** → **Create Space**
2. Name: e.g. `fieldintel-media`
3. Region: same as DB (e.g. **Singapore**)
4. CDN: optional (off is fine for demo)
5. **Settings → CORS** (if needed later for direct browser uploads):

```json
[
  {
    "AllowedOrigins": ["https://field-intelligence-system.vercel.app"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"]
  }
]
```

6. **API → Spaces Keys** → Generate key → save **Access Key** and **Secret**

### Spaces env values (for App Platform)

| Variable | Example |
|----------|---------|
| `STORAGE_BACKEND` | `s3` |
| `S3_BUCKET` | `fieldintel-media` |
| `AWS_REGION` | `sgp1` |
| `S3_ENDPOINT_URL` | `https://sgp1.digitaloceanspaces.com` |
| `AWS_ACCESS_KEY_ID` | Spaces access key |
| `AWS_SECRET_ACCESS_KEY` | Spaces secret |

---

## Part 4 — Migrate database

From your machine (add your IP to DB trusted sources first):

```powershell
$env:DATABASE_URL="postgresql://doadmin:PASSWORD@HOST:25060/defaultdb?sslmode=require"
cd backend
.venv\Scripts\activate
alembic upgrade head
cd ..
python scripts/seed_users.py --force
python scripts/seed_data.py --force
```

Or use the RDS helper with explicit URL:

```powershell
$env:DATABASE_URL="postgresql://..."
python scripts/migrate_to_rds.py --seed
```

(`migrate_to_rds.py` works with any Postgres URL in `DATABASE_URL`.)

Verify: connect with `psql` or DO web console → `\dt` → should see `users`, `visits`, etc.

---

## Part 5 — App Platform (API)

1. **App Platform** → **Create App** → **GitHub** → select this repo
2. **Resource type:** Web Service
3. **Source directory:** `backend`
4. **Type:** Dockerfile (`backend/Dockerfile` is auto-detected)
5. **HTTP port:** `8000`
6. **HTTP request routes:** `/` (default)
7. **Health check path:** `/health`
8. **Instance size:** Basic (512 MB–1 GB RAM)
9. **Environment variables** (Encrypt secrets):

```env
ENVIRONMENT=production
COOKIE_SECURE=true
STORAGE_BACKEND=s3
S3_BUCKET=fieldintel-media
AWS_REGION=sgp1
S3_ENDPOINT_URL=https://sgp1.digitaloceanspaces.com
AWS_ACCESS_KEY_ID=<spaces-key>
AWS_SECRET_ACCESS_KEY=<spaces-secret>
DATABASE_URL=postgresql://doadmin:PASSWORD@HOST:25060/defaultdb?sslmode=require
JWT_SECRET=<random-32-chars>
GEMINI_TRANSCRIBE_API_KEY=<key>
GEMINI_DEBRIEF_API_KEY=<key>
CORS_ORIGINS=https://field-intelligence-system.vercel.app
ALLOW_MANAGER_REGISTRATION=false
```

10. **Attach database:** link the Managed Postgres cluster (DO injects `DATABASE_URL` — you can use that instead of manual entry)
11. **Deploy**

When deploy finishes, copy the URL:

```
https://fieldintel-api-xxxxx.ondigitalocean.app
```

Test:

```
https://fieldintel-api-xxxxx.ondigitalocean.app/health
```

Expected: `{"status":"ok"}`

---

## Part 6 — Vercel (frontend)

1. In `frontend/vercel.json`, replace **`YOUR_DO_APP_URL`** with the App Platform hostname **only** (no `https://`):

```
fieldintel-api-xxxxx.ondigitalocean.app
```

2. Commit and push → Vercel redeploys

3. Vercel env: leave **`VITE_API_URL` empty** (same-origin via rewrites)

4. If using preview URLs, add them to App Platform `CORS_ORIGINS` comma-separated.

### Smoke test

| URL | Expected |
|-----|----------|
| `https://field-intelligence-system.vercel.app/health` | `{"status":"ok"}` |
| Login `worker@ngo.org` | Success (if seeded) |

---

## Part 7 — Decommission AWS (optional)

After DO works:

- Stop ECS service / delete cluster
- Delete ALB, target groups
- Delete RDS (after backup if needed)
- Delete S3 bucket / ECR repo
- Remove temp security group rules

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Login 500, DB errors in logs | `DATABASE_URL` must include `?sslmode=require`; check trusted sources |
| Upload fails | Spaces keys + `S3_ENDPOINT_URL` + bucket name |
| 401 after login | `COOKIE_SECURE=true`, use Vercel HTTPS + rewrites |
| Workers/visits fail, dashboard OK | Vercel rewrite 307 to DO drops cookies — use exact `/workers` + `/visits` rewrites; backend `redirect_slashes=False` + `--proxy-headers` |
| CORS errors | Add exact Vercel URL to `CORS_ORIGINS` |
| `/health` OK, login fails | Seed users; verify `DATABASE_URL` |

---

## Cost estimate (monthly)

| Resource | ~Cost |
|----------|-------|
| Managed Postgres (basic) | $15 |
| App Platform (basic) | $5–12 |
| Spaces | $5 |
| Vercel | Free tier |
| **Total** | **~$25–35** |

---

## Ticket mapping

| ID | Task | Status |
|----|------|--------|
| DO-1 | Managed Postgres + migrate/seed | Manual |
| DO-2 | Spaces bucket + keys | Manual |
| DO-3 | App Platform deploy | Manual |
| DO-4 | Vercel rewrites → DO URL | Update `vercel.json` |
| DO-5 | Production smoke test | Manual |
