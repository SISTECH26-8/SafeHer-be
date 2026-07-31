# SafeHer Backend

REST API backend for **SafeHer** — a women's safety platform providing ML-based safe route recommendations, emergency SOS, and anonymous incident reporting.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-336791?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Upstash-DC382D?style=flat-square&logo=redis&logoColor=white)
![LightGBM](https://img.shields.io/badge/ML-LightGBM-brightgreen?style=flat-square)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + PostGIS (Supabase) |
| ORM & Migrations | SQLAlchemy 2.0 + Alembic |
| Caching & Live Tracking | Redis (Upstash) |
| Machine Learning | LightGBM (`.joblib`) |
| Geo Processing | GeoAlchemy2 + OSRM |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| Emergency Notifications | WhatsApp Cloud API |

---

## Project Structure

```
SafeHer-be/
├── app/
│   ├── api/
│   │   └── dependencies.py      # get_db(), get_current_user_id()
│   ├── core/
│   │   ├── config.py            # Pydantic BaseSettings
│   │   ├── exceptions.py        # Centralized error handlers (per API Contract)
│   │   ├── lifespan.py          # Startup/shutdown events (ML model loading)
│   │   └── security.py          # JWT encode/decode + bcrypt hashing
│   ├── db/
│   │   ├── session.py           # SQLAlchemy engine & session factory
│   │   └── redis_client.py      # Upstash Redis client
│   ├── ml/
│   │   ├── geo_config.py        # Chicago bounding-box constants & risk thresholds
│   │   ├── geo_mock.py          # Coordinate translation: Jakarta → Chicago
│   │   └── predictor.py         # Model inference logic (Phase 3)
│   ├── middlewares/
│   │   └── logging_middleware.py
│   ├── users/                   # Domain: Auth & User management
│   ├── trips/                   # Domain: Navigation & Route
│   ├── reports/                 # Domain: Anonymous Reporting
│   ├── safe_points/             # Domain: Safe Points
│   ├── emergency/               # Domain: SOS & Emergency
│   ├── system/                  # Domain: Logs & Monitoring
│   └── main.py
├── alembic/                     # Database migration files
├── docs/
│   ├── API_Contract.md
│   ├── Backend_Implementation_Plan_SafeHer.md
│   └── Detailed_Implementation_Plan.md
├── .env.example
├── requirements.txt
└── alembic.ini
```

---

## Setup

### 1. Clone & create virtual environment

```bash
git clone <repo-url>
cd SafeHer-be

python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
# source venv/bin/activate    # Linux/Mac
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env
# Fill in the required values in .env (see table below)
```

### 4. Run database migrations

```bash
.\venv\Scripts\alembic upgrade head
```

---

## Running the Server

```bash
# Development with hot-reload
.\venv\Scripts\uvicorn app.main:app --reload

# Production
.\venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

Server runs at `http://127.0.0.1:8000`

| URL | Description |
|---|---|
| `/docs` | Swagger UI — interactive API docs & testing |
| `/redoc` | ReDoc — alternative API documentation |
| `/health` | Health check endpoint (DB, Redis, model status) |

---

## Build Verification

Run before every push to catch broken imports early:

```bash
.\venv\Scripts\python.exe -c "from app.main import app; print('BUILD OK')"
```

---

## Adding Database Migrations

After any change to a `models.py` file:

```bash
.\venv\Scripts\alembic revision --autogenerate -m "short_description"
.\venv\Scripts\alembic upgrade head
```

Always commit the generated migration file together with the `models.py` change in a single commit.

---

## Environment Variables

See `.env.example` for the full list. Required variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Supabase connection pooler URL (port 6543) |
| `DIRECT_URL` | Supabase direct connection URL (port 5432, used by Alembic) |
| `REDIS_URL` | Upstash Redis URL |
| `SECRET_KEY` | Secret key for JWT signing |
| `WHATSAPP_API_KEY` | WhatsApp Cloud API token (required for SOS notifications) |
