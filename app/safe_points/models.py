from sqlalchemy import Column, String, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.session import Base
from geoalchemy2 import Geometry

class SafePoint(Base):
    __tablename__ = "safe_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # e.g., POLICE_STATION, GAS_STATION, HOSPITAL, MINIMARKET
    geom = Column(Geometry('POINT', srid=4326), nullable=False, index=True) # GiST index is created automatically by GeoAlchemy2
    status_lokasi = Column(String, nullable=True)
    contact_number = Column(String, nullable=True)
