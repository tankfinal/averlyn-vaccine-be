# Averlyn Vaccine Tracker — Backend API

FastAPI backend for the Averlyn Vaccine Tracker.
Handles vaccine CRUD, auth verification, and connects to Supabase for data storage.

> Live: [averlyn-vaccine-be.onrender.com](https://averlyn-vaccine-be.onrender.com)

## Architecture

```
                         Service Dependency Map

  +-------------------+         +------------------------+
  |    Vercel (FE)    |         |   Google Cloud OAuth   |
  |  React SPA        | -----  |   Client ID + Secret   |
  +-------------------+    |   +------------------------+
           |               |              |
           |               |              |  OAuth consent
           |  API calls    |              v
           |  (Bearer)     |   +------------------------+
           v               |   |   Supabase Auth        |
  +-------------------+    |   |   - Google provider     |
  |   Render (BE)     |    |   |   - Token signing (ES256)
  |   FastAPI         |----+-->|   - get_user() verify   |
  |   Python 3.12     |       +------------------------+
  +-------------------+                  |
           |                             |
           |  Service role key           |  Shared DB
           v                             v
  +----------------------------------------------+
  |              Supabase PostgreSQL               |
  |                                                |
  |  Tables:                                       |
  |  +-----------+  +---------+  +---------------+ |
  |  | vaccines  |  |  baby   |  | allowed_emails| |
  |  | (36 rows) |  | (1 row) |  |   (2 rows)    | |
  |  +-----------+  +---------+  +---------------+ |
  |                                                |
  |  RLS: is_allowed_user() checks JWT email       |
  +----------------------------------------------+
```

## Request Lifecycle

```
  Browser                    Render (FastAPI)              Supabase
     |                            |                           |
     |  GET /api/vaccines         |                           |
     |  Authorization: Bearer xxx |                           |
     |--------------------------->|                           |
     |                            |                           |
     |                            |  auth.get_user(token)     |
     |                            |-------------------------->|
     |                            |                           |
     |                            |  User { email, id }       |
     |                            |<--------------------------|
     |                            |                           |
     |                            |  Check email whitelist    |
     |                            |  (ALLOWED_EMAILS env)     |
     |                            |                           |
     |                            |  SELECT * FROM vaccines   |
     |                            |  (service_role, no RLS)   |
     |                            |-------------------------->|
     |                            |                           |
     |                            |  [vaccine rows]           |
     |                            |<--------------------------|
     |                            |                           |
     |  200 OK + JSON             |                           |
     |<---------------------------|                           |
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/api/baby` | Yes | Get baby info (name, birth_date) |
| GET | `/api/vaccines` | Yes | List all vaccines (ordered by display_order) |
| GET | `/api/vaccines/{id}` | Yes | Get single vaccine |
| PATCH | `/api/vaccines/{id}` | Yes | Update vaccine (done + done_date) |

All `/api/*` endpoints require `Authorization: Bearer <supabase_access_token>`.

### PATCH Validation Rules

| done | done_date | Result |
|------|-----------|--------|
| `true` | provided | OK |
| `true` | `null` | 422 — date required |
| `false` | `null` | OK |
| `false` | provided | 422 — date must be null |

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI app, CORS, router mount, /health
│   ├── config.py             # Pydantic Settings (env vars)
│   ├── dependencies.py       # Supabase client + auth.get_user() verification
│   ├── schemas.py            # Pydantic models (VaccineRead, VaccineUpdate, BabyRead)
│   └── routers/
│       └── vaccines.py       # GET/PATCH endpoints for vaccines and baby
├── scripts/
│   ├── setup_db.sql          # DDL: tables, RLS policies, triggers, seed data
│   └── migrate_data.py       # Import data.json → Supabase
├── requirements.txt
├── .python-version           # 3.12.0 (pinned for Render)
└── .env.example
```

## Auth Strategy

```
  Token arrives (ES256 JWT signed by Supabase)
       |
       v
  supabase.auth.get_user(token)  <-- delegates verification to Supabase
       |
       +-- Invalid token --> 401
       |
       v
  Check email in ALLOWED_EMAILS env var
       |
       +-- Not in list --> 403
       |
       v
  Return { sub, email } to endpoint handler
```

**Why not manual JWT decode?**
New Supabase projects (2025+) sign tokens with ES256, not HS256.
The JWKS endpoint is unreliable. Using `auth.get_user()` is algorithm-agnostic and future-proof.

## Local Development

```bash
# 1. Create virtual environment (Python 3.12)
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# 4. Run the Supabase SQL setup
# Copy scripts/setup_db.sql into Supabase Dashboard > SQL Editor > Run

# 5. Migrate data from data.json (optional, if you have existing data)
python -m scripts.migrate_data

# 6. Start the server
uvicorn app.main:app --reload --port 8000
```

### Environment Variables

| Variable | Example | Note |
|----------|---------|------|
| `SUPABASE_URL` | `https://xxx.supabase.co` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | `eyJhbG...` | **Legacy format only** (`sb_secret_` not supported) |
| `SUPABASE_JWT_SECRET` | `I2pBO3Pz...` | From Supabase > Settings > API |
| `FRONTEND_URL` | `https://averlyn-vaccine-fe.vercel.app` | For CORS whitelist |
| `ALLOWED_EMAILS` | `a@gmail.com,b@gmail.com` | Comma-separated email whitelist |

## Deploy to Render

| Setting | Value |
|---------|-------|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Python Version | Pinned via `.python-version` (3.12.0) |
| Env Vars | Set all 5 variables in Render Dashboard |

## Related

- Frontend: [averlyn-vaccine-fe](https://github.com/tankfinal/averlyn-vaccine-fe)
