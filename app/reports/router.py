from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user_id
from app.reports import schemas, services

router = APIRouter(tags=["Anonymous Reporting"])

@router.post("/reports", response_model=schemas.ReportResponse, status_code=status.HTTP_201_CREATED, summary="Submit Anonymous Report")
def submit_report(data: schemas.ReportCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Mengirimkan laporan anonim mengenai insiden keamanan atau kondisi rute."""
    return services.create_anonymous_report(db=db, user_id=user_id, data=data)