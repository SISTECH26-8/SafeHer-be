from fastapi import HTTPException, status


def validation_error(message: str = "Input tidak valid."):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"status": "error", "code": "VALIDATION_ERROR", "message": message},
    )


def invalid_coordinates(message: str = "Format koordinat di luar batas yang diizinkan."):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"status": "error", "code": "INVALID_COORDINATES", "message": message},
    )


def user_already_exists():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"status": "error", "code": "USER_ALREADY_EXISTS", "message": "Email atau nomor telepon sudah terdaftar."},
    )


def auth_missing_token():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"status": "error", "code": "AUTH_MISSING_TOKEN", "message": "Header Authorization tidak ditemukan."},
        headers={"WWW-Authenticate": "Bearer"},
    )


def auth_invalid_token():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"status": "error", "code": "AUTH_INVALID_TOKEN", "message": "Token tidak valid atau format rusak."},
        headers={"WWW-Authenticate": "Bearer"},
    )


def auth_token_expired():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"status": "error", "code": "AUTH_TOKEN_EXPIRED", "message": "Token telah kedaluwarsa. Silakan login ulang."},
        headers={"WWW-Authenticate": "Bearer"},
    )


def auth_invalid_credentials():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"status": "error", "code": "AUTH_INVALID_CREDENTIALS", "message": "Kombinasi email dan password salah."},
    )


def access_denied():
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"status": "error", "code": "ACCESS_DENIED", "message": "Anda tidak memiliki izin untuk mengakses sumber daya ini."},
    )


def trip_not_found():
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"status": "error", "code": "TRIP_NOT_FOUND", "message": "Trip tidak ditemukan atau sudah selesai."},
    )


def sos_session_not_found():
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"status": "error", "code": "SOS_SESSION_NOT_FOUND", "message": "Sesi SOS tidak ditemukan atau sudah berakhir."},
    )


def contact_not_found():
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"status": "error", "code": "CONTACT_NOT_FOUND", "message": "Kontak darurat tidak ditemukan."},
    )


def ml_prediction_failed(message: str = "Model gagal memproses input."):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"status": "error", "code": "ML_PREDICTION_FAILED", "message": message},
    )


def external_api_error(message: str = "Gagal mengambil data dari external API."):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"status": "error", "code": "EXTERNAL_API_ERROR", "message": message},
    )
