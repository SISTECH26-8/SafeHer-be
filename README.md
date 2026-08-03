# SafeHer Backend

REST API backend for **SafeHer** — a women's safety platform providing ML-based safe route recommendations, emergency SOS, and anonymous incident reporting.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-PostGIS-336791?style=flat-square&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Upstash-DC382D?style=flat-square&logo=redis&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/ML-Scikit_Learn-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL + PostGIS (Supabase) |
| ORM & Migrations | SQLAlchemy 2.0 + Alembic |
| Caching & Live Tracking | Redis (Upstash) |
| Machine Learning | Scikit-Learn (RandomForest `.joblib`) |
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

---

## Machine Learning Integration

### Bounding Box Geo-Mocking (Chicago Translation)
The `RandomForest` model used in this MVP was trained on a specific geospatial dataset from the city of Chicago. Tree-based models are incapable of extrapolating beyond their trained spatial bounding boxes. If Indonesian coordinates (e.g., Jakarta/Depok) are fed directly into the model, it will yield unpredictable or arbitrary results because the values are vastly outside its known distribution.

To solve this while preserving route geometry, SafeHer employs a **Relative Geo-Mocking** technique:
1. **Single Points (`/destination-risk`)**: The requested coordinate is mapped directly to a fixed anchor point in downtown Chicago. 
2. **Routes (`/routes/recommend`)**: The origin of the route is mapped to the Chicago anchor. For every subsequent waypoint, the relative delta (distance and direction) from the origin is calculated and applied to the Chicago anchor. 

This effectively "teleports" the entire route to Chicago while preserving its exact shape, scale, and turn-by-turn geometry. The model evaluates the safety of this teleported route against Chicago's spatial crime distribution, serving as a robust Proof-of-Concept for the routing architecture.

### Risk Threshold Calibration
The risk thresholds defined in `geo_config.py` (`70` and `82`) were deliberately designed to center around the Random Forest model's baseline prediction for unknown/quiet areas. 

When spatial data is completely missing for a mocked coordinate (e.g., zero historical crimes recorded in that cell during training), the model outputs a global fallback prediction of **`70.35`**. 

To prevent these unknown or quiet areas from being prematurely flagged as highly dangerous, the thresholds were manually centered around this fallback baseline:
- **`LOW (Green)`**: **`<= 70`** (Model explicitly detects safe historical cell data).
- **`MEDIUM (Yellow)`**: **`71 - 82`** (Acts as the neutral bucket, seamlessly capturing the `70.35` global fallback baseline).
- **`HIGH (Red)`**: **`> 82`** (Model explicitly detects highly dangerous historical cell data, reaching up to the maximum score of ~89).

This ensures a balanced, proportional risk classification where areas lacking data default to a "Medium/Neutral" classification, preventing panic alerts while still punishing explicitly dangerous paths.

### Mapbox Integration & Live Testing
The routing engine utilizes the **Mapbox Directions API** (which natively supports multiple route alternatives via the `alternatives=true` parameter). This ensures we can provide up to 3 distinct routes for any given trip, which are then individually evaluated by our ML model.

You can test the system's dynamic risk evaluation using the following JSON payloads against the `POST /api/v1/trips/routes/recommend` endpoint:

**1. Medium Risk Route (Yellow)**  
*(UI to Cibinong - Leaves the Anchor point, resulting in moderate safety)*
```json
{
  "origin_lat": -6.3606,
  "origin_lon": 106.8285,
  "destination_lat": -6.4715,
  "destination_lon": 106.8488,
  "datetime": "2026-08-02T08:00:00Z"
}
```

**2. High Risk Route (Red)**  
*(UI to Margonda Area - Short trip that stays entirely within the high-risk Anchor bounding box)*
```json
{
  "origin_lat": -6.3606,
  "origin_lon": 106.8285,
  "destination_lat": -6.3650,
  "destination_lon": 106.8300,
}
```

**Note on Alternative Route Risk Variations:**
When requesting multiple routes from Mapbox, you will frequently observe that the alternative routes (`route_1`, `route_2`, etc.) share the same color indicator (e.g., both YELLOW). This is an expected geographic behavior:
- **Parallel Optimization:** Mapbox optimizes routes for time efficiency. Alternative routes are usually parallel streets running closely to each other, rarely making massive cross-city detours.
- **Grid Proximity:** Because the alternatives are geographically adjacent, they intersect the same underlying spatial grids (and distance deltas) when translated to the Chicago crime map by the ML predictor. This results in very similar average risk scores for both routes. Mixed-color routes (e.g., Route 1 Green, Route 2 Yellow) do occur naturally, but typically only when a route's baseline score straddles exactly on the `70` or `82` boundary thresholds.
