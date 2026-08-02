import re
from sqlalchemy.orm import Session
from app.users.models import EmergencyContact
from app.emergency import schemas
from app.core import exceptions as exc

SOS_TRUSTED_CONTACT_LIMIT = 3

def _normalize_phone_number(phone: str) -> str:
    cleaned = re.sub(r'[^\d+]', '', phone)
    if cleaned.startswith('+62'):
        cleaned = '0' + cleaned[3:]
    elif cleaned.startswith('62'):
        cleaned = '0' + cleaned[2:]
    return cleaned

def add_emergency_contact(db: Session, user_id: str, data: schemas.EmergencyContactCreate) -> schemas.EmergencyContactCreateResponse:
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
    
def update_emergency_contact(db: Session, user_id: str, contact_id: str, data: schemas.EmergencyContactCreate) -> schemas.EmergencyContactUpdateResponse:
    contact = db.query(EmergencyContact).filter(EmergencyContact.id == contact_id,EmergencyContact.user_id == user_id).first()

    if not contact:
        raise exc.contact_not_found()

    normalized_phone = _normalize_phone_number(data.phone_number)
    
    contact.contact_name = data.contact_name
    contact.phone_number = normalized_phone
    contact.relation = data.relation

    db.commit()
    db.refresh(contact)

    return schemas.EmergencyContactUpdateResponse(
        status="success",
        message="Kontak darurat berhasil diperbarui.",
        contact=schemas.EmergencyContactResponse(
            contact_id=contact.id,
            contact_name=contact.contact_name,
            phone_number=contact.phone_number,
            relation=contact.relation
        )
    )

def delete_emergency_contact(db: Session, user_id: str, contact_id: str) -> schemas.EmergencyContactDeleteResponse:
    contact = db.query(EmergencyContact).filter(EmergencyContact.id == contact_id, EmergencyContact.user_id == user_id).first()

    if not contact:
        raise exc.contact_not_found()

    db.delete(contact)
    db.commit()

    return schemas.EmergencyContactDeleteResponse(
        status="success",
        message="Kontak darurat berhasil dihapus."
    )