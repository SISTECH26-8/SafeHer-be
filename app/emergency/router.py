from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user_id
from app.emergency import schemas, services

router = APIRouter(tags=["Emergency Contacts"])

@router.post("/users/emergency-contacts", status_code=status.HTTP_201_CREATED)
def create_emergency_contact(data: schemas.EmergencyContactCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.add_emergency_contact(db=db, user_id=user_id, data=data)

@router.get("/users/emergency-contacts", response_model=schemas.EmergencyContactListResponse, status_code=status.HTTP_200_OK)
def get_emergency_contacts(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.list_emergency_contacts(db=db, user_id=user_id)

@router.put("/users/emergency-contacts/{contact_id}", response_model=schemas.EmergencyContactUpdateResponse, status_code=status.HTTP_200_OK)
def update_emergency_contact(contact_id: str, data: schemas.EmergencyContactCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.update_emergency_contact(db=db, user_id=user_id, contact_id=contact_id, data=data)

@router.delete("/users/emergency-contacts/{contact_id}", response_model=schemas.EmergencyContactDeleteResponse, status_code=status.HTTP_200_OK)
def delete_emergency_contact(contact_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return services.delete_emergency_contact(db=db, user_id=user_id, contact_id=contact_id)