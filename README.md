# National Weather Big Data Analytics Platform — Backend

## Folder Structure

```
weather-platform/
├── .env                        # (you create this locally — never commit it)
├── .env.example                # template showing every required variable
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── alembic.ini                 # DB migration config
│
├── app/
│   ├── main.py                 # FastAPI app entrypoint — ONLY wires routers together
│   ├── config.py                # loads .env — every other file imports `settings` from here
│   ├── database.py              # SQLAlchemy engine/session — every model uses this
│   ├── cache.py                  # Redis client — every cache read/write uses this
│   │
│   ├── models/                  # SQLAlchemy table definitions, ONE file per table
│   ├── schemas/                  # Pydantic request/response shapes (not DB tables)
│   ├── api/                       # Route handlers, grouped by who uses them
│   │   ├── routes_public.py       # public dashboard reads
│   │   ├── routes_admin.py        # admin panel actions
│   │   ├── routes_auth.py         # login/token
│   │   └── routes_citizen_report.py
│   │
│   ├── services/                  # Business logic — the verification engine lives here
│   ├── ingestion/                 # One collector file per data source
│   ├── ml/                        # Event classifier + duplicate detector
│   ├── utils/                     # Shared keyword list, logger
│   └── core/                      # Security (password hashing, JWT)
│
├── scheduler/
│   └── run_collectors.py          # cron/Airflow entrypoint — runs all collectors
│
├── dashboard/                     # Frontend (React or Streamlit) — separate from backend
├── tests/                         # Mirrors the app/ structure, one test file per concern
├── migrations/                    # Alembic-generated migration files
└── scripts/
    ├── init_db.py                 # run once to create tables
    └── seed_data.py                # optional demo data
```

## Why this structure keeps changes isolated

- **models/** only defines table shape. Change a column here, nothing outside the DB layer breaks.
- **schemas/** only defines API input/output shape. Change what a request looks like here, without touching how it's stored.
- **api/** only wires HTTP requests to service functions. It should almost never contain real logic.
- **services/** holds the actual verification/scoring logic. Update your scoring weights here — no route, model, or collector needs to change.
- **ingestion/** — every source is its own file implementing the same interface (base_collector.py). Add or fix Reddit's collector without touching IMD's, Windy's, or the queue logic.
- **config.py** is the ONLY file that reads environment variables. Every other file imports `settings` from here — so changing a .env value never requires touching code.

## Setup

```bash
cp .env.example .env          # then fill in your real API keys and DB password
pip install -r requirements.txt
python scripts/init_db.py     # creates all tables
uvicorn app.main:app --reload
```

Or with Docker:
```bash
docker-compose up --build
```

## Adding a new data source (example workflow)

1. Create app/ingestion/telegram_collector.py, inheriting base_collector.py
2. Implement .fetch() returning the normalized event shape
3. Register it in scheduler/run_collectors.py
4. Nothing else needs to change — the verification engine and API layer are source-agnostic

## Starting Process

### Option A: Local & ngrok / Remote Sharing (Recommended)
This runs the frontend server with the built-in API proxy on port **5000** (avoiding VS Code/IDE Live Preview conflict on port 3000) so that **a single ngrok tunnel** (`ngrok http 5000`) works for remote users, mobile devices, and team testing with full backend API connectivity (no Mixed Content / localhost errors):

1. **Terminal 1 — Backend (FastAPI):**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Terminal 2 — Frontend & API Proxy:**
   ```bash
   python serve_frontend.py 5000
   ```

3. **Terminal 3 — ngrok Tunnel (for sharing with team / remote users):**
   ```bash
   ngrok http 5000
   ```
   *Share the generated HTTPS URL (e.g. `https://your-domain.ngrok-free.dev/home.html` or `/login.html`) with anyone. Everything (auth, OTP, registration, citizen reports, maps) works out-of-the-box!*

4. **Local Access:**
   Open browser at: [http://localhost:5000/home.html](http://localhost:5000/home.html)