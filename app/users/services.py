import re
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.users.models import User
from app.users.schemas import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core import exceptions as exc

def _normalize_phone_number(phone: str) -> str:
    # Remove spaces and non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    # Normalize +62 or 62 to 0
    if cleaned.startswith('+62'):
        cleaned = '0' + cleaned[3:]
    elif cleaned.startswith('62'):
        cleaned = '0' + cleaned[2:]
    return cleaned

def register_user(db: Session, data: RegisterRequest) -> RegisterResponse:
    email_lower = data.email.lower()
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email_lower).first()
    if existing_user:
        raise exc.user_already_exists()
        
    normalized_phone = _normalize_phone_number(data.phone_number)
    hashed_password = hash_password(data.password)
    
    new_user = User(
        full_name=data.full_name,
        email=email_lower,
        password_hash=hashed_password,
        phone_number=normalized_phone
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise exc.user_already_exists()
    
    return RegisterResponse(
        user_id=new_user.id,
        message="Registrasi berhasil."
    )

def login_user(db: Session, data: LoginRequest) -> LoginResponse:
    email_lower = data.email.lower()
    user = db.query(User).filter(User.email == email_lower).first()
    
    if not user:
        raise exc.auth_invalid_credentials()
        
    if not verify_password(data.password, user.password_hash):
        raise exc.auth_invalid_credentials()
        
    token = create_access_token(str(user.id))
    
    return LoginResponse(
        token=token,
        user={
            "user_id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "phone_number": user.phone_number
        }
    )
    
