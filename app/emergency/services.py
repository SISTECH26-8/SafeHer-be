import re
import json
import httpx
import logging
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import BackgroundTasks
from app.users.models import User, EmergencyContact
from app.emergency.models import SOSSession
from app.emergency import schemas
from app.core import exceptions as exc
from app.db.redis_client import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

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
    
async def send_wa_alerts(user_name: str, contacts: list, tracking_url: str):
    """
    Mengirim pesan darurat ke kontak via Otoway.net API
    """
    url = settings.WHATSAPP_API_URL
    token = settings.WHATSAPP_API_TOKEN
    
    if not token or token == "your-wa-api-key" or not url:
        for contact in contacts:
            logger.info(f"[MOCK WA] Mengirim ke {contact.contact_name} ({contact.phone_number})")
        return

    async with httpx.AsyncClient() as client:
        for contact in contacts:
            message_text = (
                f"*DARURAT!* ⚠️\n\n"
                f"*{user_name}* sedang dalam bahaya!\n\n"
                f"Lacak lokasi terkini secara live di sini:\n"
                f"{tracking_url}"
            )
            
            payload = {
                "phone": contact.phone_number,
                "message": message_text
            }
            
            headers = {
                "Authorization": f"Bearer {token}", 
                "Content-Type": "application/json"
            }
            
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
                response.raise_for_status()
                logger.info(f"Berhasil kirim WA SOS ke {contact.phone_number}")
            except Exception as e:
                logger.error(f"Gagal kirim WA SOS ke {contact.phone_number}: {e}")

def create_sos_session(db: Session, user_id: str, data: schemas.SOSCreateRequest, background_tasks: BackgroundTasks) -> schemas.SOSCreateResponse:
    existing_session = db.query(SOSSession).filter(
        SOSSession.user_id == user_id,
        SOSSession.status == "EMERGENCY_ACTIVE"
    ).first()

    if existing_session:
        sos_id = str(existing_session.id)
    else:
        new_sos = SOSSession(
            user_id=user_id,
            status="EMERGENCY_ACTIVE"
        )
        db.add(new_sos)
        db.commit()
        db.refresh(new_sos)
        sos_id = str(new_sos.id)

    redis_key = f"sos:{sos_id}:location"
    location_data = {
        "lat": data.current_lat,
        "lon": data.current_lon,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    redis_client.setex(redis_key, 3600, json.dumps(location_data))

    user = db.query(User).filter(User.id == user_id).first()
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).all()
    
    live_tracking_url = f"https://safeher.app/track/{sos_id}"

    if contacts:
        background_tasks.add_task(send_wa_alerts, user.full_name, contacts, live_tracking_url)

    return schemas.SOSCreateResponse(
        sos_session_id=sos_id,
        message="Lokasi telah dikirim ke kontak darurat Anda.",
        live_tracking_url=live_tracking_url
    )

def update_sos_location(db: Session, user_id: str, sos_session_id: str, data: schemas.SOSLocationUpdate) -> schemas.SOSLocationUpdateResponse:
    session = db.query(SOSSession).filter(
        SOSSession.id == sos_session_id,
        SOSSession.user_id == user_id
    ).first()

    if not session or session.status == "RESOLVED":
        raise exc.sos_session_not_found()

    redis_key = f"sos:{sos_session_id}:location"
    location_data = {
        "lat": data.lat,
        "lon": data.lon,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    redis_client.setex(redis_key, 3600, json.dumps(location_data))

    return schemas.SOSLocationUpdateResponse(status="updated")

def get_sos_tracking(db: Session, sos_session_id: str) -> schemas.SOSTrackResponse:
    session = db.query(SOSSession).filter(SOSSession.id == sos_session_id).first()
    
    if not session:
        raise exc.sos_session_not_found()

    user = db.query(User).filter(User.id == session.user_id).first()

    redis_key = f"sos:{sos_session_id}:location"
    redis_data = redis_client.get(redis_key)

    if redis_data:
        parsed_data = json.loads(redis_data)
        current_lat = parsed_data["lat"]
        current_lon = parsed_data["lon"]
        last_updated = datetime.fromisoformat(parsed_data["updated_at"])
    else:
        current_lat = 0.0
        current_lon = 0.0
        last_updated = session.created_at

    return schemas.SOSTrackResponse(
        user_name=user.full_name,
        status=session.status,
        last_updated=last_updated,
        current_location=schemas.SOSTrackLocation(lat=current_lat, lon=current_lon)
    )

def end_sos_session(db: Session, user_id: str, sos_session_id: str) -> schemas.SOSEndResponse:
    session = db.query(SOSSession).filter(
        SOSSession.id == sos_session_id,
        SOSSession.user_id == user_id
    ).first()

    if not session:
        raise exc.sos_session_not_found()

    if session.status == "RESOLVED":
        return schemas.SOSEndResponse(
            status="success",
            message="Mode SOS sudah dalam keadaan dinonaktifkan."
        )

    session.status = "RESOLVED"
    session.resolved_at = func.now()
    db.commit()

    redis_key = f"sos:{sos_session_id}:location"
    redis_client.delete(redis_key)

    return schemas.SOSEndResponse(
        status="success",
        message="Mode SOS dinonaktifkan. Anda sudah aman."
    )