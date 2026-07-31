# Backend Implementation Plan — SafeHer Platform
### Women Safety & Smart Protection Platform (MVP V1)

| Versi | Pengarang | Tanggal | Keterangan |
|---|---|---|---|
| 1.0 | - | 2026-07-31 | Dokumen task/blueprint teknis end-to-end untuk implementasi Backend + MLOps |

**Referensi:**
- Product Planning — PM Group 8 (SISTECH 2026)
- Final Project Task — SISTECH 2026
- SafeHer API Contract v1.1
- SISTECH 2026 Session 3 — API Serving & Monitoring

**Tech Stack Final:**

| Komponen | Teknologi | Target Deployment |
|---|---|---|
| Framework Backend & ML Serving | Python 3.11, FastAPI, Uvicorn, `joblib` | render/koyeb/google cloud run |
| Database Relasional & Spasial | PostgreSQL + PostGIS | Supabase |
| Caching & Queue (Asinkron) | Redis | Upstash |
| Model ML | LightGBM (`.joblib`), dilatih dari dataset kriminalitas Chicago | Menyatu di dalam container |
| External API (Pesan Darurat) | WhatsApp Cloud API / Twilio | - |
| External API (Rute) | OSRM (public routing API) | - |

> ⚠️ **CATATAN KRUSIAL — MOCKING DATASET CHICAGO**
> Model LightGBM dilatih dari data kriminalitas Chicago. Semua koordinat *real* pengguna (Jakarta/Depok, dll) **wajib** ditranslasikan ke *bounding box* Chicago sebelum masuk ke `.predict()`. Detail lengkap ada di **Phase 2.4**. Koordinat asli **tidak pernah** dikirim mentah ke model, dan koordinat mock **tidak pernah** dikirim balik ke Frontend.

---

## Cara Menggunakan Dokumen Ini

- Dokumen ini disusun **per Fase → per Stage**. Kerjakan berurutan, jangan lompat — Stage 3.x saling bergantung pada Fase 1 & 2.
- Setiap fitur di Fase 3 memiliki **4 bagian wajib**: Business Logic (step-by-step), API Contract, Edge Cases, dan Definition of Done (DoD).
- Checklist `[ ]` dipakai sebagai tracker progres — centang saat selesai + sudah lolos unit/manual test.
- Semua endpoint **harus 1:1 sama** dengan `SafeHer_API_Contract.pdf` v1.1. Jika ada perubahan kontrak, update dokumen kontrak dulu, baru kode.

---

# Phase 1: Repository & Environment Setup

## 1.1 Branching Strategy (Simplified GitFlow)

```
main        → Production. Hanya menerima merge dari develop (via PR) atau hotfix/*.
develop     → Staging/integration. Basis utama pengerjaan.
feat/<nama-fitur>   → Cabang fitur baru. Dibuat dari develop.
fix/<nama-bug>      → Perbaikan bug hasil testing di develop.
hotfix/<nama-issue> → Perbaikan darurat langsung dari main (untuk production incident).
chore/<nama-task>   → Task non-fitur (setup, dependency bump, refactor kecil).
```

**Alur kerja standar per fitur:**
1. `git checkout develop && git pull`
2. `git checkout -b feat/safe-route-recommendation`
3. Commit kecil & sering (Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`)
4. Push → buka PR ke `develop` → self-review checklist Edge Cases (lihat tiap Stage) → merge (squash).
5. Setelah beberapa fitur stabil di `develop` dan lolos smoke test → PR `develop → main` → tag rilis (`v1.0.0`, dst).

**Contoh nama branch per Stage di dokumen ini:**
- `feat/auth-jwt`
- `feat/emergency-contacts`
- `feat/safe-route-recommendation`
- `feat/chicago-geo-mock`
- `feat/active-navigation-reroute`
- `feat/anonymous-reporting`
- `feat/sos-emergency`
- `feat/batch-retraining-pipeline`
- `feat/api-request-logging`
- `chore/swagger-docs`

**Checklist:**
- [ ] Buat repo `safeher-backend` (private)
- [ ] Set branch protection di `main` dan `develop` (require PR, no direct push)
- [ ] Buat branch `develop` dari `main`

---

## 1.2 Struktur Direktori (Domain-Driven / Module-Based)

Struktur direktori utama dari backend menggunakan **Domain-Driven / Module-Based Architecture**. Dalam arsitektur ini, kode dikelompokkan berdasarkan entitas bisnis (domain) alih-alih berdasarkan fungsinya (layer). Hal ini membuat proyek lebih skalabel ketika fitur bertambah.

```text
safeher-backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py # Kumpulan dependency injection (misal: get_db, auth)
│   │   └── v1/             # Konfigurasi router gabungan (opsional)
│   │
│   ├── core/               # Konfigurasi sistem global
│   │   ├── config.py       # Pydantic BaseSettings
│   │   ├── security.py     # Hashing & JWT
│   │   ├── lifespan.py     # Startup & Shutdown event
│   │   └── exceptions.py   # Global Exception Handler
│   │
│   ├── db/                 # Setup Koneksi Database & Redis
│   │   ├── session.py      # SQLAlchemy Session
│   │   └── redis_client.py # Upstash Client
│   │
│   ├── ml/                 # Integrasi Model ML
│   │   ├── geo_config.py   # Konstanta Geo-Mocking
│   │   ├── geo_mock.py     # Logika translasi titik Jakarta -> Chicago
│   │   ├── model_v1.joblib # LightGBM Model File
│   │   └── predictor.py    # Logika inferensi model
│   │
│   ├── users/              # Domain: Pengguna & Auth
│   │   ├── models.py       # Tabel `User`, `EmergencyContact`
│   │   ├── schemas.py      # Pydantic validasi request/response
│   │   ├── services.py     # Business logic untuk auth & user management
│   │   └── router.py       # Endpoint khusus User (`/users/`, `/auth/`)
│   │
│   ├── trips/              # Domain: Perjalanan & Rute
│   │   ├── models.py       # Tabel `Trip`
│   │   ├── schemas.py      
│   │   ├── services.py     
│   │   └── router.py       
│   │
│   ├── reports/            # Domain: Pelaporan Kejadian
│   │   ├── models.py       # Tabel `Report`
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── router.py
│   │
│   ├── safe_points/        # Domain: Titik Aman
│   │   ├── models.py       # Tabel `SafePoint`
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── router.py
│   │
│   ├── emergency/          # Domain: Darurat & SOS
│   │   ├── models.py       # Tabel `SOSSession`
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── router.py
│   │
│   ├── system/             # Domain: Log & Statistik Global
│   │   ├── models.py       # Tabel `APIRequestLog`, `MLPredictionLog`
│   │   ├── schemas.py
│   │   └── services.py
│   │
│   ├── middlewares/
│   │   └── logging_middleware.py   # general API request logging → DB
│   ├── utils/
│   │   ├── geo.py                  # haversine, validasi lat/lon
│   │   └── time.py                 # ISO-8601 helpers
│   └── main.py             # Entry point aplikasi FastAPI
├── alembic/                        # migration DB (versioned schema)
├── notebooks/
│   └── retrain_evaluation.ipynb    # skrip evaluasi batch/offline
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

**Checklist:**
- [ ] Inisiasi struktur direktori di atas
- [ ] Inisiasi `alembic init alembic` untuk migration DB (jangan andalkan `create_all()` di production)
- [ ] Tambahkan `README.md` berisi cara run lokal (`uvicorn app.main:app --reload`)

---

## 1.3 Dependencies (`requirements.txt`)

```text
# Web Framework & Server
fastapi==0.111.0
uvicorn[standard]==0.30.1
gunicorn==22.0.0
pydantic==2.7.4
pydantic-settings==2.3.4

# Database ORM & PostgreSQL
sqlalchemy==2.0.31
psycopg2-binary==2.9.9
geoalchemy2==0.17.0
alembic==1.13.2

# Redis / Upstash
redis==5.0.7

# Machine Learning & Data Processing
scikit-learn==1.4.1
lightgbm==4.3.0
joblib==1.3.2
numpy==1.26.4
pandas==2.2.1

# Auth & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# HTTP client (OSRM, WhatsApp API)
httpx==0.27.0
tenacity==8.3.0                # retry mechanism untuk external API
```

## 1.4 Environment Variables (`.env.example`)

```ini
# --- App ---
PROJECT_NAME="SafeHer API"
ENVIRONMENT="development"          # development | staging | production
API_V1_PREFIX="/api/v1"
CORS_ORIGINS="http://localhost:5173,https://safeher.app"

# --- Auth ---
SECRET_KEY="your-super-secret-key-change-this"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# --- Database (Supabase Postgres + PostGIS) ---
DATABASE_URL="postgresql://[user]:[password]@[host]:[port]/postgres"

# --- Redis (Upstash) ---
REDIS_URL="rediss://default:[password]@[endpoint]:[port]"
REDIS_SOS_TTL_SECONDS=3600          # auto-expire live location jika SOS lupa di-end

# --- ML Model ---
MODEL_VERSION="v1.0"
MODEL_PATH="app/ml/model_v1.joblib"

# --- External APIs ---
OSRM_BASE_URL="http://router.project-osrm.org"
OSRM_TIMEOUT_SECONDS=5
WHATSAPP_API_KEY="your-wa-api-key"
WHATSAPP_API_BASE_URL="https://graph.facebook.com/v19.0"

# --- Business Rules (yang wajar berbeda per environment, mis. staging vs prod) ---
SAFE_POINT_DEFAULT_RADIUS_KM=2
SOS_TRUSTED_CONTACT_LIMIT=3
TRIP_TRACK_POLL_MIN_INTERVAL_SECONDS=10
```

> ℹ️ **Kenapa Chicago bbox & threshold risiko TIDAK ada di `.env`?**
> `.env` isinya secret (`SECRET_KEY`, `DATABASE_URL`, API key) atau nilai yang *memang* beda per environment (dev/staging/prod). Bounding box Chicago & threshold skor risiko (`LOW/MEDIUM/HIGH`) itu **bukan rahasia** dan **bukan sesuatu yang berubah antar environment** — nilainya melekat ke model yang sedang dipakai (kalau model di-retrain dan bbox/threshold berubah, itu harus tercatat di riwayat Git bareng versi model, bukan diam-diam berubah lewat env var yang gampang lupa di-sync antar environment). Karena itu ditaruh sebagai **konstanta di kode** (lihat `app/ml/geo_config.py` di Phase 2.4) yang ikut di-commit & di-review lewat PR seperti kode lainnya.

**Checklist:**
- [ ] `.env.example` di-commit, `.env` asli masuk `.gitignore`
- [ ] Validasi semua env wajib via `pydantic-settings` (`app/core/config.py`) — app harus **gagal start** (fail-fast) kalau env kritikal kosong, bukan error saat runtime.

---

# Phase 2: Database & Core Configurations

## 2.1 Skema Database (Supabase PostgreSQL + PostGIS)

### Tabel Operasional

| Tabel | Kolom Kunci | Catatan |
|---|---|---|
| `users` | `id (UUID, PK)`, `full_name`, `email (unique)`, `password_hash`, `phone_number`, `created_at` | Password **wajib** di-hash (bcrypt), tidak pernah disimpan/di-log plaintext |
| `emergency_contacts` | `id (UUID, PK)`, `user_id (FK→users)`, `contact_name`, `phone_number`, `relation`, `created_at` | Maks `SOS_TRUSTED_CONTACT_LIMIT` (3) kontak aktif per user (validasi di service layer) |
| `safe_points` | `id (UUID, PK)`, `name`, `type (Enum)`, `geom (Point, SRID 4326)`, `status_lokasi`, `contact_number` | Index **GiST** di kolom `geom` wajib untuk query radius cepat |
| `reports` | `id (UUID, PK)`, `category (Enum)`, `description`, `geom (Point)`, `moderation_status (Enum: PENDING/APPROVED/REJECTED)`, `created_at` | **Tidak ada `user_id`** — anonim by design (lihat FR di Stage 3.4) |
| `trips` | `id (UUID, PK)`, `user_id (FK)`, `route_id`, `start_geom`, `destination_geom`, `status (Enum: ACTIVE/COMPLETED)`, `created_at`, `ended_at` | |
| `sos_sessions` | `id (UUID, PK)`, `user_id (FK)`, `status (Enum: EMERGENCY_ACTIVE/RESOLVED)`, `created_at`, `resolved_at` | Titik lokasi live **tidak** disimpan di sini (lihat 2.3 Redis) |

### Tabel Monitoring (pengganti file `.jsonl` — lihat Session 3 materi MLOps)

| Tabel | Kolom Kunci | Dipakai Untuk |
|---|---|---|
| `ml_prediction_logs` | `request_id`, `timestamp`, `model_version`, `source (live/batch)`, `inputs (JSONB)` *(berisi koordinat asli **dan** mock, waktu, fitur turunan)*, `predicted_score`, `latency_ms` | Dashboard drift, audit debugging |
| `api_request_logs` | `request_id`, `timestamp`, `method`, `path`, `status_code`, `latency_ms`, `user_id (nullable)` | Debug produksi, deteksi endpoint lambat |

### 2.1.1 Entity Relationship (ringkas)

```
users (1) ──< emergency_contacts (N)
users (1) ──< trips (N)
users (1) ──< sos_sessions (N)
reports        → standalone (anonim, tidak terhubung ke users)
safe_points    → standalone (data referensi, di-seed manual/CSV)
```

**Checklist:**
- [ ] Aktifkan ekstensi `postgis` di SQL Editor Supabase: `CREATE EXTENSION IF NOT EXISTS postgis;`
- [ ] Buat migration Alembic untuk semua tabel di atas (jangan pakai `Base.metadata.create_all()` di production)
- [ ] Index: GiST index di `safe_points.geom` dan `reports.geom`; unique index di `users.email`
- [ ] Seed data awal `safe_points` (minimal 10–20 titik area target, misal kampus/kost) untuk demo

## 2.2 Konfigurasi Koneksi Database & ORM

- [ ] `app/db/session.py`: buat `engine` (SQLAlchemy 2.0 style) + `SessionLocal` + dependency `get_db()` (yield + close di `finally`)
- [ ] Gunakan **connection pool kecil** (`pool_size=5, max_overflow=2`) — penting karena target deploy adalah Cloud Run (serverless, banyak instance kecil, jangan sampai exhaust koneksi Supabase pooler)
- [ ] Gunakan Supabase **connection pooler (PgBouncer, port 6543)** untuk `DATABASE_URL`, bukan direct connection (port 5432), agar tahan cold-start & scaling instance

## 2.3 Redis (Upstash) — Live Location & Async Queue

**Struktur key yang dipakai:**

| Key Pattern | Value | TTL |
|---|---|---|
| `sos:{sos_session_id}:location` | JSON `{lat, lon, updated_at}` | `REDIS_SOS_TTL_SECONDS` (auto-expire safety net) |
| `trip:{trip_id}:last_position` | JSON `{lat, lon, updated_at}` | 1 jam |

- [ ] `app/db/redis_client.py`: buat client `redis.from_url(REDIS_URL, decode_responses=True)` sebagai singleton
- [ ] Gunakan Redis **hanya** untuk data *ephemeral* (live tracking). Data permanen (trip metadata, SOS metadata) tetap di Postgres.

## 2.4 Chicago Geo-Mocking Utility (`app/ml/geo_mock.py`) — **KRITIKAL**

### Masalah
Model LightGBM dilatih dari distribusi spasial kota Chicago. Jika koordinat asli pengguna (mis. Jakarta, lat ≈ -6.x) langsung dimasukkan ke `.predict()`, model akan:
1. Melakukan ekstrapolasi jauh di luar distribusi data latih → skor tidak reliabel / bisa error dari `lightgbm` jika ada validasi range fitur.
2. Menghasilkan skor yang secara statistik tidak bermakna (garbage in, garbage out).

### Solusi: Relative Offset Mapping (bukan sekadar 1 titik statis)

❌ **Anti-pattern yang harus dihindari:** memetakan *semua* titik ke satu koordinat tunggal `(41.8781, -87.6298)`. Ini membuat semua waypoint dalam satu rute punya koordinat **identik**, sehingga model tidak bisa membedakan segmen aman vs berisiko dalam rute yang sama — fitur inti "Safe Route Recommendation" jadi tidak berfungsi.

✅ **Pendekatan yang dipakai — anchor + delta offset:**
1. Tetapkan **anchor point** di Chicago (konstanta `ANCHOR_LAT/LON` — lihat `geo_config.py` di bawah).
2. Untuk **satu request** (misal satu pemanggilan `routes/recommend` dengan beberapa waypoint), ambil titik **origin** dari request sebagai titik referensi (`ref_lat, ref_lon`).
3. Untuk setiap titik `(lat, lon)` dalam request tersebut, hitung **delta** relatif terhadap origin:
   `delta_lat = lat - ref_lat`
   `delta_lon = lon - ref_lon`
4. Mock point = `anchor + delta` → seluruh waypoint tetap punya **jarak & bentuk geometri relatif yang sama** seperti rute aslinya, hanya "dipindahkan" ke wilayah Chicago.
5. **Clamp** hasil akhir ke dalam `BBOX_MIN/MAX_LAT/LON` (`geo_config.py`) — jika delta terlalu besar (rute lintas kota, jarak >±0.15° ≈ ±16km), lakukan **scale-down proporsional** terhadap delta sebelum ditambahkan ke anchor, supaya titik tidak jatuh di luar cakupan dataset training.

```python
# app/ml/geo_config.py — KONSTANTA, di-commit ke repo (bukan .env, bukan secret)
# Nilai ini melekat ke model_v1.joblib yang sedang dipakai; kalau model
# di-retrain dan area/threshold berubah, update di sini bareng PR ganti model.

ANCHOR_LAT = 41.8781
ANCHOR_LON = -87.6298
BBOX_MIN_LAT = 41.6445
BBOX_MAX_LAT = 42.0230
BBOX_MIN_LON = -87.9401
BBOX_MAX_LON = -87.5240

RISK_THRESHOLD_LOW_MAX = 33
RISK_THRESHOLD_MEDIUM_MAX = 66      # >66 = HIGH
REROUTE_TRIGGER_THRESHOLD = 67      # skor >= ini saat polling trips/track memicu alert
```

```python
# app/ml/geo_mock.py (pseudocode inti)
from app.ml.geo_config import ANCHOR_LAT, ANCHOR_LON, BBOX_MIN_LAT, BBOX_MAX_LAT, BBOX_MIN_LON, BBOX_MAX_LON

def mock_route_to_chicago(waypoints: list[tuple[float, float]]) -> list[tuple[float, float]]:
    ref_lat, ref_lon = waypoints[0]
    mocked = []
    for lat, lon in waypoints:
        delta_lat, delta_lon = lat - ref_lat, lon - ref_lon
        delta_lat, delta_lon = _scale_if_out_of_bbox(delta_lat, delta_lon)
        mock_lat = clamp(ANCHOR_LAT + delta_lat, BBOX_MIN_LAT, BBOX_MAX_LAT)
        mock_lon = clamp(ANCHOR_LON + delta_lon, BBOX_MIN_LON, BBOX_MAX_LON)
        mocked.append((mock_lat, mock_lon))
    return mocked
```

### Edge Cases Wajib Ditangani
- [ ] **Single-point request** (`GET /ml/destination-risk`, tidak ada "origin lain"): gunakan titik itu sendiri sebagai `ref`, delta = 0 → mock = anchor point persis. Ini valid karena tidak ada geometri relatif yang perlu dijaga.
- [ ] **Determinisme:** fungsi harus *pure* (tanpa random) — input sama → output sama persis, supaya hasil prediksi konsisten & mudah di-debug/reproduce dari log.
- [ ] **Validasi input dulu, mock kemudian:** validasi `lat ∈ [-90,90]`, `lon ∈ [-180,180]` di layer `schemas/` (Pydantic) **sebelum** masuk ke `geo_mock.py` → lempar `INVALID_COORDINATES` jika gagal, jangan biarkan proses mocking menerima input tak valid.
- [ ] **Fitur waktu (`datetime`) TIDAK ikut di-mock.** Jam/hari yang dipakai model tetap memakai waktu lokal asli dari request (WIB), **bukan** dikonversi ke timezone Chicago (CST/CDT) — karena tujuan fitur waktu adalah menangkap pola perilaku "malam hari vs siang hari" pengguna asli, bukan waktu literal Chicago.
- [ ] **Audit trail privasi-aman:** simpan **kedua** koordinat (asli & mock) di `ml_prediction_logs.inputs` untuk keperluan debug tim internal, tapi **response API ke Frontend selalu memakai koordinat asli** — koordinat mock **tidak boleh bocor** ke client manapun.
- [ ] **Rute sangat panjang (>16km delta):** setelah scale-down proporsional, tetap jaga urutan/arah relatif antar waypoint (jangan sampai titik urutan ke-3 malah "mendahului" titik ke-2 secara geometris setelah scaling).
- [ ] Verifikasi manual sebelum lanjut ke Stage 3.2: coba 3–4 pasang koordinat asli (dekat & jauh) → print hasil mock → pastikan (a) selalu jatuh di dalam bbox, (b) input sama selalu hasilkan output sama, (c) jarak relatif antar titik tidak berubah drastis.

## 2.5 Model Loading via `lifespan` (bukan load di setiap request)

- [ ] `app/core/lifespan.py`: load `model_v1.joblib` ke memori sekali saat `startup`, simpan di `app.state.model`
- [ ] Jangan pernah panggil `joblib.load()` di dalam route handler — ini penyebab umum latensi tinggi & cold-start lambat
- [ ] Simpan juga `MODEL_VERSION` di `app.state` agar bisa dicatat konsisten di `ml_prediction_logs.model_version`

## 2.6 Middleware — General API Request Logging

- [ ] `app/middlewares/logging_middleware.py`: intercept semua request/response, catat metadata ke `api_request_logs` secara **asinkron** (pakai `BackgroundTasks` atau `asyncio.create_task`, jangan blocking response utama)
- [ ] Pastikan **body sensitif** (password) tidak pernah masuk ke log (redact field `password` sebelum insert)

## Phase 2 — Checklist Keseluruhan
- [ ] `db/session.py` (SQLAlchemy) siap, koneksi via pooler
- [ ] Semua model ORM & migration Alembic dijalankan (`alembic upgrade head`) sukses di Supabase
- [ ] `middlewares/logging.py` aktif dan tervalidasi (cek 1 request masuk ke `api_request_logs`)
- [ ] `core/lifespan.py` sukses load model, endpoint `/health` mengonfirmasi `model_loaded: true`
- [ ] `ml/geo_mock.py` sudah diverifikasi manual sesuai edge case di atas

---

# Phase 3: Staged Feature Implementation (Core Focus)

> Setiap Stage **wajib** diselesaikan dengan urutan ini karena ada dependency data (mis. Stage 3.2 butuh Auth dari 3.1; Stage 3.3 butuh route dari 3.2).

## Stage 3.1 — Authentication & Emergency Contacts
`branch: feat/auth-jwt`, `feat/emergency-contacts`

### Business Logic (step-by-step)
1. **Register**: validasi format email & password (min length) → cek `USER_ALREADY_EXISTS` via query email/phone → hash password (bcrypt) → insert `users` → return `201`.
2. **Login**: cari user by email → jika tidak ada / password mismatch → `AUTH_INVALID_CREDENTIALS` (401) — **jangan bedakan pesan** antara "email tidak ada" vs "password salah" (mencegah user enumeration) → jika cocok, generate JWT (`sub=user_id`, `exp` sesuai `ACCESS_TOKEN_EXPIRE_MINUTES`) → return `200`.
3. **JWT Middleware/Dependency** (`core/security.py` → `get_current_user`): dipakai sebagai `Depends()` di semua endpoint terproteksi. Decode token → jika header tidak ada → `AUTH_MISSING_TOKEN`; jika signature/format rusak → `AUTH_INVALID_TOKEN`; jika `exp` lewat → `AUTH_TOKEN_EXPIRED`.
4. **Tambah kontak darurat**: validasi `user_id` dari token (bukan dari body!) → cek jumlah kontak existing < `SOS_TRUSTED_CONTACT_LIMIT` → insert `emergency_contacts`.
5. **List kontak darurat**: filter `WHERE user_id = current_user.id` — **wajib** filter by owner, jangan pernah return semua kontak di tabel.

### API Contract

| Method | Route | Request | Response Sukses | Error Spesifik |
|---|---|---|---|---|
| POST | `/api/v1/auth/register` | `full_name, email, password, phone_number` | `201 {user_id, message}` | `VALIDATION_ERROR`, `USER_ALREADY_EXISTS` |
| POST | `/api/v1/auth/login` | `email, password` | `200 {token, user:{user_id, full_name}}` | `AUTH_INVALID_CREDENTIALS` |
| POST | `/api/v1/users/emergency-contacts` 🔒 | `contact_name, phone_number, relation` | `201 {contact_id, message}` | `VALIDATION_ERROR` |
| GET | `/api/v1/users/emergency-contacts` 🔒 | - | `200 {contacts:[...]}` | - |

🔒 = wajib `Authorization: Bearer <token>`

### Edge Cases
- [ ] Email tidak *case-sensitive* saat pengecekan duplikat (`normalize` ke lowercase sebelum simpan & query)
- [ ] Nomor telepon: normalisasi format (misal strip spasi/`+62` vs `0`) agar tidak lolos sebagai "unik" padahal sama
- [ ] Password tidak pernah dikembalikan di response manapun, termasuk endpoint debug/log
- [ ] Batas `SOS_TRUSTED_CONTACT_LIMIT` terlampaui → response error jelas (`VALIDATION_ERROR`, pesan: "Maksimal 3 kontak darurat")
- [ ] Token kedaluwarsa di tengah sesi aktif (misal saat SOS berlangsung) → FE harus diberi sinyal jelas via `AUTH_TOKEN_EXPIRED` supaya tidak silent-fail

### Definition of Done
- [ ] Register → Login → panggil endpoint terproteksi berhasil end-to-end (manual test via Swagger)
- [ ] Password ter-hash di DB (cek langsung via SQL Editor, pastikan bukan plaintext)
- [ ] Coba manual via Swagger: token invalid/expired/missing masing-masing menghasilkan status code & error code yang benar

---

## Stage 3.2 — Safe Route Recommendation & Risk Prediction (Real-Time Inference)
`branch: feat/safe-route-recommendation`, `feat/chicago-geo-mock`

> **Konteks MLOps:** Real-Time Inference — prediksi harus selesai dalam hitungan milidetik–detik karena user menunggu rekomendasi rute saat itu juga.

### Business Logic (step-by-step)

**A. `GET /ml/destination-risk`**
1. Validasi query params `lat, lon, datetime` (format & range).
2. Mock koordinat tujuan ke Chicago (single-point, lihat 2.4).
3. Susun fitur input model (koordinat mock + fitur waktu dari `datetime` asli: jam, hari-dalam-minggu, weekend/weekday).
4. Panggil `model.predict()` → dapatkan skor mentah.
5. Normalisasi skor ke rentang **0–100**, mapping ke `level`/`color_indicator` sesuai threshold di `geo_config.py`:
   - `0–33` → `LOW` / `GREEN`
   - `34–66` → `MEDIUM` / `YELLOW`
   - `67–100` → `HIGH` / `RED`
6. Insert log ke `ml_prediction_logs` (`source="live"`).
7. Return response.

**B. `POST /ml/routes/recommend`**
1. Validasi `origin_lat/lon`, `destination_lat/lon`, `datetime`.
2. Panggil **OSRM** (`services/routing_service.py`) untuk mendapatkan **minimal 2 rute alternatif** (gunakan parameter `alternatives=true` pada OSRM). Gunakan `httpx` dengan **timeout** (`OSRM_TIMEOUT_SECONDS`) dan **retry** (`tenacity`, maks 2x, exponential backoff).
3. Untuk setiap rute: ekstrak waypoints dari geometry OSRM → **sampling** waypoint (jangan evaluasi *setiap* titik geometry mentah OSRM yang bisa ratusan — ambil sampel tiap N meter, misal tiap ±200m, demi performa & biaya inference).
4. Mock **seluruh waypoint dalam satu rute** ke Chicago **sekaligus** (satu `ref` = origin rute tsb) agar geometri relatif terjaga (lihat 2.4).
5. Jalankan `model.predict()` **batch** (bukan loop satu-satu) untuk semua waypoint tersampling → efisien.
6. Hitung `average_risk_score` per rute (mean dari skor semua waypoint tersampling).
7. Tentukan `color_indicator` & `status` teks (mis. "Aman dilalui" / "Berisiko Tinggi") berdasarkan threshold.
8. Tentukan `recommended_route_id` = rute dengan `average_risk_score` **terendah** (bukan otomatis rute tercepat — ini adalah inti value proposition produk).
9. Insert log prediksi (JSONB berisi semua input+output) ke `ml_prediction_logs`.
10. Response memakai **koordinat asli** (waypoints hasil OSRM), bukan koordinat mock.

**C. `GET /safe-points`** (dipakai saat user klik marker Safe Point di peta)
1. Validasi query params `lat, lon, radius_km`.
2. Query `safe_points` dengan filter spasial PostGIS (`ST_DWithin` pada kolom `geom`, dalam radius meter = `radius_km * 1000`).
3. Return daftar safe point beserta `status_lokasi` & `contact_number` apa adanya dari DB (**tidak** melalui model ML — ini murni query spasial, bukan prediksi risiko).

### API Contract

| Method | Route | Request | Response |
|---|---|---|---|
| GET | `/api/v1/ml/destination-risk` 🔒 | Query: `lat, lon, datetime` | `200 {risk_score, level, color_indicator}` |
| POST | `/api/v1/ml/routes/recommend` 🔒 | `origin_lat, origin_lon, destination_lat, destination_lon, datetime` | `200 {recommended_route_id, evaluations:[{route_id, average_risk_score, color_indicator, status, waypoints}]}` |
| GET | `/api/v1/safe-points` 🔒 | Query: `lat, lon, radius_km` | `200 [{safe_id, name, type, lat, lon, status_lokasi, contact_number}]` |

### Edge Cases
- [ ] **OSRM tidak menemukan rute** (mis. koordinat di tengah laut/tidak terjangkau jalan) → tangkap error OSRM → return `EXTERNAL_API_ERROR` (500), jangan biarkan exception mentah bocor ke client.
- [ ] **OSRM hanya mengembalikan 1 rute** (tidak selalu ada alternatif) → sistem tetap harus jalan, `evaluations` berisi 1 elemen saja, `recommended_route_id` = rute itu.
- [ ] **Model gagal / timeout saat predict** → tangkap exception → `ML_PREDICTION_FAILED` (500), **jangan** biarkan seluruh request 500 generic tanpa konteks.
- [ ] **`destination_lat/lon` sama dengan `origin_lat/lon`** → validasi awal, balas `VALIDATION_ERROR` ("origin dan destination tidak boleh sama").
- [ ] **Origin/destination di luar Indonesia atau format tidak masuk akal** → tetap lolos validasi range lat/lon standar, tapi dicatat sebagai potential anomaly di log (tidak perlu blocking, cukup dicatat).
- [ ] **`average_risk_score` dua rute sama persis** → tie-breaker: pilih rute dengan **waktu tempuh OSRM lebih pendek** sebagai `recommended_route_id`.
- [ ] **Datetime di masa lalu jauh / format salah** → validasi ISO-8601 ketat di schema, `VALIDATION_ERROR` jika parsing gagal.
- [ ] Pastikan `model.predict()` dipanggil **batch** untuk semua waypoint sekaligus (bukan loop satu-satu per titik) — ini yang membuat endpoint tetap responsif walau satu rute punya banyak waypoint tersampling.
- [ ] `GET /safe-points`: jika `radius_km` tidak dikirim, pakai default `SAFE_POINT_DEFAULT_RADIUS_KM`; jika tidak ada safe point dalam radius, return array kosong `[]` (bukan error).

### Definition of Done
- [ ] Response `color_indicator` konsisten dengan `risk_score` (tidak pernah GREEN tapi skor 80)
- [ ] `recommended_route_id` selalu merujuk rute dengan skor rata-rata terendah di antara `evaluations`
- [ ] Log `ml_prediction_logs` berisi input asli + mock, bisa direkonstruksi untuk debug
- [ ] Endpoint tetap responsif (<3 detik) untuk rute dengan ±20 waypoint tersampling

---

## Stage 3.3 — Active Navigation & Real-time Reroute Alert (Real-Time Inference)
`branch: feat/active-navigation-reroute`

> **Konteks MLOps:** Real-Time Inference. Ini adalah **fitur ekstra wajib Grup 8** — notifikasi otomatis + rute alternatif saat kondisi rute yang sedang dilalui tiba-tiba berisiko.

### Business Logic (step-by-step)

**A. `POST /trips/start`**
1. Validasi `route_id` valid & milik user (dari hasil `routes/recommend` sebelumnya — cukup validasi format, tidak perlu FK ketat karena `route_id` bersifat sementara/session-based dari OSRM).
2. Insert `trips` dengan `status=ACTIVE`.
3. Return `trip_id`.

**B. `PATCH /trips/{trip_id}/track`** (dipanggil FE via polling, minimal interval `TRIP_TRACK_POLL_MIN_INTERVAL_SECONDS`)
1. Validasi `trip_id` exists & `status=ACTIVE` & milik `current_user` → jika tidak → `TRIP_NOT_FOUND` / `ACCESS_DENIED`.
2. Simpan `current_lat/lon` ke Redis (`trip:{trip_id}:last_position`).
3. Query **laporan baru** (`reports`) dalam radius kecil (misal 300m) dari posisi saat ini, dibuat **setelah** trip dimulai (`reports.created_at > trip.created_at`) — ini adalah trigger utama anomaly selain skor ML.
4. Hitung ulang risk score posisi saat ini via `risk_service` (mock ke Chicago → predict) — **hanya untuk titik searah perjalanan berikutnya**, bukan seluruh rute lagi (efisiensi).
5. **Trigger kondisi reroute** jika **salah satu** terpenuhi:
   - skor risiko titik saat ini/depan ≥ `REROUTE_TRIGGER_THRESHOLD` (konstanta di `geo_config.py`), ATAU
   - ada laporan baru dalam radius dekat rute yang sedang dilalui.
6. Jika trigger aktif: panggil ulang `routing_service` untuk cari rute alternatif dari posisi saat ini ke destination awal trip → pilih rute dengan skor terendah → return `show_popup_alert: true` + `new_safe_route`.
7. Jika tidak trigger: return `is_safe: true, show_popup_alert: false`.

**C. `POST /trips/{trip_id}/end`**
1. Update `status=COMPLETED`, `ended_at=now()`.
2. Hapus/biarkan expire key Redis `trip:{trip_id}:last_position` (TTL sudah handle otomatis, tapi bisa dihapus eksplisit untuk kebersihan).

### API Contract

| Method | Route | Request | Response |
|---|---|---|---|
| POST | `/api/v1/trips/start` 🔒 | `route_id, destination_lat, destination_lon` | `201 {trip_id}` |
| PATCH | `/api/v1/trips/{trip_id}/track` 🔒 | `current_lat, current_lon` | `200 {is_safe, show_popup_alert, alert_message?, new_safe_route?}` |
| POST | `/api/v1/trips/{trip_id}/end` 🔒 | - | `200 {status, message}` |

### Edge Cases
- [ ] **Polling terlalu sering dari FE** (mis. tiap 1 detik) → rate-limit sederhana di service layer berdasarkan `TRIP_TRACK_POLL_MIN_INTERVAL_SECONDS`, agar tidak membanjiri model & DB.
- [ ] **Trip sudah `COMPLETED` tapi FE masih polling** (race condition saat `end` dan `track` hampir bersamaan) → return `TRIP_NOT_FOUND` (404), FE harus berhenti polling.
- [ ] **User mencoba track trip milik user lain** → `ACCESS_DENIED` (403).
- [ ] **Posisi user melompat jauh secara tidak wajar** (GPS jump, mis. >2km dalam <10 detik) → anggap anomaly GPS, jangan langsung trigger reroute alert berdasarkan data ini; log sebagai kejadian tapi skip evaluasi risk untuk titik tsb.
- [ ] **Reroute berulang kali dalam waktu singkat** (rute alternatif juga langsung "berisiko" lagi) → beri **cooldown** (misal 60 detik) sebelum popup alert bisa muncul lagi, agar tidak spam notifikasi ke user yang sedang panik.
- [ ] **Tidak ada rute alternatif yang lebih aman ditemukan** → tetap kirim `show_popup_alert: true` dengan `alert_message` yang menyarankan waspada/ke Safe Point terdekat, bukan software error.

### Definition of Done
- [ ] Simulasi manual: buat laporan baru dekat rute aktif → polling berikutnya harus mengembalikan `show_popup_alert: true`
- [ ] Cooldown reroute teruji (tidak alert setiap polling secara berturut-turut)
- [ ] `trip_id` milik user lain tidak bisa diakses (403 teruji)

---

## Stage 3.4 — Anonymous Reporting
`branch: feat/anonymous-reporting`

### Business Logic (step-by-step)
1. Validasi `category` (harus salah satu enum), `description`, `lat/lon`.
2. **Tidak menyimpan `user_id`/informasi identitas apapun** di record — ambil dari token hanya untuk **rate-limiting** (mis. via Redis counter `report_rate:{user_id}`, bukan disimpan permanen di tabel `reports`).
3. Insert `reports` dengan `moderation_status=PENDING`.
4. Response sukses instan ke user (moderasi berjalan async/manual, tidak memblokir UX).
5. *(Batch job terpisah — lihat Stage 3.6)* laporan yang `APPROVED` yang dipakai untuk heatmap & retraining.

> Catatan: `SafeHer_API_Contract.pdf` v1.1 belum mendefinisikan field upload evidence di `POST /reports` (hanya `category, description, lat, lon`). Kalau fitur upload bukti mau dimasukkan, itu perubahan kontrak dulu (update dokumen API Contract + tambah `python-multipart` & storage service), baru diimplementasikan — bukan diasumsikan dari draft PM.

### API Contract

| Method | Route | Request | Response |
|---|---|---|---|
| POST | `/api/v1/reports` 🔒* | `category, description, lat, lon` | `201 {status, message}` |

\* Autentikasi dipakai **hanya** untuk rate-limiting anti-spam di level aplikasi — **bukan** disimpan sebagai relasi kepemilikan data.

### Edge Cases
- [ ] **Spam/report beruntun dari 1 akun** → rate limit (misal maks 5 laporan/jam per user, via Redis) → jika terlampaui, tolak dengan pesan jelas (tetap generic error code `VALIDATION_ERROR`, jangan bocorkan detail mekanisme anti-spam).
- [ ] **Konsistensi anonimitas**: pastikan tidak ada kolom lain (IP address, session, dsb.) yang secara tidak sengaja disimpan dan bisa dipakai untuk re-identifikasi user pelapor.
- [ ] **`lat/lon` di luar radius wajar Indonesia** (opsional business rule) → tetap terima (sistem generik secara global), cukup dicatat.
- [ ] **Deskripsi kosong/hanya spasi** → `VALIDATION_ERROR` (min length setelah `strip()`).
- [ ] Laporan **tidak langsung** muncul di heatmap publik sebelum `moderation_status=APPROVED` — cegah penyalahgunaan (laporan palsu/fitnah) langsung tampil ke publik.

### Definition of Done
- [ ] Cek langsung di DB: record `reports` tidak mengandung kolom `user_id` atau identitas apapun
- [ ] Rate limit teruji manual (laporan ke-6 dalam 1 jam ditolak)

---

## Stage 3.5 — Emergency Feature (SOS)
`branch: feat/sos-emergency`

### Business Logic (step-by-step)

**A. `POST /emergency/sos`**
1. Validasi `current_lat/lon`.
2. Insert `sos_sessions` (`status=EMERGENCY_ACTIVE`).
3. Simpan lokasi awal ke Redis `sos:{sos_session_id}:location`.
4. Ambil daftar `emergency_contacts` milik user.
5. Trigger **`BackgroundTasks`** FastAPI (async, tidak memblokir response) → `notification_service.send_whatsapp_alert()` ke setiap kontak, berisi nama user + `live_tracking_url`.
6. Return `sos_session_id`, `message`, `live_tracking_url` **segera** (jangan tunggu WA API selesai — response harus instan demi UX darurat).

**B. `PATCH /emergency/sos/{sos_session_id}/location`**
1. Validasi `sos_session_id` exists & `status=EMERGENCY_ACTIVE` → else `SOS_SESSION_NOT_FOUND`.
2. Update key Redis (overwrite, refresh TTL).

**C. `GET /emergency/sos/{sos_session_id}/track`** (diakses publik oleh kontak darurat via link WA — **tanpa JWT**, sesuai Aturan Umum kontrak: "web live tracking" dikecualikan dari autentikasi)
1. Ambil `sos_sessions` by id → jika tidak ada → `SOS_SESSION_NOT_FOUND`.
2. Ambil posisi terakhir dari Redis (fallback: jika key sudah expire karena TTL, gunakan lokasi awal dari saat SOS dibuat di Postgres sebagai fallback minimal, jangan return kosong total).
3. Return status + lokasi terkini.

**D. `POST /emergency/sos/{sos_session_id}/end`**
1. Update `status=RESOLVED`, `resolved_at=now()`.
2. Hapus key Redis terkait.
3. *(Opsional but recommended)* Trigger notifikasi WA "sudah aman" ke kontak darurat.

### API Contract

| Method | Route | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/api/v1/emergency/sos` | 🔒 | `current_lat, current_lon` | `201 {sos_session_id, message, live_tracking_url}` |
| PATCH | `/api/v1/emergency/sos/{id}/location` | 🔒 | `lat, lon` | `200 {status:"updated"}` |
| GET | `/api/v1/emergency/sos/{id}/track` | ❌ Publik | - | `200 {user_name, status, last_updated, current_location}` |
| POST | `/api/v1/emergency/sos/{id}/end` | 🔒 | - | `200 {status, message}` |

### Edge Cases
- [ ] **User tidak punya kontak darurat sama sekali saat SOS ditekan** → tetap buat sesi SOS (jangan blocking!) + tampilkan link tracking, tapi skip pengiriman WA + catat warning di log (fitur SOS harus tetap berfungsi minimal — live tracking link — walau notifikasi kontak gagal).
- [ ] **WhatsApp API gagal/timeout** → jangan sampai bikin endpoint `POST /emergency/sos` gagal/500 — kegagalan notifikasi **tidak boleh** menggagalkan pembuatan sesi SOS itu sendiri (decoupling total via `BackgroundTasks` + try/except + retry via `tenacity`).
- [ ] **User menekan SOS dua kali berturut-turut** (double tap / network retry dari FE) → idempotency sederhana: jika ada sesi `EMERGENCY_ACTIVE` milik user yang sama dalam beberapa detik terakhir, kembalikan sesi yang sudah ada, jangan buat sesi duplikat.
- [ ] **Redis key `sos:*:location` expired** (TTL habis) sebelum sesi di-`end` (user lupa mengakhiri / device mati) → endpoint `track` tetap harus mengembalikan sesuatu yang informatif (fallback ke lokasi awal + tandai "data mungkin tidak terkini"), bukan error 500.
- [ ] **Kontak darurat mengakses link tracking untuk sesi yang sudah `RESOLVED`** → tetap `200`, tapi `status: "RESOLVED"` jelas ditampilkan (bukan error) supaya kontak tahu situasinya sudah aman.
- [ ] **Race condition**: `location` di-update tepat saat `end` dipanggil → gunakan DB transaction / cek status sebelum accept update, tolak update jika status sudah `RESOLVED`.

### Definition of Done
- [ ] SOS trigger → response instan (<500ms) walau WA API lambat (verifikasi via simulasi delay)
- [ ] Link tracking bisa diakses **tanpa login** dan menampilkan lokasi terkini
- [ ] Idempotency double-tap SOS teruji manual

---

## Stage 3.6 — Continual Learning & Model Retraining (Batch Inference / MLOps)
`branch: feat/batch-retraining-pipeline`

> **Konteks MLOps:** Batch Processing, dijalankan terjadwal (lokal/cron), **bukan** per-request.

### Business Logic (step-by-step)
1. Tarik seluruh `reports` dengan `moderation_status = APPROVED` sejak retraining terakhir (batch, bukan satu-satu).
2. Jalankan `notebooks/retrain_evaluation.ipynb` (offline) untuk:
   - Cek **data drift**: bandingkan distribusi fitur baru vs data training awal (PSI/KS test, sesuai materi Session 3).
   - Jika drift signifikan → latih ulang model dengan gabungan data lama + baru.
3. Evaluasi model baru vs model lama (metrik: precision/recall pada label risiko, atau proxy metric yang disepakati) sebelum promosi.
4. Jika model baru lebih baik → simpan sebagai `model_v1.1.joblib` (increment versi, **file-based lightweight registry** — bukan MLflow, sesuai batasan *Out of Scope* materi Session 3).
5. Push ke repo (`app/ml/model_v1.1.joblib`) → update `MODEL_VERSION` di config → deploy ulang (Cloud Run rebuild image).

### Edge Cases
- [ ] **Data baru terlalu sedikit** (mis. <30 laporan baru sejak retrain terakhir) → skip retraining, cukup log ke laporan evaluasi ("insufficient data"), jangan paksa retrain dengan sampel kecil yang bisa menurunkan performa model.
- [ ] **Model baru performanya lebih buruk** dari model lama saat evaluasi offline → **jangan promosikan**, tetap pakai versi lama, catat di catatan retraining.
- [ ] **Rollback**: karena versi model disimpan sebagai file terpisah (`model_v1.joblib`, `model_v1.1.joblib`, ...), rollback cukup mengubah `MODEL_PATH`/`MODEL_VERSION` di env dan redeploy — pastikan minimal **2 versi terakhir** model selalu tersedia di repo, jangan overwrite file lama.

### Definition of Done
- [ ] Skrip retraining bisa dijalankan manual end-to-end tanpa error terhadap data dummy
- [ ] Ada catatan (README/log) prosedur promosi & rollback versi model

---

# Phase 3 — Ringkasan Prioritas Fitur

| Prioritas | Stage | Fitur |
|---|---|---|
| **MUST** | 3.1 | Authentication & Emergency Contacts |
| **MUST** | 3.2 | Safe Route Recommendation & Risk Prediction |
| **MUST** | 3.4 | Anonymous Reporting |
| **MUST** | 3.5 | Emergency Feature (SOS) |
| **MUST (Fitur Ekstra Grup 8)** | 3.3 | Real-time Reroute Notification |
| **SHOULD** | — | Notification Center (di luar cakupan detail dokumen ini — bisa memakai tabel `notifications` sederhana + polling, dikembangkan setelah semua MUST selesai) |
| **Ongoing/MLOps** | 3.6 | Continual Learning & Batch Retraining |

---

# Phase 4: Documentation & Production Readiness

## 4.1 API Documentation (Swagger/OpenAPI)
`branch: chore/swagger-docs`

- [ ] Aktifkan dokumentasi otomatis FastAPI di `http://localhost:8000/docs` (Swagger UI) dan `/redoc`
- [ ] Setiap Pydantic schema (`app/schemas/*.py`) diberi `Field(..., example=...)` agar dokumentasi menampilkan contoh payload nyata (sesuai contoh di `SafeHer_API_Contract.pdf`)
- [ ] Setiap route diberi `summary`, `description`, dan `responses={...}` eksplisit untuk error code kustom (`VALIDATION_ERROR`, `ML_PREDICTION_FAILED`, dst.) agar terlihat di Swagger — jangan andalkan default FastAPI yang hanya menampilkan `422`
- [ ] Tambahkan endpoint `GET /health` (tanpa auth) untuk cek: DB connected, Redis connected, model loaded — dipakai Cloud Run health check

## 4.2 Production Monitoring (Streamlit Dashboard)
- [ ] Dashboard Streamlit terpisah (read-only), query langsung `SELECT * FROM ml_prediction_logs` & `api_request_logs` ke Supabase
- [ ] Metrik minimum: **Prediction Distribution** (drift), **Model Usage** per `model_version`, **Latency** (avg & P95)
- [ ] Deploy ke Streamlit Community Cloud (terpisah dari backend, sesuai arsitektur)

## 4.3 Deployment
- [ ] `Dockerfile` multi-stage (build dependencies → slim runtime image)
- [ ] Deploy ke **Google Cloud Run** (stateless, auto-scaling)
- [ ] Set **min instance ≥ 1** jika budget memungkinkan untuk hindari cold-start pada fitur kritikal (SOS, destination-risk) — jika tidak, komunikasikan efek cold-start ke tim FE agar ada loading state yang aman dari timeout
- [ ] Environment variables di-set via Cloud Run console/secret manager, **jangan** hardcode/commit `.env` asli

## Phase 4 — Checklist Final Sebelum Rilis
- [ ] Semua endpoint di dokumen ini sudah **1:1 cocok** dengan `SafeHer_API_Contract.pdf` v1.1
- [ ] Semua error code di §5 API Contract sudah diimplementasikan dan dicoba manual (tidak ada endpoint yang melempar `500` generic untuk kasus yang seharusnya punya error code spesifik)
- [ ] `geo_mock.py` sudah diverifikasi manual sesuai edge case Phase 2.4
- [ ] `/health` endpoint hijau di environment staging sebelum promote ke `main`
