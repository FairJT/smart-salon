from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator
from datetime import datetime

# Base Salon schema with common attributes
class SalonBase(BaseModel):
    name: str
    description: Optional[str] = None
    
    address: str
    city: str
    state: Optional[str] = None
    country: str = "Iran"
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None

# Schema for creating a new salon
class SalonCreate(SalonBase):
    business_hours: Optional[Dict[str, Dict[str, str]]] = None
    
    @validator('business_hours')
    def validate_business_hours(cls, v):
        """Validate business hours format"""
        if v is None:
            return v
            
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in v:
            if day.lower() not in days:
                raise ValueError(f"Invalid day: {day}. Must be one of {days}")
            
            if 'open' not in v[day] or 'close' not in v[day]:
                raise ValueError(f"Business hours for {day} must contain 'open' and 'close' times")
                
            # Could add time format validation here
        
        return v

# Schema for updating a salon
class SalonUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None
    
    logo_url: Optional[HttpUrl] = None
    images: Optional[List[HttpUrl]] = None
    
    is_active: Optional[bool] = None
    business_hours: Optional[Dict[str, Dict[str, str]]] = None

# Schema for salon business hours update
class SalonBusinessHoursUpdate(BaseModel):
    business_hours: Dict[str, Dict[str, str]]
    
    @validator('business_hours')
    def validate_business_hours(cls, v):
        """Validate business hours format"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in v:
            if day.lower() not in days:
                raise ValueError(f"Invalid day: {day}. Must be one of {days}")
            
            if 'open' not in v[day] or 'close' not in v[day]:
                raise ValueError(f"Business hours for {day} must contain 'open' and 'close' times")
                
            # Could add time format validation here
        
        return v

# Schema for salon in response
class Salon(SalonBase):
    id: int
    owner_id: int
    
    logo_url: Optional[str] = None
    images: Optional[List[str]] = None
    
    is_active: bool
    business_hours: Optional[Dict[str, Dict[str, str]]] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Schema for salon list response (with minimal information)
class SalonBrief(BaseModel):
    id: int
    name: str
    city: str
    logo_url: Optional[str] = None
    is_active: bool
    
    class Config:
        orm_mode = True