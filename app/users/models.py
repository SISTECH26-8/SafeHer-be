from sqlalchemy import Column, String, DateTime, Boolean, Float, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.session import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    emergency_contacts = relationship("EmergencyContact", back_populates="user", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    sos_sessions = relationship("SOSSession", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    relation = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="emergency_contacts")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    priority_main_road = Column(Boolean, default=False)
    auto_share_sos_to_contacts = Column(Boolean, default=False)
    alert_radius_km = Column(Float, default=2.5)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
