from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

from app.schemas.service import ServiceBrief

# Base Stylist schema with common attributes
class StylistBase(BaseModel):
    full_name: str
    bio: Optional[str] = None
    years_of_experience: Optional[int] = None
    specialties: Optional[List[str]] = None

# Schema for creating a new stylist
class StylistCreate(StylistBase):
    user_id: Optional[int] = None  # Optional link to User account
    profile_image_url: Optional[HttpUrl] = None
    portfolio_images: Optional[List[HttpUrl]] = None
    working_hours: Optional[Dict[str, List[Dict[str, str]]]] = None

# Schema for updating a stylist
class StylistUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    years_of_experience: Optional[int] = None
    specialties: Optional[List[str]] = None
    profile_image_url: Optional[HttpUrl] = None
    portfolio_images: Optional[List[HttpUrl]] = None
    is_active: Optional[bool] = None
    working_hours: Optional[Dict[str, List[Dict[str, str]]]] = None

# Schema for stylist working hours update
class StylistWorkingHoursUpdate(BaseModel):
    working_hours: Dict[str, List[Dict[str, str]]]

# Schema for adding/removing services to a stylist
class StylistServiceUpdate(BaseModel):
    service_ids: List[int]

# Schema for stylist in response
class Stylist(StylistBase):
    id: int
    salon_id: int
    user_id: Optional[int] = None
    profile_image_url: Optional[str] = None
    portfolio_images: Optional[List[str]] = None
    is_active: bool
    working_hours: Optional[Dict[str, List[Dict[str, str]]]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Schema for stylist with services
class StylistWithServices(Stylist):
    services: List[ServiceBrief] = []
    
    class Config:
        orm_mode = True

# Schema for stylist list response (with minimal information)
class StylistBrief(BaseModel):
    id: int
    full_name: str
    specialties: Optional[List[str]] = None
    years_of_experience: Optional[int] = None
    profile_image_url: Optional[str] = None
    is_active: bool
    
    class Config:
        orm_mode = True