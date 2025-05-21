from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, Enum, DateTime, Text
from sqlalchemy.orm import relationship
import enum

from app.database import Base
from app.models.base import BaseModel

class AppointmentStatus(enum.Enum):
    """Enum for appointment status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class AppointmentType(enum.Enum):
    """Enum for appointment type"""
    IN_SALON = "in_salon"
    AT_HOME = "at_home"

class Appointment(Base, BaseModel):
    """Appointment model representing service bookings"""
    
    # Appointment participants
    client_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("service.id"), nullable=False)
    stylist_id = Column(Integer, ForeignKey("stylist.id"), nullable=False)
    
    # Appointment details
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False)
    appointment_type = Column(Enum(AppointmentType), default=AppointmentType.IN_SALON, nullable=False)
    
    # Location (for at-home services)
    address = Column(String, nullable=True)
    
    # Payment information
    price = Column(Float, nullable=False)  # Final price including any discounts or fees
    original_price = Column(Float, nullable=False)  # Original service price
    discount_amount = Column(Float, default=0.0, nullable=False)
    additional_fees = Column(Float, default=0.0, nullable=False)  # For at-home services
    is_paid = Column(Boolean, default=False, nullable=False)
    
    # Additional information
    notes = Column(Text, nullable=True)
    cancellation_reason = Column(String, nullable=True)
    
    # Relationships
    client = relationship("User", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    stylist = relationship("Stylist", back_populates="appointments")
    
    def __repr__(self):
        return f"<Appointment {self.id}: {self.service.name} at {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.status.value}>"