from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user_id
from app.users import schemas, services

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=schemas.RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    return services.register_user(db, data)

@router.post("/login", response_model=schemas.LoginResponse, status_code=status.HTTP_200_OK)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    return services.login_user(db, data)

@router.get("/me", status_code=status.HTTP_200_OK)
def get_current_user_info(user_id: str = Depends(get_current_user_id)):
    """Test endpoint to verify JWT token."""
    return {"user_id": user_id, "message": "Token Anda valid!"}
