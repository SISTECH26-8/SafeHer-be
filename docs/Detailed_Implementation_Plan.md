# SafeHer Backend — Detailed Implementation Plan (MVP)
>
> Setiap branch dikerjakan oleh **tepat 1 developer**. Sebuah tugas hanya boleh dimulai jika seluruh dependensinya sudah ter-merge ke `develop`.

---

## 🔀 Git Workflow & Branching Strategy

Untuk mencegah *merge conflict* dan menjaga branch *main* tetap stabil, wajib gunakan alur kerja berikut:

1. **Branch Utama:**
   - `main`: Branch produksi yang stabil. **DILARANG KERAS** melakukan `push` langsung ke branch ini.
   - `develop`: Branch integrasi utama tempat semua fitur baru dikumpulkan dan dites.
2. **Mulai Mengerjakan Fitur:**
   - Pastikan Anda berada di branch `develop` terbaru sebelum membuat branch fitur:
     ```bash
     git checkout develop
     git pull origin develop
     git checkout -b feat/nama-fitur
     ```
3. **Menyelesaikan Fitur:**
   - Lakukan commit dan push ke branch fitur Anda (`git push origin feat/nama-fitur`).
   - Buka GitHub dan buat **Pull Request (PR)** dari branch fitur Anda menuju branch **`develop`**.
   - Tunggu *CodeRabbit* melakukan *review* otomatis. Jika bersih, fitur bisa di-merge ke `develop`.
4. **Deploy ke Production (`main`):**
   - Penggabungan ke `main` HANYA dilakukan jika seluruh fitur MVP sudah selesai, di-test, dan siap dirilis. Alurnya menggunakan PR dari `develop` menuju `main`.

---

## Global Engineering Standards

Aturan ini berlaku untuk semua Stage. Violation adalah alasan yang sah untuk menolak PR.

### A. Error Handling

Gunakan fungsi dari `app/core/exceptions.py`. Jangan gunakan `raise HTTPException(...)` langsung di router atau service.

```python
from app.core import exceptions as exc

exc.trip_not_found()
exc.access_denied()
exc.validation_error("Password minimal 8 karakter")
exc.auth_invalid_credentials()
```

Semua error harus 1:1 sesuai `API_Contract.md`. Fungsi di `exceptions.py` sudah memformat response `{status, code, message}` dengan benar.

---

### B. Autentikasi

Gunakan `Depends(get_current_user_id)` dari `app/api/dependencies.py`. Jangan parse JWT secara manual di router.

```python
@router.post("/endpoint")
def my_handler(user_id: str = Depends(get_current_user_id)):
    ...
```

---

### C. Database Session

Gunakan `Depends(get_db)` dari `app/api/dependencies.py`. Jangan buat `SessionLocal()` manual di router — session tidak akan tertutup jika ada exception.

```python
@router.post("/endpoint")
def my_handler(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.do_something(db, user_id)
```

---

### D. Separation of Concerns

Router hanya memanggil service. Tidak boleh ada query DB, logika bisnis, atau kondisional di dalam fungsi router.

```python
# Benar
@router.post("/register", status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return services.register_user(db, data)
```

Semua logika (query, validasi bisnis, error handling) ada di `services.py`.

---

### E. Validasi Koordinat

Setiap schema yang menerima `lat`/`lon` wajib menggunakan Pydantic validator. Jika validasi gagal, tangkap dan re-raise sebagai `exc.invalid_coordinates()`.

```python
@validator("lat")
def validate_lat(cls, v):
    if not -90 <= v <= 90:
        raise ValueError("Invalid latitude")
    return v
```

---

### F. Alembic — Migrasi Database

Setiap perubahan pada `models.py` (tambah kolom, tabel baru) harus diikuti dengan:
```bash
.\venv\Scripts\alembic revision --autogenerate -m "deskripsi"
.\venv\Scripts\alembic upgrade head
```

Commit file migrasi (`alembic/versions/*.py`) bersama perubahan `models.py` dalam satu commit. Jangan gunakan `Base.metadata.create_all()`.

---

### G. Router Registration — Swagger Visibility

Router **tidak otomatis** muncul di Swagger. Setiap `router.py` yang selesai dibuat **wajib** didaftarkan ke `app/main.py` menggunakan `app.include_router()`:

```python
# app/main.py
from app.users.router import router as users_router
from app.trips.router import router as trips_router

app.include_router(users_router, prefix="/api/v1", tags=["Auth & Users"])
app.include_router(trips_router, prefix="/api/v1", tags=["Trips"])
```

Jika tidak didaftarkan, endpoint tidak akan bisa diakses sama sekali (bukan hanya tidak muncul di docs). Pendaftaran router adalah bagian dari checklist PR setiap Stage.

---

### H. Build Verification

Jalankan sebelum setiap `git push`:
```bash
.\venv\Scripts\python.exe -c "from app.main import app; print('BUILD OK')"
```

Jika output bukan `BUILD OK`, jangan push.

---

### I. Naming Convention

| Item | Convention | Contoh |
|---|---|---|
| Fungsi service | `verb_noun` snake_case | `register_user`, `list_contacts` |
| Schema Request | Suffix `Request` | `RegisterRequest`, `TrackRequest` |
| Schema Response | Suffix `Response` | `LoginResponse`, `TripStartResponse` |
| Router prefix | Sesuai API Contract | `/api/v1/auth`, `/api/v1/trips` |
| Konstanta | UPPER_SNAKE_CASE | `RISK_THRESHOLD_LOW_MAX` |

---



## Peta Dependensi (Gambaran Besar)

```text
[main] ← Sudah selesai
       │
       └──► [feat/auth-jwt]
                  │
                  ├──► [feat/emergency-contacts]
                  │          │
                  │          └──► [feat/sos-emergency]
                  │
                  ├──► [feat/ml-risk-engine] (paralel dengan emergency-contacts)
                  │          │
                  │          └──► [feat/safe-route-recommend]
                  │                     │
                  │                     ├──► [feat/active-navigation]
                  │                     │
                  │                     └──► [feat/safe-points] (dapat paralel)
                  │
                  └──► [feat/anonymous-reporting] (paralel setelah auth)

[feat/logging-monitoring] ← Dikerjakan paling akhir setelah semua fitur selesai
```

---

## Stage 0 — Foundation (Sudah Selesai ✅)
`branch: main`

File yang sudah ada dan **jangan diubah** oleh branch lain tanpa koordinasi:
- `app/core/config.py`, `app/core/security.py`, `app/core/exceptions.py`, `app/core/lifespan.py`
- `app/api/dependencies.py`
- `app/db/session.py`, `app/db/redis_client.py`
- `app/ml/geo_config.py`, `app/ml/geo_mock.py`
- `app/middlewares/logging_middleware.py`
- Semua `*/models.py` di setiap domain
- `alembic/`, `alembic.ini`, `requirements.txt`

---

## Stage 1 — Authentication & JWT
`branch: feat/auth-jwt`

### Dependensi
- -

### Code Focus

**File yang dibuat/diubah:**
- `app/users/schemas.py` — Pydantic schemas
- `app/users/services.py` — Business logic
- `app/users/router.py` — Endpoint handler
- `app/main.py` — Daftarkan `users_router`

**Schemas (`app/users/schemas.py`):**
```python
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str  # min 8 char, validated in service layer
    phone_number: str

class RegisterResponse(BaseModel):
    user_id: UUID
    message: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict  # {user_id, full_name}
```

**Services (`app/users/services.py`):**
- `register_user(db, data: RegisterRequest)` → hash pw → insert `users` → return `user_id`
- `login_user(db, data: LoginRequest)` → query by email → `verify_password` → `create_access_token` → return token

**Router (`app/users/router.py`):**
- `POST /api/v1/auth/register` → `services.register_user()`
- `POST /api/v1/auth/login` → `services.login_user()`

### Aturan & Edge Cases

| Skenario | Handling |
|---|---|
| Email sudah terdaftar | Raise `exc.user_already_exists()` |
| Password < 8 karakter | Raise `exc.validation_error("Password minimal 8 karakter")` |
| Email case-insensitive | Simpan dan query dalam format `.lower()` |
| Phone number format | Strip spasi, normalize ke `08xxx` sebelum simpan |
| Login: email tidak ada | Raise `exc.auth_invalid_credentials()` — **jangan bedakan** dengan "password salah" |
| Login: password salah | Raise `exc.auth_invalid_credentials()` |
| Password di response | **DILARANG KERAS** — tidak boleh ada field `password_hash` di response manapun |

### Checklist Kesiapan PR
- [ ] `POST /auth/register` mengembalikan `201` dengan `user_id` bertipe UUID
- [ ] `POST /auth/login` mengembalikan `200` dengan `token` (JWT valid) dan `user.full_name`
- [ ] Cek di Supabase: kolom `password_hash` berisi bcrypt hash (bukan plaintext)
- [ ] Email duplikat → `400 USER_ALREADY_EXISTS`
- [ ] Password salah → `401 AUTH_INVALID_CREDENTIALS` (pesan sama dengan "email tidak ada")
- [ ] Token valid bisa digunakan di endpoint terproteksi (test manual via Swagger)
- [ ] Token tidak ada → `401 AUTH_MISSING_TOKEN`
- [ ] Token expired/rusak → `401 AUTH_INVALID_TOKEN`

---

## Stage 2A — Emergency Contacts
`branch: feat/emergency-contacts`

### Dependensi
- `feat/auth-jwt` harus ter-merge ✅

### Code Focus

**File yang dibuat/diubah:**
- `app/users/schemas.py` — Tambah schemas kontak
- `app/users/services.py` — Tambah fungsi kontak
- `app/users/router.py` — Tambah 2 endpoint kontak

**Schemas tambahan:**
```python
class EmergencyContactCreate(BaseModel):
    contact_name: str
    phone_number: str
    relation: str | None = None

class EmergencyContactResponse(BaseModel):
    contact_id: UUID
    contact_name: str
    phone_number: str
    relation: str | None

class EmergencyContactListResponse(BaseModel):
    contacts: list[EmergencyContactResponse]
```

**Services tambahan:**
- `add_emergency_contact(db, user_id, data)` → cek jumlah kontak < `SOS_TRUSTED_CONTACT_LIMIT` → insert
- `list_emergency_contacts(db, user_id)` → `WHERE user_id = current_user.id`

**Router tambahan:**
- `POST /api/v1/users/emergency-contacts` 🔒
- `GET /api/v1/users/emergency-contacts` 🔒

### Aturan & Edge Cases

| Skenario | Handling |
|---|---|
| Kontak ke-4 ditambahkan | Raise `exc.validation_error("Maksimal 3 kontak darurat")` |
| `user_id` diambil dari token | **Jangan** ambil `user_id` dari request body — selalu dari `Depends(get_current_user_id)` |
| List kontak user lain | Tidak mungkin — filter selalu `WHERE user_id = current_user_id` |

### Checklist Kesiapan PR
- [ ] `POST` kontak berhasil → `201` dengan `contact_id`
- [ ] `GET` kontak mengembalikan hanya kontak milik user yang sedang login
- [ ] Kontak ke-4 ditolak dengan `400 VALIDATION_ERROR`
- [ ] Request tanpa token → `401 AUTH_MISSING_TOKEN`
- [ ] Tidak ada `user_id` yang bocor di response body kontak

---

## Stage 2B — ML Risk Engine & Geo-Mock (Paralel dengan 2A)
`branch: feat/ml-risk-engine`

### Dependensi
- `feat/auth-jwt` harus ter-merge ✅

### Code Focus

**File yang dibuat:**
- `app/ml/predictor.py` — Logika inferensi model
- `app/system/schemas.py` — Schema untuk logging ML

**`app/ml/predictor.py`:**
```python
def predict_risk_score(model, lat: float, lon: float, dt: datetime) -> float:
    """Single point prediction → returns raw score (0-100)."""
    ...

def predict_batch(model, waypoints: list[tuple], dt: datetime) -> list[float]:
    """Batch prediction for route waypoints → returns list of scores."""
    ...

def score_to_level(score: float) -> tuple[str, str]:
    """Returns (level, color_indicator) tuple."""
    if score <= RISK_THRESHOLD_LOW_MAX:
        return "LOW", "GREEN"
    elif score <= RISK_THRESHOLD_MEDIUM_MAX:
        return "MEDIUM", "YELLOW"
    return "HIGH", "RED"
```

### Aturan & Edge Cases

| Skenario | Handling |
|---|---|
| Model belum di-load | `app.state.model = None` → cek di predictor, raise `exc.ml_prediction_failed()` |
| Input koordinat invalid | Validasi di layer schema/router **sebelum** masuk ke predictor |
| Fitur waktu | Gunakan waktu asli dari request — **JANGAN** konversi ke timezone Chicago |
| Koordinat mock bocor ke response | Predictor mengembalikan skor/level saja — mock hanya masuk ke log |
| Model predict error | Wrap dalam `try/except`, raise `exc.ml_prediction_failed(str(e))` |

### Checklist Kesiapan PR
- [ ] `predict_risk_score()` mengembalikan angka `0–100`
- [ ] `score_to_level()` konsisten: skor ≤33 → GREEN, 34–66 → YELLOW, >66 → RED
- [ ] `predict_batch()` menerima list waypoint, mengembalikan list score (bukan loop satu-satu)
- [ ] Koordinat mock tidak pernah muncul di return value fungsi (hanya di log input JSONB)
- [ ] Unit test untuk `score_to_level()` dengan nilai boundary (33, 34, 66, 67)

---

## Stage 3 — Safe Route & Destination Risk
`branch: feat/safe-route-recommend`

### Dependensi
- `feat/ml-risk-engine` harus ter-merge ✅
- `feat/auth-jwt` harus ter-merge ✅

### Code Focus

**File yang dibuat:**
- `app/trips/schemas.py`
- `app/trips/services.py` — OSRM + ML integration
- `app/trips/router.py`
- `app/safe_points/router.py`

**Endpoints:**
- `GET /api/v1/ml/destination-risk` 🔒
- `POST /api/v1/ml/routes/recommend` 🔒
- `GET /api/v1/safe-points` 🔒

**Schema response `routes/recommend`:**
```python
class RouteEvaluation(BaseModel):
    route_id: str
    average_risk_score: float
    color_indicator: str  # "GREEN"|"YELLOW"|"RED"
    status: str
    waypoints: list[dict]  # [{lat, lon}] — koordinat ASLI dari OSRM

class RecommendResponse(BaseModel):
    recommended_route_id: str
    evaluations: list[RouteEvaluation]
```

### Aturan & Edge Cases

| Skenario | Handling |
|---|---|
| OSRM timeout/error | Raise `exc.external_api_error()` |
| OSRM hanya 1 rute | `evaluations` berisi 1 elemen, tetap jalan |
| 2 rute skor sama | Tie-breaker: pilih rute dengan `duration` OSRM lebih pendek |
| `origin == destination` | Raise `exc.validation_error("Origin dan destination tidak boleh sama")` |
| Waypoints di response | Selalu koordinat **asli** dari OSRM |
| `GET /safe-points` tidak ada hasil | Return `[]` |
| Log ML | Insert ke `ml_prediction_logs` secara async |

### Checklist Kesiapan PR
- [ ] `GET /ml/destination-risk` → `{risk_score, level, color_indicator}` konsisten
- [ ] `POST /ml/routes/recommend`: `recommended_route_id` selalu rute dengan skor terendah
- [ ] Waypoints di response adalah koordinat asli (verifikasi manual)
- [ ] `ml_prediction_logs` terisi dengan kedua koordinat (asli + mock) di kolom `inputs`
- [ ] OSRM 1 rute → tetap jalan
- [ ] OSRM gagal → `500 EXTERNAL_API_ERROR`
- [ ] `GET /safe-points` dengan radius 0 → return `[]`

---

## Stage 4 — Active Navigation & Reroute Alert
`branch: feat/active-navigation`

### Dependensi
- `feat/safe-route-recommend` harus ter-merge ✅

### Code Focus

**File yang diubah:**
- `app/trips/schemas.py` — Tambah schemas trip start/track/end
- `app/trips/services.py` — Tambah trip services
- `app/trips/router.py` — Tambah 3 endpoint trip

**Endpoints:**
- `POST /api/v1/trips/start` 🔒
- `PATCH /api/v1/trips/{trip_id}/track` 🔒
- `POST /api/v1/trips/{trip_id}/end` 🔒

**Logika `track` (paling kritis):**
```
1. Validasi trip: ada, ACTIVE, milik current_user
2. Simpan posisi ke Redis: trip:{trip_id}:last_position
3. Query reports baru (created_at > trip.created_at) dalam radius 300m
4. Hitung risk score titik posisi saat ini via predictor
5. Cek kondisi trigger:
   - risk_score >= REROUTE_TRIGGER_THRESHOLD, ATAU
   - ada report baru dalam radius
6. Jika trigger → cari rute alternatif dari posisi saat ini ke destination trip
7. Return {is_safe, show_popup_alert, alert_message?, new_safe_route?}
```

### Aturan & Edge Cases

| Skenario | Handling |
|---|---|
| Trip sudah `COMPLETED` tapi FE masih poll | Raise `exc.trip_not_found()` |
| Track trip milik user lain | Raise `exc.access_denied()` |
| GPS jump (>2km dalam <10 detik) | Skip evaluasi risk, return `is_safe: true`, log anomaly |
| Reroute alert spam | Cooldown 60 detik via Redis `last_alert_at:{trip_id}` |
| Tidak ada rute alternatif lebih aman | Tetap kirim `show_popup_alert: true` + saran ke Safe Point |

### Checklist Kesiapan PR
- [ ] `POST /trips/start` → `201` dengan `trip_id`
- [ ] `PATCH /trips/{trip_id}/track` (aman) → `200 {is_safe: true, show_popup_alert: false}`
- [ ] Simulasi: buat laporan baru dekat posisi → polling berikutnya `show_popup_alert: true`
- [ ] Cooldown 60 detik reroute diverifikasi
- [ ] Track trip milik user lain → `403 ACCESS_DENIED`
- [ ] Trip `COMPLETED` di-track → `404 TRIP_NOT_FOUND`
- [ ] `POST /trips/{trip_id}/end` → posisi Redis dihapus/expire

---

## Stage 5 — Anonymous Reporting (Paralel dengan Stage 3/4)
`branch: feat/anonymous-reporting`

### Dependensi
- `feat/auth-jwt` harus ter-merge ✅

### Code Focus

**File yang dibuat:**
- `app/reports/schemas.py`
- `app/reports/services.py`
- `app/reports/router.py`

**Endpoint:** `POST /api/v1/reports` 🔒*

**Schema:**
```python
class ReportCreate(BaseModel):
    category: Literal["TINDAK_KRIMINAL", "PELECEHAN_SEKSUAL", "ORANG_MENCURIGAKAN"]
    description: str
    lat: float
    lon: float

    @validator("lat")
    def validate_lat(cls, v):
        if not -90 <= v <= 90: raise ValueError("Invalid latitude")
        return v

    @validator("lon")
    def validate_lon(cls, v):
        if not -180 <= v <= 180: raise ValueError("Invalid longitude")
        return v
```

### Aturan & Edge Cases

| Skenario | Handling |
|---|---|
| Description kosong/hanya spasi | Raise `exc.validation_error("Deskripsi tidak boleh kosong")` |
| Koordinat di luar range | Raise `exc.invalid_coordinates()` |
| > 5 laporan/jam per user | Redis counter — raise `exc.validation_error("Batas laporan per jam terlampaui")` |
| `user_id` di tabel `reports` | **DILARANG** — tidak boleh ada FK ke `users` |

### Checklist Kesiapan PR
- [ ] `POST /reports` → `201 {status: "success", message: "Laporan berhasil terkirim."}`
- [ ] Cek di Supabase: tabel `reports` tidak memiliki `user_id` terisi
- [ ] Laporan ke-6 dalam 1 jam → `400 VALIDATION_ERROR`
- [ ] Koordinat di luar range → `400 INVALID_COORDINATES`
- [ ] Laporan berstatus `PENDING` — tidak langsung tampil di hasil apapun

---

## Stage 6 — SOS Emergency
`branch: feat/sos-emergency`

### Dependensi
- `feat/emergency-contacts` harus ter-merge ✅
- `feat/auth-jwt` harus ter-merge ✅

### Code Focus

**File yang dibuat:**
- `app/emergency/schemas.py`
- `app/emergency/services.py`
- `app/emergency/router.py`

**Endpoints:**
- `POST /api/v1/emergency/sos` 🔒
- `PATCH /api/v1/emergency/sos/{sos_session_id}/location` 🔒
- `GET /api/v1/emergency/sos/{sos_session_id}/track` ❌ Publik
- `POST /api/v1/emergency/sos/{sos_session_id}/end` 🔒

**Alur `POST /sos`:**
```
1. Insert sos_sessions (status=EMERGENCY_ACTIVE)
2. Simpan lokasi awal ke Redis sos:{id}:location
3. Ambil emergency_contacts milik user
4. background_tasks.add_task(send_wa_alerts, ...)
5. Return segera: {sos_session_id, message, live_tracking_url}
```

### Aturan & Edge Cases

| Skenario | Handling |
|---|---|
| User tidak punya kontak darurat | Tetap buat sesi SOS, skip WA, log warning |
| WhatsApp API gagal | Error di-catch dalam `send_wa_alerts` — tidak boleh membuat `/sos` jadi 500 |
| Double-tap SOS | Cek sesi `EMERGENCY_ACTIVE` milik user dalam 10 detik — return sesi yang ada |
| Redis key expire sebelum `end` | `GET /track` fallback ke lokasi awal dari Postgres + flag "data mungkin tidak terkini" |
| Kontak buka link setelah `RESOLVED` | Return `200 {status: "RESOLVED"}` — bukan error |
| Update lokasi di sesi `RESOLVED` | Raise `exc.sos_session_not_found()` |
| `GET /track` | Endpoint **publik** — tidak perlu token |

### Checklist Kesiapan PR
- [ ] `POST /sos` → `201` dengan `sos_session_id` + `live_tracking_url`
- [ ] Response `POST /sos` muncul instan (<500ms) walau WA API lambat
- [ ] `GET /track/{id}` bisa diakses **tanpa token**
- [ ] `GET /track/{id}` sesi RESOLVED → `200 {status: "RESOLVED"}`
- [ ] `PATCH /location` di sesi RESOLVED → `404 SOS_SESSION_NOT_FOUND`
- [ ] Double-tap SOS → hanya 1 sesi yang dibuat
- [ ] Key Redis terhapus setelah `POST /end`

---

## Stage 7 — Logging & Monitoring (Final)
`branch: feat/logging-monitoring`

### Dependensi
- Semua stage di atas harus ter-merge ✅

### Code Focus
- Verifikasi `logging_middleware.py` mencatat semua endpoint
- Verifikasi `ml_prediction_logs` terisi untuk setiap prediksi
- `GET /health` mengembalikan status DB, Redis, dan model

### Checklist Kesiapan PR
- [ ] Hit semua endpoint → `api_request_logs` di Supabase terisi
- [ ] Hit endpoint ML → `ml_prediction_logs.inputs` berisi kedua koordinat
- [ ] `GET /health` → `{status: "ok", model_loaded: true}`
- [ ] Swagger UI (`/docs`) menampilkan semua 15 endpoint dengan deskripsi

---

## Ringkasan Parallelism

| Sprint | Developer 1 | Developer 2 |
|---|---|---|
| 1 | `feat/auth-jwt` | — |
| 2 | `feat/emergency-contacts` | `feat/ml-risk-engine` |
| 3 | `feat/safe-route-recommend` | `feat/anonymous-reporting` |
| 4 | `feat/active-navigation` | `feat/sos-emergency` |
| 5 | `feat/logging-monitoring` | Code review & testing akhir |

> ⚠️ **Aturan Konflik File:** Jika dua branch perlu menyentuh file yang sama (misal `app/main.py` untuk registrasi router), koordinasikan dan lakukan di satu branch saja, atau gunakan rebase setelah branch pertama di-merge.
