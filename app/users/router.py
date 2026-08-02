from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user_id
from app.users import schemas, services

router = APIRouter(tags=["Authentication"])

@router.post("/auth/register", response_model=schemas.RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    return services.register_user(db, data)

@router.post("/auth/login", response_model=schemas.LoginResponse, status_code=status.HTTP_200_OK)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    return services.login_user(db, data)

@router.get("/auth/me", status_code=status.HTTP_200_OK)
def get_current_user_info(user_id: str = Depends(get_current_user_id)):
    """Test endpoint to verify JWT token."""
    return {"user_id": user_id, "message": "Token Anda valid!"}

# emergency contact
@router.post("/users/emergency-contacts", status_code=status.HTTP_201_CREATED, tags=["Emergency Contacts"])
def create_emergency_contact(data: schemas.EmergencyContactCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.add_emergency_contact(db=db, user_id=user_id, data=data)

@router.get("/users/emergency-contacts", response_model=schemas.EmergencyContactListResponse, status_code=status.HTTP_200_OK, tags=["Emergency Contacts"])
def get_emergency_contacts(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.list_emergency_contacts(db=db, user_id=user_id)