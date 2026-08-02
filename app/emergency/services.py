import re
from sqlalchemy.orm import Session
from app.users.models import EmergencyContact
from app.emergency.schemas import EmergencyContactCreate, EmergencyContactResponse, EmergencyContactListResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core import exceptions as exc

SOS_TRUSTED_CONTACT_LIMIT = 3

def add_emergency_contact(db: Session, user_id: str, data: EmergencyContactCreate) -> dict:
    current_count = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id
    ).count()

    if current_count >= SOS_TRUSTED_CONTACT_LIMIT:
        raise exc.validation_error(f"Maksimal {SOS_TRUSTED_CONTACT_LIMIT} kontak darurat")

    normalized_phone = _normalize_phone_number(data.phone_number)

    new_contact = EmergencyContact(
        user_id=user_id,
        contact_name=data.contact_name,
        phone_number=normalized_phone,
        relation=data.relation
    )
    
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    return {
        "contact_id": str(new_contact.id),
        "message": "Kontak darurat berhasil ditambahkan." 
    }
    
def list_emergency_contacts(db: Session, user_id: str) -> schemas.EmergencyContactListResponse:
    contacts = db.query(EmergencyContact).filter(
        EmergencyContact.user_id == user_id
    ).all()

    return schemas.EmergencyContactListResponse(
        contacts=[
            schemas.EmergencyContactResponse(
                contact_id=c.id,
                contact_name=c.contact_name,
                phone_number=c.phone_number,
                relation=c.relation
            ) for c in contacts
        ]
    )