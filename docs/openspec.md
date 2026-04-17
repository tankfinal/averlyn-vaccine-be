# OpenSpec: Averlyn Vaccine Tracker — Full Stack Upgrade

## 1. Overview

Migrate the Averlyn Vaccine Tracker from a pure static site (HTML + CSS + JS on GitHub Pages) to a full-stack application with authenticated editing capabilities.

| Layer | Current | Target |
|-------|---------|--------|
| Frontend | Static HTML/CSS/JS (`index.html`, `style.css`, `app.js`) | React (Vite) on **Vercel** |
| Backend | None (data embedded in `data.json`) | Python **FastAPI** on **Render** (free tier) |
| Database | Static `data.json` (35 vaccine records) | **Supabase** PostgreSQL |
| Auth | None | **Supabase Auth** with Google OAuth |
| Domain | GitHub Pages | Vercel (frontend) + Render (backend API) |

**Baby info**: Averlyn, born 2025-12-03.

---

## 2. User Stories

| # | As a... | I want to... | So that... |
|---|---------|-------------|-----------|
| US-1 | Visitor (unauthenticated) | View all vaccine cards, filter by category, expand details | I can see Averlyn's vaccine schedule without logging in |
| US-2 | Authenticated user (wife) | Log in with my Google account | I can edit vaccine records securely |
| US-3 | Authenticated user | Mark a vaccine as "done" and input the vaccination date | The record reflects the actual vaccination |
| US-4 | Authenticated user | Undo a "done" vaccine (mark back to "not done") | I can correct mistakes |
| US-5 | Authenticated user | Edit the vaccination date of an already-done vaccine | I can fix a wrong date |
| US-6 | Visitor | See "Last updated: xxx" on each card that has been edited | I know when records were last changed |
| US-7 | System | Record `updated_at` on every edit | Audit trail is maintained |

---

## 3. Current State

### 3.1 File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `/averlyn-vaccine/index.html` | 68 | Single-page HTML shell |
| `/averlyn-vaccine/style.css` | 435 | All styling (CSS custom properties, responsive) |
| `/averlyn-vaccine/app.js` | 254 | Client-side rendering, filtering, age calculation |
| `/averlyn-vaccine/data.json` | 423 | Baby info + 35 vaccine records |

### 3.2 Data Structure (`data.json`)

**Top-level shape:**
```json
{
  "baby": { "name": "Averlyn", "birthDate": "2025-12-03" },
  "vaccines": [ ... ]
}
```

**Vaccine record shape** (line 7-17 as representative example):
```json
{
  "id": "hepb-1",            // string, unique identifier
  "name": "B型肝炎疫苗第1劑",  // string, Chinese display name
  "nameEn": "HepB #1",        // string, English display name
  "type": "public",           // "public" | "self-paid"
  "done": true,               // boolean
  "doneDate": "2025-12-04",   // string (YYYY-MM-DD), present when done=true
  "scheduledDate": null,       // string (YYYY-MM-DD) | null, present when done=false
  "price": 1800,              // number | undefined, only for self-paid
  "subtitle": "...",           // string | undefined
  "description": "...",        // string, always present
  "sideEffects": "...",        // string | undefined
  "notes": "..."              // string | undefined
}
```

**Data summary:**
- Total vaccines: 35
- Done (`done: true`): 10 (lines 7-121, IDs: hepb-1, hepb-2, pcv13-1, dtap-ipv-hib-1, rota-1, rsv, ev71-1, pcv13-2, dtap-ipv-hib-2, rota-2)
- Not done with `scheduledDate`: 19
- Not done with `scheduledDate: null`: 6 (IDs: pcv-3-self, menb-1, menb-2, menb-3 and partially others)

### 3.3 Key Frontend Logic (`app.js`)

- **Lines 1-7**: IIFE wrapper, `TODAY` date, `vaccineData` and `currentFilter` state
- **Lines 10-53**: Helper functions (`monthsDiff`, `daysDiff`, `formatAge`, `formatDate`, `formatPrice`, `ageLabel`)
- **Lines 57-81**: Status logic (`getStatus` returns `done|optional|overdue|upcoming`), `findNextVaccine`, `filterVaccines`
- **Lines 83-147**: `renderCard()` — builds HTML string for a single vaccine card with status badge, type badge, price badge, expand-on-click
- **Lines 158-203**: `renderTimeline()` — groups vaccines by date, renders timeline with age-group headers
- **Lines 205-222**: `updateStats()` — populates stats bar (done count, upcoming count, next countdown)
- **Lines 226-253**: `initFilters()` and `init()` — fetches `data.json`, bootstraps UI

### 3.4 CSS Design Tokens (`style.css`, lines 10-28)

Key variables to preserve in the React rewrite:
```css
--pink: #f8a4b8;    --pink-light: #fce4ec;  --pink-dark: #e91e63;
--cream: #fff8f0;    --green: #66bb6a;       --green-light: #e8f5e9;
--blue: #42a5f5;     --orange: #ffa726;      --radius: 16px;
```
Font: `Quicksand` (Google Fonts, loaded in `index.html` lines 7-9).

---

## 4. Proposed Changes

### 4.1 Supabase Setup

#### 4.1.1 Tables

**Table: `vaccines`**

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `text` | PRIMARY KEY | Matches existing `id` field (e.g. `"hepb-1"`) |
| `name` | `text` | NOT NULL | Chinese name |
| `name_en` | `text` | NOT NULL | English name |
| `subtitle` | `text` | nullable | Optional subtitle |
| `type` | `text` | NOT NULL, CHECK (`type` IN ('public', 'self-paid')) | Funding type |
| `done` | `boolean` | NOT NULL, DEFAULT false | Whether administered |
| `done_date` | `date` | nullable | Actual vaccination date |
| `scheduled_date` | `date` | nullable | Planned date |
| `price` | `integer` | nullable | Cost in TWD (self-paid only) |
| `description` | `text` | NOT NULL | Full description |
| `side_effects` | `text` | nullable | Side effects info |
| `notes` | `text` | nullable | Additional notes |
| `display_order` | `integer` | NOT NULL | Preserve original ordering from data.json |
| `updated_at` | `timestamptz` | NOT NULL, DEFAULT now() | Auto-updated on edit |
| `created_at` | `timestamptz` | NOT NULL, DEFAULT now() | Record creation time |

**Table: `baby`**

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `integer` | PRIMARY KEY, DEFAULT 1 | Single-row table |
| `name` | `text` | NOT NULL | "Averlyn" |
| `birth_date` | `date` | NOT NULL | 2025-12-03 |

> No `users` table needed — Supabase Auth handles user records in `auth.users` internally.

#### 4.1.2 Allowed Users (Email Whitelist)

Only the following two Google accounts may access the application:
- `feverjp751111@gmail.com` (wife)
- `aaa2003.loveyou@gmail.com` (Tank)

**Table: `allowed_emails`**

| Column | Type | Constraints |
|--------|------|-------------|
| `email` | `text` | PRIMARY KEY |

Seed data:
```sql
INSERT INTO allowed_emails (email) VALUES
  ('feverjp751111@gmail.com'),
  ('aaa2003.loveyou@gmail.com');
```

#### 4.1.3 RLS (Row Level Security) Policies

```sql
-- Helper function: check if user email is in allowed list
CREATE OR REPLACE FUNCTION is_allowed_user()
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM allowed_emails
    WHERE email = auth.jwt() ->> 'email'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- vaccines table
ALTER TABLE vaccines ENABLE ROW LEVEL SECURITY;

-- Only allowed users can read
CREATE POLICY "Allowed users read" ON vaccines
  FOR SELECT USING (is_allowed_user());

-- Only allowed users can update
CREATE POLICY "Allowed users update" ON vaccines
  FOR UPDATE USING (is_allowed_user())
  WITH CHECK (is_allowed_user());

-- baby table
ALTER TABLE baby ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allowed users read" ON baby
  FOR SELECT USING (is_allowed_user());

-- allowed_emails table
ALTER TABLE allowed_emails ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allowed users read" ON allowed_emails
  FOR SELECT USING (is_allowed_user());
```

> INSERT and DELETE policies are intentionally omitted — vaccines are seeded via migration, not created/deleted by users.
> The site is fully private. Unauthenticated or non-whitelisted users see only the login page.

#### 4.1.3 Database Function (auto-update `updated_at`)

```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON vaccines
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
```

#### 4.1.4 Supabase Auth Config

- Enable **Google OAuth** provider in Supabase Dashboard > Authentication > Providers
- Required: Google Cloud Console OAuth 2.0 Client ID + Secret
- Redirect URL: `https://<your-vercel-domain>/auth/callback`
- No email/password auth needed

---

### 4.2 Python Backend (FastAPI)

#### 4.2.1 Project Structure

```
averlyn-vaccine-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, lifespan
│   ├── config.py            # Settings (env vars: SUPABASE_URL, SUPABASE_SERVICE_KEY, etc.)
│   ├── dependencies.py      # get_supabase_client, get_current_user
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── vaccines.py      # Vaccine CRUD endpoints
│   │   └── auth.py          # Auth-related endpoints (optional, mostly for token verification)
│   └── schemas.py           # Pydantic models
├── scripts/
│   └── migrate_data.py      # One-time migration from data.json to Supabase
├── requirements.txt
├── render.yaml              # Render deployment config
└── .env.example
```

#### 4.2.2 Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL (e.g. `https://xxx.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Supabase service_role key (for backend-only operations) |
| `SUPABASE_JWT_SECRET` | JWT secret from Supabase for token verification |
| `FRONTEND_URL` | Vercel frontend URL (for CORS) |

#### 4.2.3 Pydantic Schemas (`schemas.py`)

```python
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class VaccineRead(BaseModel):
    id: str
    name: str
    name_en: str
    subtitle: Optional[str]
    type: str                    # "public" | "self-paid"
    done: bool
    done_date: Optional[date]
    scheduled_date: Optional[date]
    price: Optional[int]
    description: str
    side_effects: Optional[str]
    notes: Optional[str]
    display_order: int
    updated_at: datetime
    created_at: datetime

class VaccineUpdate(BaseModel):
    done: bool
    done_date: Optional[date]   # Required when done=True

class BabyRead(BaseModel):
    id: int
    name: str
    birth_date: date
```

#### 4.2.4 Auth Middleware (`dependencies.py`)

```python
from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError

async def get_current_user(authorization: str = Header(...)):
    """
    Extracts and verifies Supabase JWT from Authorization: Bearer <token>.
    Returns the user payload (sub, email, etc.).
    Raises 401 if invalid/expired.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"],
                             audience="authenticated")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

#### 4.2.5 API Endpoints

**Base URL**: `https://<render-service>.onrender.com/api`

| Method | Path | Auth | Request Body | Response | Description |
|--------|------|------|-------------|----------|-------------|
| `GET` | `/api/baby` | Yes (Bearer token) | — | `BabyRead` | Get baby info |
| `GET` | `/api/vaccines` | Yes (Bearer token) | — | `list[VaccineRead]` | Get all vaccines (ordered by `display_order`) |
| `GET` | `/api/vaccines/{id}` | Yes (Bearer token) | — | `VaccineRead` | Get single vaccine |
| `PATCH` | `/api/vaccines/{id}` | Yes (Bearer token) | `VaccineUpdate` | `VaccineRead` | Update vaccine done status + date |

> **ALL endpoints require authentication.** The backend verifies both JWT validity AND that the user's email is in the `allowed_emails` whitelist.

**Detailed endpoint specs:**

---

**`GET /api/baby`**

Response `200`:
```json
{
  "id": 1,
  "name": "Averlyn",
  "birth_date": "2025-12-03"
}
```

---

**`GET /api/vaccines`**

Response `200`:
```json
[
  {
    "id": "hepb-1",
    "name": "B型肝炎疫苗第1劑",
    "name_en": "HepB #1",
    "subtitle": null,
    "type": "public",
    "done": true,
    "done_date": "2025-12-04",
    "scheduled_date": null,
    "price": null,
    "description": "出生24小時內施打...",
    "side_effects": "注射部位紅腫...",
    "notes": "早產兒體重達2,000g...",
    "display_order": 1,
    "updated_at": "2026-04-17T10:00:00+00:00",
    "created_at": "2026-04-17T10:00:00+00:00"
  }
]
```

---

**`PATCH /api/vaccines/{id}`**

Request headers: `Authorization: Bearer <supabase_access_token>`

Request body — mark as done:
```json
{
  "done": true,
  "done_date": "2026-04-15"
}
```

Request body — undo (mark not done):
```json
{
  "done": false,
  "done_date": null
}
```

Validation rules:
- If `done` is `true`, `done_date` MUST be provided (return `422` otherwise)
- If `done` is `false`, `done_date` MUST be `null`
- Vaccine `id` must exist (return `404` otherwise)

Response `200`: returns updated `VaccineRead`

Response `401`: `{ "detail": "Invalid or expired token" }`

Response `404`: `{ "detail": "Vaccine not found" }`

Response `422`: `{ "detail": "done_date is required when marking as done" }`

---

**`main.py` CORS config:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 4.3 React Frontend

#### 4.3.1 Project Structure

```
averlyn-vaccine-frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx                    # Vite entry point
│   ├── App.tsx                     # Root component, routes
│   ├── api/
│   │   └── client.ts              # Axios/fetch wrapper, base URL, auth header injection
│   ├── auth/
│   │   ├── AuthProvider.tsx        # React context: session state, login/logout
│   │   ├── AuthCallback.tsx        # Handles /auth/callback redirect from Google OAuth
│   │   └── supabaseClient.ts      # Supabase JS client init (for auth only)
│   ├── components/
│   │   ├── Header.tsx             # Baby name, age, birth date (replaces index.html lines 15-30)
│   │   ├── StatsBar.tsx           # Done/upcoming/next countdown (replaces index.html lines 33-46)
│   │   ├── FilterBar.tsx          # Filter buttons (replaces index.html lines 49-55)
│   │   ├── Timeline.tsx           # Date-grouped vaccine list (replaces app.js renderTimeline)
│   │   ├── VaccineCard.tsx        # Single vaccine card with expand/collapse (replaces app.js renderCard)
│   │   ├── VaccineEditModal.tsx   # Modal dialog for marking done / editing date
│   │   ├── LoginButton.tsx        # Google login button (shown in header when not authenticated)
│   │   └── UserMenu.tsx           # User avatar + logout (shown in header when authenticated)
│   ├── hooks/
│   │   ├── useVaccines.ts         # Fetch + cache vaccine data, expose mutate functions
│   │   ├── useBaby.ts             # Fetch baby info
│   │   └── useAuth.ts             # Convenience hook for AuthProvider context
│   ├── types/
│   │   └── index.ts               # TypeScript interfaces (Vaccine, Baby, etc.)
│   ├── utils/
│   │   ├── date.ts                # Age calculation, formatting (ported from app.js lines 10-53)
│   │   └── vaccine.ts             # Status logic, sorting (ported from app.js lines 57-81)
│   └── styles/
│       └── index.css              # Global styles (ported from style.css, using same CSS variables)
├── index.html                     # Vite HTML template (minimal)
├── vite.config.ts
├── tsconfig.json
├── package.json
└── .env.example                   # VITE_API_URL, VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY
```

#### 4.3.2 Component Tree

```
App
├── AuthProvider                    (context: session, login, logout)
│   ├── Header
│   │   ├── BabyInfo               (name, age, birth date)
│   │   ├── LoginButton            (when not authenticated)
│   │   └── UserMenu               (when authenticated: avatar, logout)
│   ├── StatsBar                   (done count, upcoming count, next countdown)
│   ├── FilterBar                  (all, public, self-paid, done, upcoming)
│   ├── Timeline
│   │   └── VaccineCard[]          (one per vaccine, expand/collapse)
│   │       └── [edit button]      (visible only when authenticated)
│   ├── VaccineEditModal           (shown on edit button click)
│   └── Footer
```

#### 4.3.3 TypeScript Interfaces (`types/index.ts`)

```typescript
export interface Vaccine {
  id: string;
  name: string;
  name_en: string;
  subtitle: string | null;
  type: "public" | "self-paid";
  done: boolean;
  done_date: string | null;       // "YYYY-MM-DD"
  scheduled_date: string | null;  // "YYYY-MM-DD"
  price: number | null;
  description: string;
  side_effects: string | null;
  notes: string | null;
  display_order: number;
  updated_at: string;             // ISO 8601
  created_at: string;             // ISO 8601
}

export interface Baby {
  id: number;
  name: string;
  birth_date: string;             // "YYYY-MM-DD"
}

export interface VaccineUpdatePayload {
  done: boolean;
  done_date: string | null;       // "YYYY-MM-DD" or null
}
```

#### 4.3.4 State Management

Use **React Query (TanStack Query)** for server state:
- `useQuery(['vaccines'], fetchVaccines)` — GET all vaccines
- `useQuery(['baby'], fetchBaby)` — GET baby info
- `useMutation(updateVaccine, { onSuccess: invalidate(['vaccines']) })` — PATCH vaccine

Local UI state (via `useState`):
- `currentFilter`: string (`"all" | "public" | "self-paid" | "done" | "upcoming"`)
- `expandedCardId`: string | null
- `editingVaccineId`: string | null (controls modal visibility)

#### 4.3.5 Auth Flow (Step by Step)

1. User clicks **LoginButton** in header
2. `LoginButton` calls `supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: '<FRONTEND_URL>/auth/callback' } })`
3. Browser redirects to Google consent screen
4. Google redirects back to `<FRONTEND_URL>/auth/callback` with auth code
5. **AuthCallback** component calls `supabase.auth.exchangeCodeForSession(code)` to obtain session (access_token + refresh_token)
6. **AuthProvider** stores session in state, `supabase.auth.onAuthStateChange` keeps it synced
7. `api/client.ts` reads access_token from AuthProvider context and attaches `Authorization: Bearer <token>` to all PATCH requests
8. When token expires, Supabase JS client auto-refreshes using refresh_token
9. User clicks **Logout** in UserMenu -> calls `supabase.auth.signOut()` -> session cleared

**Key point**: The Supabase JS client is used **only for auth** on the frontend. All data operations go through the FastAPI backend.

---

### 4.4 Data Migration

**Script**: `averlyn-vaccine-api/scripts/migrate_data.py`

Steps:
1. Read `/averlyn-vaccine/data.json`
2. Insert row into `baby` table: `{ id: 1, name: "Averlyn", birth_date: "2025-12-03" }`
3. For each vaccine in `data.json.vaccines` (preserving array order as `display_order`):
   - Map `nameEn` -> `name_en`
   - Map `doneDate` -> `done_date`
   - Map `scheduledDate` -> `scheduled_date`
   - Map `sideEffects` -> `side_effects`
   - Map `price` -> `price` (keep null for missing)
   - Set `display_order` = array index + 1
   - Insert into `vaccines` table

**Field mapping** (camelCase -> snake_case):

| data.json field | DB column |
|----------------|-----------|
| `id` | `id` |
| `name` | `name` |
| `nameEn` | `name_en` |
| `subtitle` | `subtitle` |
| `type` | `type` |
| `done` | `done` |
| `doneDate` | `done_date` |
| `scheduledDate` | `scheduled_date` |
| `price` | `price` |
| `description` | `description` |
| `sideEffects` | `side_effects` |
| `notes` | `notes` |

---

### 4.5 UI/UX Changes

#### 4.5.1 Login Page (Unauthenticated)

**This is a fully private site.** Unauthenticated visitors see ONLY a login page:
- Centered card with baby name "Averlyn" and a subtitle
- "Sign in with Google" button
- Clean, warm design matching the existing pink/cream theme
- If a non-whitelisted Google account logs in, show an error: "抱歉，您沒有存取權限" and a logout button

#### 4.5.2 Main View (Authenticated + Whitelisted)

Visually identical to current site. All existing features preserved:
- Header with baby name, age display (ported from `app.js` lines 24-32)
- Stats bar: done count, upcoming count, next countdown (ported from `app.js` lines 205-222)
- Filter bar: all, public, self-paid, done, upcoming (ported from `app.js` lines 73-81)
- Timeline with date-grouped cards (ported from `app.js` lines 158-203)
- Card expand/collapse on click (currently `onclick="this.classList.toggle('expanded')"` in `app.js` line 125)
- Card status: done (green), upcoming (orange), overdue (red), optional (gray) (ported from `app.js` lines 57-64)
- "NEXT UP" highlight on nearest upcoming vaccine (ported from `app.js` lines 66-71)

**Addition**: Each card that has been edited shows "Last updated: YYYY/MM/DD HH:mm" below the date line.

#### 4.5.2 Authenticated View — Additional UI

When logged in, each **VaccineCard** gets an **edit button** (pencil icon or "Edit" text) visible in the card header area (right side, below badges). This button does NOT appear for unauthenticated visitors.

#### 4.5.3 Edit Flow (Step by Step) — Mark as Done

1. User clicks **edit button** on a vaccine card that is currently `done: false`
2. **VaccineEditModal** opens as a bottom-sheet or centered modal
3. Modal shows:
   - Vaccine name (read-only display)
   - Toggle switch: "Completed" (off by default)
   - Date picker input (disabled until toggle is on)
4. User flips toggle to ON
5. Date picker becomes enabled; default value = today
6. User picks or confirms the date
7. User clicks "Save"
8. Frontend sends `PATCH /api/vaccines/{id}` with `{ "done": true, "done_date": "2026-04-15" }`
9. On success: modal closes, vaccine list refetches, card now shows green "done" status with the vaccination date
10. On error: show inline error message in modal

#### 4.5.4 Edit Flow (Step by Step) — Undo Done

1. User clicks **edit button** on a vaccine card that is currently `done: true`
2. **VaccineEditModal** opens
3. Modal shows:
   - Vaccine name (read-only)
   - Toggle switch: "Completed" (on, showing current done_date)
   - Date picker showing the current `done_date`
4. User flips toggle to OFF
5. Date picker becomes disabled and cleared
6. User clicks "Save"
7. Frontend sends `PATCH /api/vaccines/{id}` with `{ "done": false, "done_date": null }`
8. On success: modal closes, card reverts to upcoming/overdue/optional status

#### 4.5.5 Edit Flow (Step by Step) — Change Date

1. User clicks **edit button** on a `done: true` vaccine
2. Modal opens with toggle ON and current date shown
3. User changes the date in the date picker
4. User clicks "Save"
5. Frontend sends `PATCH /api/vaccines/{id}` with `{ "done": true, "done_date": "2026-04-10" }`
6. On success: card date updates

#### 4.5.6 "Last Updated" Display

- On each VaccineCard, if `updated_at` differs from `created_at` (i.e., the record has been edited), show:
  ```
  Last updated: 2026/04/15 14:30
  ```
- Displayed in `var(--text-light)` color, font-size `0.75rem`, below the existing date line
- Format: `YYYY/MM/DD HH:mm` (local timezone)

---

### 4.6 Deployment

#### 4.6.1 Frontend — Vercel

- Connect Vercel to GitHub repo (frontend repo or monorepo subfolder)
- Framework preset: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Environment variables in Vercel dashboard:
  - `VITE_API_URL` = `https://<render-service>.onrender.com/api`
  - `VITE_SUPABASE_URL` = `https://xxx.supabase.co`
  - `VITE_SUPABASE_ANON_KEY` = Supabase anon/public key

#### 4.6.2 Backend — Render (Free Tier)

- Create a **Web Service** on Render
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables in Render dashboard:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - `SUPABASE_JWT_SECRET`
  - `FRONTEND_URL` (Vercel URL, for CORS)

**Note on Render free tier**: service spins down after 15 minutes of inactivity. First request after sleep may take 30-60 seconds. This is acceptable for a personal/family tool.

#### 4.6.3 Supabase (Free Tier)

- Project created at `app.supabase.com`
- Free tier limits: 500MB database, 50MB file storage, 50K monthly active users (more than enough)
- Pauses after 1 week of inactivity on free tier — consider pinging via Render cron or external monitor if needed

---

## 5. Acceptance Criteria

- [ ] **AC-1**: Visiting the frontend URL without login shows all 35 vaccine cards in the correct order with correct statuses, matching the current static site's appearance
- [ ] **AC-2**: Stats bar shows correct done/upcoming counts and next-vaccine countdown
- [ ] **AC-3**: Filter buttons (all, public, self-paid, done, upcoming) work correctly
- [ ] **AC-4**: Clicking a card expands/collapses its detail section
- [ ] **AC-5**: "NEXT UP" label appears on the nearest upcoming vaccine
- [ ] **AC-6**: Google Login button is visible in the header; clicking it redirects to Google consent and returns authenticated
- [ ] **AC-7**: After login, edit buttons appear on every vaccine card
- [ ] **AC-8**: Clicking edit on a not-done vaccine opens a modal where user can toggle "done" and pick a date; saving updates the record
- [ ] **AC-9**: Clicking edit on a done vaccine allows undoing (toggle off) or changing the date
- [ ] **AC-10**: `done_date` is required when `done=true` (backend returns 422 if missing; frontend prevents submission)
- [ ] **AC-11**: Each edited card shows "Last updated: YYYY/MM/DD HH:mm"
- [ ] **AC-12**: Unauthenticated PATCH requests return 401
- [ ] **AC-13**: All 35 vaccines from `data.json` are correctly migrated to Supabase with no data loss
- [ ] **AC-14**: Frontend is deployed on Vercel and accessible via HTTPS
- [ ] **AC-15**: Backend is deployed on Render and responds to health check
- [ ] **AC-16**: Mobile-responsive layout preserved (max-width 640px container, responsive breakpoint at 420px as in current `style.css` lines 404-429)

---

## 6. Technical Notes

### 6.1 Dependencies

**Frontend (`package.json`)**:
- `react`, `react-dom` (^18 or ^19)
- `@tanstack/react-query` — server state management
- `@supabase/supabase-js` — auth only (not for data fetching)
- `axios` — HTTP client (or use native fetch)
- `react-router-dom` — routing for `/auth/callback`
- TypeScript, Vite

**Backend (`requirements.txt`)**:
- `fastapi`
- `uvicorn[standard]`
- `supabase` (Python Supabase client)
- `python-jose[cryptography]` — JWT verification
- `pydantic`
- `python-dotenv`

### 6.2 Frontend Routes

| Path | Component | Purpose |
|------|-----------|---------|
| `/` | `App` (main page) | Vaccine tracker view |
| `/auth/callback` | `AuthCallback` | Handles OAuth redirect |

### 6.3 Repo Strategy

Two separate repositories (recommended for independent deployment):
- `averlyn-vaccine-fe` — React app on Vercel
- `averlyn-vaccine-be` — FastAPI app on Render

The existing `averlyn-vaccine` repo (static site) can be archived after migration.

### 6.4 CSS Migration Strategy

Port the existing `style.css` as-is into `src/styles/index.css`. The CSS custom properties (`--pink`, `--cream`, etc.) and class names (`.vaccine-card`, `.badge-done`, etc.) should be preserved to maintain visual consistency. Components use these class names directly rather than CSS-in-JS.

### 6.5 Logic Migration Strategy

Port `app.js` utility functions into TypeScript:
- `monthsDiff`, `daysDiff`, `formatAge`, `formatDate`, `formatPrice` -> `src/utils/date.ts`
- `getStatus`, `findNextVaccine`, `filterVaccines` -> `src/utils/vaccine.ts`

These are pure functions and can be ported with minimal changes (add type annotations).

---

## 7. Out of Scope

- **Reset button** — explicitly not needed per user confirmation
- **Adding or deleting vaccines** — only toggling done/undone and editing dates
- **Multi-baby support** — single baby (Averlyn) only
- **Email/password auth** — Google OAuth only
- **Push notifications** — no reminders or alerts
- **Offline support / PWA** — not required
- **i18n** — UI stays in Chinese (Traditional) with English vaccine names
- **User roles / permissions** — any authenticated Google user can edit (no allowlist)
- **Vaccine scheduling logic** — no auto-calculation of next dose dates
- **Print / export** — not required

---

## 8. Open Questions

| # | Question | Impact | Suggested Default |
|---|----------|--------|-------------------|
All open questions have been resolved:

| # | Question | Decision |
|---|----------|----------|
| OQ-1 | Email restriction | **Yes** — whitelist: `feverjp751111@gmail.com`, `aaa2003.loveyou@gmail.com` |
| OQ-2 | Old GitHub Pages site | **Archive** after migration confirmed |
| OQ-3 | Render cold-start | **Accept** for now, add keep-alive later if needed |
| OQ-4 | `updated_at` display | **Only** when `updated_at > created_at` |
| OQ-5 | Repo strategy | **Two repos**: `averlyn-vaccine-fe`, `averlyn-vaccine-be` |
| NEW | Site privacy | **Fully private** — login page for unauthenticated, whitelist-only access |
