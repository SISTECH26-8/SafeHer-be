# SafeHer Backend

REST API backend for **SafeHer** — a women's safety platform providing ML-based safe route recommendations, emergency SOS, and anonymous incident reporting.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)

*If you want to check out the Machine Learning repository for this project, please click [here](https://github.com/SISTECH26-8/SafeHer-ml).*

## Live Deployment Links

- **Main API Deployment:** [https://safeher-be.onrender.com](https://safeher-be.onrender.com)
- **API Documentation (Swagger UI):** [https://safeher-be.onrender.com/docs](https://safeher-be.onrender.com/docs)
- **Monitoring Dashboard:** [https://safeher-be.onrender.com/monitoring](https://safeher-be.onrender.com/monitoring)

## Tech Stack & Components

**1. Cloud Server & Database (Infrastructure)**
* **Application Hosting (Compute):** Render
* **Primary Database:** Supabase (PostgreSQL + PostGIS for spatial calculations)
* **Cache Memory (SOS Sessions):** Upstash (Redis)

**2. External API**
* **Routing & Maps:** Mapbox API (Directions API)
* **WhatsApp SOS Notifications:** Fonnte API (WhatsApp Gateway)

**3. Other Application Components**
* **Backend Framework:** FastAPI (Python) & Uvicorn
* **Machine Learning (MLOps):** RandomForestRegressor & Scikit-Learn (trained using the Chicago Crime Dataset)
* **DB ORM & Migration:** SQLAlchemy, GeoAlchemy2, & Alembic
* **Authentication:** JWT (JSON Web Tokens)

## Project Structure

```text
SafeHer-be/
├── app/
│   ├── api/             # Global dependencies (Auth, DB session)
│   ├── core/            # Config (.env), Security (JWT), Exceptions
│   ├── db/              # SQLAlchemy session, Redis client
│   ├── ml/              # Machine Learning logic (Model, Geo-Mocking)
│   ├── middlewares/     # Global middleware (e.g., API Request Logging)
│   ├── users/           # Endpoints: Register, Login, Profile, Preferences
│   ├── trips/           # Endpoints: Route Recommendations, Start Trip
│   ├── reports/         # Endpoints: Anonymous Incident Reporting
│   ├── safe_points/     # Endpoints: Safe Points
│   ├── emergency/       # Endpoints: Emergency Contacts, Trigger SOS
│   ├── system/          # Endpoints: Monitoring Dashboard & Export Logs
│   └── main.py          # FastAPI Entry point
├── artifacts/           # Dataset & ML Model (.joblib)
├── scripts/             # Utility scripts (API Audit, Data Export)
├── alembic/             # Database migration files
└── requirements.txt
```

## Setup & Running the Project

### 1. Clone & Setup Environment
```bash
git clone https://github.com/SISTECH26-8/SafeHer-be.git
cd SafeHer-be

# Create virtual environment
python -m venv venv

# Activate environment (Choose based on your OS)
.\venv\Scripts\Activate.ps1   # Windows (PowerShell)
source venv/bin/activate      # Mac/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables (`.env`)
Copy the template file and fill in the values (especially DB credentials, Redis, and Mapbox API keys).
```bash
copy .env.example .env   # Windows
cp .env.example .env     # Mac/Linux
```

### 4. Run Database Migrations
Ensure both `DATABASE_URL` and `DIRECT_URL` in `.env` are set correctly (Alembic requires `DIRECT_URL` for migrations when using a Supabase connection pooler). This command will create the tables in Supabase.
```bash
alembic upgrade head
```

### 5. Run the API Server
```bash
uvicorn app.main:app --reload
```
The API will run at: **`http://localhost:8000`**

## API Testing Flow

To test the SafeHer system flow sequentially in Swagger UI (`/docs`) or Postman, follow these phases:

### **Phase 1: Authentication & User Profile**
1. **`POST /api/v1/auth/register`**: Register a new account (provide name, email, password, phone number).
2. **`POST /api/v1/auth/login`**: Login using email & password. You will receive a **JWT Token**. *(Copy this token to use in the Authorization header or the Swagger padlock icon).*
3. **`PUT /api/v1/users/profiles`**: (Optional) Update user profile details.

### **Phase 2: Emergency Setup**
1. **`POST /api/v1/emergency/contacts`**: Add at least 1 emergency contact (name & active phone number to receive SOS WhatsApp messages). Maximum 3 contacts.
2. **`PUT /api/v1/users/preferences`**: (Optional) Configure user preferences (e.g., prioritize main roads).

### **Phase 3: Route Recommendation (Core ML)**
1. **`POST /api/v1/trips/routes/recommend`**: Submit the origin (`origin_lat`, `origin_lon`), destination (`destination_lat`, `destination_lon`), and `datetime`. 
   - *The backend calls the Mapbox API to find alternative routes, extracts the waypoints, and evaluates the risk of each route using the Machine Learning model.*
   - Note the recommended `route_id` in the response.

### **Phase 4: Navigation & SOS Trigger**
1. **`POST /api/v1/trips/start`**: Submit the selected `route_id` along with your start (`start_lat`, `start_lon`) and destination (`destination_lat`, `destination_lon`) coordinates to start the trip. You will receive a `trip_id`.
2. **`POST /api/v1/emergency/sos`**: (Danger Simulation). Hit this endpoint using the `trip_id` and the current coordinates.
   - *The backend creates an SOS session in Redis.*
   - *The backend triggers the Fonnte WhatsApp Gateway to send a WhatsApp message containing the Live Tracking link (based on `FRONTEND_URL`) to the emergency contacts registered in Phase 2.*
3. **`POST /api/v1/emergency/sos/{sos_id}/end`**: (Safety Simulation). End the active SOS emergency session.

### **Phase 5: Extra Features (Safe Points & Reroute)**
1. **Nearby Safe Points (`GET /api/v1/safe-points/nearby`)**: Provide your current location (`lat`, `lon`) via query parameters to find the nearest 24/7 safe locations (e.g., police stations, hospitals, 24h minimarkets).
2. **Anonymous Incident Report (`POST /api/v1/reports`)**: Users can report incidents (e.g., suspicious activity) by submitting the report details (`category`, `description`) along with their coordinates (`lat`, `lon`).
3. **Dynamic Rerouting (`PATCH /api/v1/trips/{trip_id}/track`)**: During active navigation (after Phase 4 step 1), if you continuously ping this endpoint with your current location (`current_lat`, `current_lon`), the backend will monitor your surroundings.
   - *If you walk near a newly submitted anonymous report (from step 2), the system will trigger an **Automatic Reroute** and return a newly generated safer route.*

## Machine Learning Integration

### 1. Bounding Box Geo-Mocking (Chicago Translation)
The `RandomForestRegressor` model used in this MVP was trained specifically on the **Chicago Crime Dataset**. Tree-based models cannot extrapolate data if the locations are far outside the trained spatial bounding box. If Indonesian coordinates (e.g., Jakarta/Depok) are provided directly, the model will break or yield arbitrary values.

To resolve this, SafeHer employs a **Relative Geo-Mocking** technique:
1. The user's origin point (e.g., UI Depok) is directly translated to the **center point of Chicago (Anchor Point)**.
2. For every step or turn in the Mapbox route, the original distance and direction are preserved, and then applied relative to the Chicago anchor point.
3. *Result:* The user's route is effectively "teleported" to the center of Chicago as a whole (the route shape and travel distance are identical), allowing the ML model to evaluate its risk level accurately.

### 2. Why is the Average Prediction Score Always High (~73)?
When hitting the route recommendation endpoint, you may notice that the `average_risk_score` consistently sits around ~73 to 80+. 

This occurs because the selected *Anchor* point (the teleportation center) is located exactly in **Downtown Chicago (The Loop)**. Downtown Chicago is an extremely dense urban area with historically high crime rates. Consequently, any route teleported there will overlap with these high-risk hotspots, causing the baseline risk score to be naturally inflated.

### 3. Risk Threshold Calibration
Because the risk scores are inherently concentrated at higher values due to the Chicago downtown effect, the thresholds in `geo_config.py` were recalibrated:

- **LOW (Green) - Score `<= 70`**: Route is very safe.
- **MEDIUM (Yellow) - Score `> 70 and <= 82`**: Route is neutral/cautionary. (The average route will fall into this category due to the Chicago downtown effect).
- **HIGH (Red) - Score `> 82`**: Route is highly dangerous. The model detected extreme crime areas.

This calibration ensures that not all streets are immediately flagged as red (panic-inducing) just because they are teleported to the city center, while still providing accurate warnings when the user passes through genuinely high-crime streets.
