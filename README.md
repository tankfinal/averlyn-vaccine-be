# Averlyn Vaccine Tracker — Backend API

FastAPI backend for the Averlyn Vaccine Tracker. Connects to Supabase for data storage and auth.

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# 4. Run the Supabase SQL setup
# Copy scripts/setup_db.sql content into Supabase SQL Editor and run it

# 5. Migrate data from data.json
python -m scripts.migrate_data

# 6. Start the server
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |
| GET | `/api/baby` | Yes | Get baby info |
| GET | `/api/vaccines` | Yes | Get all vaccines |
| GET | `/api/vaccines/{id}` | Yes | Get single vaccine |
| PATCH | `/api/vaccines/{id}` | Yes | Update vaccine done/date |

All `/api/*` endpoints require `Authorization: Bearer <supabase_access_token>`.

## Deploy to Render

- Runtime: Python
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `FRONTEND_URL`, `ALLOWED_EMAILS`
