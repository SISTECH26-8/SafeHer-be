from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.session import Base
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship

class Trip(Base):
    __tablename__ = "trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    route_id = Column(String, nullable=False)
    start_geom = Column(Geometry('POINT', srid=4326), nullable=True)
    destination_geom = Column(Geometry('POINT', srid=4326), nullable=False)
    status = Column(String, nullable=False, default="ACTIVE") # ACTIVE, COMPLETED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="trips")
