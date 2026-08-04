from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user_id
from app.users import schemas, services

auth_router = APIRouter(tags=["Authentication"])

@auth_router.post("/register", response_model=schemas.RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    return services.register_user(db, data)

@auth_router.post("/login", response_model=schemas.LoginResponse, status_code=status.HTTP_200_OK)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    return services.login_user(db, data)

@auth_router.get("/me", status_code=status.HTTP_200_OK)
def get_current_user_info(user_id: str = Depends(get_current_user_id)):
    """Test endpoint to verify JWT token."""
    return {"user_id": user_id, "message": "Token Anda valid!"}

users_router = APIRouter(tags=["Account and Safety"])

@users_router.get("/profiles", response_model=schemas.UserProfileResponse, status_code=status.HTTP_200_OK)
def get_profile(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.get_user_profile(db, user_id)

@users_router.put("/profiles", response_model=schemas.UserProfileUpdateResponse, status_code=status.HTTP_200_OK)
def update_profile(data: schemas.UserProfileUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.update_user_profile(db, user_id, data)

@users_router.get("/preferences", response_model=schemas.UserPreferenceSchema, status_code=status.HTTP_200_OK)
def get_preferences(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.get_user_preferences(db, user_id)

@users_router.put("/preferences", response_model=schemas.UserPreferenceUpdateResponse, status_code=status.HTTP_200_OK)
def update_preferences(data: schemas.UserPreferenceSchema, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.update_user_preferences(db, user_id, data)


