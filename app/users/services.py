import re
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.users.models import User
from app.users.schemas import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
import app.users.schemas as schemas
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

def get_user_profile(db: Session, user_id: str):
    from app.users.schemas import UserProfileResponse
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise exc.user_not_found()
    return UserProfileResponse(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone_number=user.phone_number,
        created_at=user.created_at
    )


def update_user_profile(db: Session, user_id: str, data: schemas.UserProfileUpdate):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise exc.user_not_found()
    
    user.full_name = data.full_name
    user.phone_number = _normalize_phone_number(data.phone_number)
    db.commit()
    db.refresh(user)
    
    return schemas.UserProfileUpdateResponse(
        status="success",
        message="Profil berhasil diperbarui",
        user=get_user_profile(db, user_id)
    )

def get_user_preferences(db: Session, user_id: str):
    from app.users.models import UserPreference
    from app.users.schemas import UserPreferenceSchema
    
    # Validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise exc.user_not_found()

    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        try:
            pref = UserPreference(user_id=user_id)
            db.add(pref)
            db.commit()
            db.refresh(pref)
        except IntegrityError:
            db.rollback()
            pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        
    return UserPreferenceSchema(
        priority_main_road=pref.priority_main_road,
        auto_share_sos_to_contacts=pref.auto_share_sos_to_contacts,
        alert_radius_km=pref.alert_radius_km
    )

def update_user_preferences(db: Session, user_id: str, data: schemas.UserPreferenceSchema):
    from app.users.models import UserPreference
    
    # Validate user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise exc.user_not_found()

    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if not pref:
        try:
            pref = UserPreference(user_id=user_id)
            db.add(pref)
            db.commit()
            db.refresh(pref)
        except IntegrityError:
            db.rollback()
            pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        
    pref.priority_main_road = data.priority_main_road
    pref.auto_share_sos_to_contacts = data.auto_share_sos_to_contacts
    pref.alert_radius_km = data.alert_radius_km
    
    db.commit()
    
    return schemas.UserPreferenceUpdateResponse(
        status="success",
        message="Preferensi keamanan berhasil disimpan"
    )
