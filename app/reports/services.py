from sqlalchemy.orm import Session
from app.reports.models import Report
from app.reports import schemas
from app.core import exceptions as exc
from app.db.redis_client import redis_client

def create_anonymous_report(db: Session, user_id: str, data: schemas.ReportCreate) -> dict:
    redis_key = f"report_rate:{user_id}"
    current_reports = redis_client.get(redis_key)

    if current_reports and int(current_reports) >= 5:
        raise exc.validation_error("Batas laporan per jam terlampaui")

    if not data.description.strip():
        raise exc.validation_error("Deskripsi tidak boleh kosong")

    geom_wkt = f"POINT({data.lon} {data.lat})"

    new_report = Report(
        category=data.category,
        description=data.description.strip(),
        geom=geom_wkt,
        moderation_status="PENDING"
    )

    db.add(new_report)
    db.commit()

    redis_client.incr(redis_key)
    if not current_reports:
        redis_client.expire(redis_key, 3600)

    return {
        "status": "success",
        "message": "Laporan berhasil terkirim."
    }