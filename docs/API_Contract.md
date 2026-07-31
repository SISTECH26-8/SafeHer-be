SafeHer Platform API Contract 
Versi
Pengarang
Tanggal
Keterangan
 
1.0
Keisha
2026-07-27
v1
1.1
Keisha
2026-07-31
Update flow route recommend.
Penambahan endpoint trips/end, sos/end, dan manajemen kontak darurat.

 
1. Aturan Umum
Format Data: Semua Request dan Response menggunakan application/json.
Autentikasi (JWT): Seluruh endpoint (kecuali register, login, dan akses web live tracking) mewajibkan header Authorization: Bearer <jwt_token>. Pengguna akan diarahkan ke login/register jika belum terautentikasi.
Koordinat: Menggunakan desimal (float) untuk latitude (lat) dan longitude (lon).
Waktu: Menggunakan standar ISO-8601 (contoh: 2026-07-27T20:00:00Z).
Standar Error Response:
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "Deskripsi error yang jelas"
}

2. Endpoint
FLOW 1: Authentication
1. POST /api/v1/auth/register
Deskripsi: Mendaftarkan pengguna baru setelah user mengisi form registrasi dan klik "Daftar".
Request Body:
{
  "full_name": "Raisha Alma",
  "email": "raisha@example.com",
  "password": "securepassword123",
  "phone_number": "081234567890"
}

Response 201 Created:
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Registrasi berhasil, silakan login."
}

2. POST /api/v1/auth/login
Deskripsi: Masuk ke sistem. Jika validasi data berhasil, sistem mengarahkan user ke Home Page.
Request Body:
{
  "email": "raisha@example.com",
  "password": "securepassword123"
}

Response 200 OK:
{ 
  "token": "eyJhbGciOiJIUzI1NiIsInR...",
  "user": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "full_name": "Raisha Alma"
  }
}

3. POST /api/v1/users/emergency-contacts
Deskripsi: Menambahkan kontak darurat (Secondary User) yang akan menerima lokasi saat kondisi darurat.
Request Body:
{
  "contact_name": "Ibu Nur Rani",
  "phone_number": "081987654321",
  "relation": "Ibu"
}

Response 201 Created:
{
  "contact_id": "a3b2c1d4-5678-90ab-cdef-112233445566",
  "message": "Kontak darurat berhasil ditambahkan."
}


FLOW 2: Safe Route & Reroute Alert
Mengakomodasi input tujuan, kalkulasi risk score lokasi tujuan, rekomendasi rute dengan indikator warna, klik marker safe point, dan pop-up peringatan ganti rute.
4. GET /api/v1/ml/destination-risk
Deskripsi: (Langkah: Sistem mengkalkulasikan risk score lokasi tujuan). Mengecek tingkat bahaya di titik tujuan yang diinput user sebelum merencanakan rute.
Query Params: lat (lokasi tujuan), lon (lokasi tujuan), datetime
Response 200 OK:
{ 
  "risk_score": 74,
  "level": "HIGH",
  "color_indicator": "RED"
}

5. POST /api/v1/ml/routes/recommend
Deskripsi: Menerima titik awal dan tujuan. Backend akan memanggil OSRM untuk mendapatkan rute alternatif, mengevaluasi skor keamanan dengan model ML, dan mengembalikan rute beserta indikator warnanya ke FE. 
Request Body:
{
  "origin_lat": -6.3640,
  "origin_lon": 106.8280,
  "destination_lat": -6.3700,
  "destination_lon": 106.8300,
  "datetime": "2026-07-31T21:00:00Z"
}

Response 200 OK:
{
  "recommended_route_id": "route_1",
  "evaluations": [
    {
      "route_id": "route_1",
      "average_risk_score": 30,
      "color_indicator": "GREEN",
      "status": "Aman dilalui",
      "waypoints": [
        {"lat": -6.3640, "lon": 106.8280},
        {"lat": -6.3650, "lon": 106.8290},
        {"lat": -6.3700, "lon": 106.8300}
      ]
    },
    {
      "route_id": "route_2",
      "average_risk_score": 75,
      "color_indicator": "RED",
      "status": "Berisiko Tinggi",
      "waypoints": [
        {"lat": -6.3640, "lon": 106.8280},
        {"lat": -6.3680, "lon": 106.8250},
        {"lat": -6.3700, "lon": 106.8300}
      ]
    }
  ]
}

6. GET /api/v1/safe-points
Deskripsi: (Langkah: User klik marker Safe Point -> Sistem tampilkan info tempat & status lokasi). Mengambil daftar titik aman di sekitar rute/pengguna.
Query Params: lat, lon, radius_km
Response 200 OK:[
  {
    "safe_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Pos Polisi Sektor Beji",
    "type": "POLICE_STATION",
    "lat": -6.3640,
    "lon": 106.8280,
    "status_lokasi": "Buka 24 Jam - Siaga",
    "contact_number": "110"
  }
]

7. POST /api/v1/trips/start
Deskripsi: (Langkah: User klik button "Mulai Navigasi"). Backend mencatat sesi navigasi GPS aktif.
Request Body:
{
  "route_id": "123e4567-e89b-12d3-a456-426614174000", 
  "destination_lat": -6.37, 
  "destination_lon": 106.83
}

Response 201 Created:
{
  "trip_id": "8d3e9b2a-1c4f-4d5e-a9b0-6c7d8e9f0a1b",
}
 
8. PATCH /api/v1/trips/{trip_id}/track
Deskripsi: (Langkah: Apakah di jalan aman? -> Tidak -> Sistem menampilkan Pop-Up Alert untuk mengganti rute). FE melakukan polling lokasi terkini secara berkala.
Request Body:
{
  "current_lat": -6.3645, 
  "current_lon": 106.8288
}

Response 200 OK (Skenario Aman):
{ 
  "is_safe": true,
  "show_popup_alert": false
}

Response 200 OK (Skenario Bahaya - Memicu Pop-Up Ganti Rute):
{
  "is_safe": false,
  "show_popup_alert": true,
  "alert_message": "Bahaya terdeteksi di depan. Silakan ganti rute sekarang.",
  "new_safe_route": [
    {"lat": -6.3650, "lon": 106.8300},
    {"lat": -6.3660, "lon": 106.8310}
  ]
}
 
FLOW 3: Anonymous Reporting & SOS
Mengakomodasi alur "Ada Bahaya?" (Ancaman Rute, Bahaya Sekitar, Darurat).
9. POST /api/v1/reports
Deskripsi: (Langkah: User mengisi form -> User klik tombol Kirim -> Sistem memberikan pop-up modal sukses). Melaporkan bahaya sekitar secara anonim. Backend tidak menyimpan user_id di tabel laporan.
Request Body:
{
  "category": "TINDAK_KRIMINAL",
  "description": "Terdapat tindak pencurian di jalan ini.",
  "lat": -6.3650,
  "lon": 106.8280
}

Response 201 Created:
{
  "status": "success",
  "message": "Laporan berhasil terkirim."
}

10. POST /api/v1/emergency/sos
Deskripsi: (Langkah: Darurat -> Menekan tombol SOS -> Sistem mengirim lokasi kepada kontak darurat). Memicu mode darurat.
Request Body:
{
  "current_lat": -6.3644, 
  "current_lon": 106.8286
}

Response 201 Created:
{  
  "sos_session_id": "c9a8b7d6-e5f4-4321-b1a2-9c8d7e6f5a4b",
  "message": "Lokasi telah dikirim ke kontak darurat Anda.",
  "live_tracking_url": 
  "https://safeher.app/track/c9a8b7d6-e5f4-4321-b1a2-9c8d7e6f5a4b"
}

11. PATCH /api/v1/emergency/sos/{sos_session_id}/location
Deskripsi: (Langkah lanjutan dari SOS). Endpoint untuk di-hit terus-menerus oleh FE untuk memperbarui koordinat Live Location selama mode SOS masih aktif agar keluarga dapat melacak secara akurat.
Request Body: 
{
  "lat": -6.3650, "lon": 106.8290
}

Response 200 OK:
{"status": "updated"}

12. GET /api/v1/emergency/sos/{sos_session_id}/track
Deskripsi: Digunakan oleh halaman Web Tracker untuk mengambil titik lokasi korban secara real-time. Diakses oleh kontak darurat melalui link yang dikirim via WhatsApp. 
Request Body: Tidak ada body, hanya UUID di URL. 

Response 200 OK:
{
  "user_name": "Raisha Alma",
  "status": "EMERGENCY_ACTIVE",
  "last_updated": "2026-07-27T21:05:10Z",
  "current_location": {
    "lat": -6.3650,
    "lon": 106.8290
  }
}

13. POST /api/v1/trips/{trip_id}/end
Deskripsi: Mengakhiri sesi navigasi rute agar sistem berhenti mencatat dan tidak lagi mengharapkan polling lokasi dari user. 
Request Body: Tidak ada body. 

Response 200 OK:
{
  "status": "success",
  "message": "Sesi navigasi telah diakhiri."
}

14. POST /api/v1/emergency/sos/{sos_session_id}/end 
Deskripsi: Mematikan mode darurat SOS. Ini akan menghentikan live tracking sehingga jika kontak darurat membuka link pelacakan, statusnya akan berubah menjadi aman/selesai. 
Request Body: Tidak ada body. 

Response 200 OK:
{
  "status": "success",
  "message": "Mode SOS dinonaktifkan. Anda sudah aman."
}
15. GET /api/v1/users/emergency-contacts 
Deskripsi: Mengambil daftar kontak darurat milik user yang sedang login untuk ditampilkan di halaman profil. 
Request Body: Tidak ada body. 

Response 200 OK:
{
  "contacts": [
    {
      "contact_id": "a3b2c1d4-5678-90ab-cdef-112233445566",
      "contact_name": "Ibu Nur Rani",
      "phone_number": "081987654321",
      "relation": "Ibu"
    }
  ]
}

4. Enum
Parameter
Allowed Values
Desc
color_indicator
["GREEN", "RED", "YELLOW”]
Digunakan pada endpoint evaluasi rute dan risiko destinasi untuk memvisualisasikan tingkat bahaya di FE.
level
["HIGH", "LOW", "MEDIUM”]
Mendeskripsikan tingkat bahaya di lokasi tujuan secara tekstual.
type
["POLICE_STATION", "GAS_STATION", "HOSPITAL", "MINIMARKET"]
Mengklasifikasikan kategori tempat yang dianggap aman pada peta.
category
["TINDAK_KRIMINAL ", "PELECEHAN_SEKSUAL", “ORANG_MENCURIGAKAN”]
Mengelompokkan jenis laporan anonim yang dikirimkan oleh pengguna terkait kondisi lingkungan. 


5. Error Code
HTTP Status
Error Code
Desc
400 (Bad Request)
VALIDATION_ERROR 
Format input tidak sesuai (field kosong, tipe data salah, atau email tidak valid).
INVALID_COORDINATES
Format koordinat di luar batas (-90 s/d 90 untuk latitude, -180 s/d 180 untuk longitude).
USER_ALREADY_EXISTS
Email atau nomor telepon sudah terdaftar di sistem.
401 (Unauthorized)
AUTH_MISSING_TOKEN 
Header Authorization tidak dikirimkan oleh klien pada endpoint yang dilindungi.  
AUTH_INVALID_TOKEN 
Token JWT salah, format rusak, atau bukan diterbitkan oleh sistem backend. 
AUTH_TOKEN_EXPIRED 
Token JWT sudah kedaluwarsa (FE harus mengarahkan user untuk login ulang). 
AUTH_INVALID_CREDENTIALS 
Kombinasi email dan kata sandi yang dimasukkan salah.
403 (Forbidden) 
ACCESS_DENIED 
Pengguna mencoba mengakses sumber daya milik pengguna lain.
404 (Not Found) 
TRIP_NOT_FOUND 
UUID trip_id tidak valid, atau sesi navigasi tsb sudah selesai. 
SOS_SESSION_NOT_FOUND 
UUID sos_session_id tidak valid atau masa pelacakan darurat sudah berakhir. 
CONTACT_NOT_FOUND 
Kontak darurat yang ingin diakses tidak ada di daftar pengguna. 
500 (Server Error) 
INTERNAL_SERVER_ERROR 
Terjadi kesalahan pada sisi BE. 
ML_PREDICTION_FAILED 
Model gagal memproses input atau timeout saat mengalkulasi skor risiko. 
EXTERNAL_API_ERROR 
Gagal mengambil data dari external API. 