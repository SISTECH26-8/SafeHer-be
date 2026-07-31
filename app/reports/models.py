from sqlalchemy import Column, String, DateTime, func, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.session import Base
from geoalchemy2 import Geometry

class Report(Base):
    __tablename__ = "reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String, nullable=False) # e.g., TINDAK_KRIMINAL, PELECEHAN_SEKSUAL, ORANG_MENCURIGAKAN
    description = Column(String, nullable=False)
    geom = Column(Geometry('POINT', srid=4326), nullable=False, index=True)
    moderation_status = Column(String, nullable=False, default="PENDING") # PENDING, APPROVED, REJECTED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
