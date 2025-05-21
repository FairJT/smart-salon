from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime

from app.models.appointment import AppointmentStatus, AppointmentType
from app.schemas.service import ServiceBrief
from app.schemas.stylist import StylistBrief

# Base Appointment schema with common attributes
class AppointmentBase(BaseModel):
    service_id: int
    stylist_id: int
    start_time: datetime
    appointment_type: AppointmentType = AppointmentType.IN_SALON
    address: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('address')
    def validate_address(cls, v, values):
        """Validate that address is provided for at-home appointments"""
        if values.get('appointment_type') == AppointmentType.AT_HOME and not v:
            raise ValueError('Address is required for at-home appointments')
        return v

# Schema for creating a new appointment
class AppointmentCreate(AppointmentBase):
    pass

# Schema for updating an appointment
class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    
    @validator('cancellation_reason')
    def validate_cancellation_reason(cls, v, values):
        """Validate that cancellation reason is provided when status is CANCELLED"""
        if values.get('status') == AppointmentStatus.CANCELLED and not v:
            raise ValueError('Cancellation reason is required when cancelling an appointment')
        return v

# Schema for appointment status update
class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    cancellation_reason: Optional[str] = None
    
    @validator('cancellation_reason')
    def validate_cancellation_reason(cls, v, values):
        """Validate that cancellation reason is provided when status is CANCELLED"""
        if values.get('status') == AppointmentStatus.CANCELLED and not v:
            raise ValueError('Cancellation reason is required when cancelling an appointment')
        return v

# Schema for appointment payment update
class AppointmentPaymentUpdate(BaseModel):
    is_paid: bool = True

# Schema for appointment in response
class Appointment(AppointmentBase):
    id: int
    client_id: int
    end_time: datetime
    status: AppointmentStatus
    price: float
    original_price: float
    discount_amount: float
    additional_fees: float
    is_paid: bool
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Schema for appointment with related entities
class AppointmentDetail(Appointment):
    service: ServiceBrief
    stylist: StylistBrief
    
    class Config:
        orm_mode = True

# Schema for available time slots
class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    stylist_id: int
    stylist_name: str

# Schema for availability request
class AvailabilityRequest(BaseModel):
    service_id: int
    date: datetime
    stylist_id: Optional[int] = None