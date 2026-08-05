from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user_id
from app.emergency import schemas, services

router = APIRouter(tags=["Emergency Contacts"])

@router.post("/users/emergency-contacts", status_code=status.HTTP_201_CREATED, summary="Add Emergency Contact")
def create_emergency_contact(data: schemas.EmergencyContactCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Menambahkan kontak darurat baru untuk pengguna."""
    return services.add_emergency_contact(db=db, user_id=user_id, data=data)

@router.get("/users/emergency-contacts", response_model=schemas.EmergencyContactListResponse, status_code=status.HTTP_200_OK, summary="List Emergency Contacts")
def get_emergency_contacts(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Menampilkan daftar kontak darurat milik pengguna."""
    return services.list_emergency_contacts(db=db, user_id=user_id)

@router.put("/users/emergency-contacts/{contact_id}", response_model=schemas.EmergencyContactUpdateResponse, status_code=status.HTTP_200_OK, summary="Update Emergency Contact")
def update_emergency_contact(contact_id: str, data: schemas.EmergencyContactCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Memperbarui informasi kontak darurat tertentu."""
    return services.update_emergency_contact(db=db, user_id=user_id, contact_id=contact_id, data=data)

@router.delete("/users/emergency-contacts/{contact_id}", response_model=schemas.EmergencyContactDeleteResponse, status_code=status.HTTP_200_OK, summary="Delete Emergency Contact")
def delete_emergency_contact(contact_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Menghapus kontak darurat tertentu."""
    return services.delete_emergency_contact(db=db, user_id=user_id, contact_id=contact_id)

@router.post("/emergency/sos", response_model=schemas.SOSCreateResponse, status_code=status.HTTP_201_CREATED, summary="Trigger SOS")
def trigger_sos(data: schemas.SOSCreateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Memicu sinyal SOS dan mengirimkan notifikasi ke kontak darurat."""
    return services.create_sos_session(db=db, user_id=user_id, data=data, background_tasks=background_tasks)

@router.patch("/emergency/sos/{sos_session_id}/location", response_model=schemas.SOSLocationUpdateResponse, status_code=status.HTTP_200_OK, summary="Update SOS Location")
def update_sos_location(sos_session_id: str, data: schemas.SOSLocationUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Memperbarui lokasi pengguna saat SOS aktif."""
    return services.update_sos_location(db=db, user_id=user_id, sos_session_id=sos_session_id, data=data)

@router.get("/emergency/sos/{sos_session_id}/track", response_model=schemas.SOSTrackResponse, status_code=status.HTTP_200_OK, summary="Track SOS Location")
def track_sos_location(sos_session_id: str, db: Session = Depends(get_db)):
    """Melacak lokasi pengguna yang sedang SOS melalui tautan publik."""
    return services.get_sos_tracking(db=db, sos_session_id=sos_session_id)

@router.post("/emergency/sos/{sos_session_id}/end", response_model=schemas.SOSEndResponse, status_code=status.HTTP_200_OK, summary="End SOS Session")
def end_sos(sos_session_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Mengakhiri sesi SOS."""
    return services.end_sos_session(db=db, user_id=user_id, sos_session_id=sos_session_id)