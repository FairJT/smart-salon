from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime

# Base Service schema with common attributes
class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    duration_minutes: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    allows_online_booking: bool = True
    available_at_home: bool = False
    home_service_fee: Optional[float] = None

# Schema for creating a new service
class ServiceCreate(ServiceBase):
    image_url: Optional[HttpUrl] = None
    
    @validator('home_service_fee')
    def validate_home_service_fee(cls, v, values):
        """Validate home service fee"""
        if values.get('available_at_home') and v is None:
            raise ValueError('Home service fee is required when service is available at home')
        return v

# Schema for updating a service
class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None
    image_url: Optional[HttpUrl] = None
    allows_online_booking: Optional[bool] = None
    available_at_home: Optional[bool] = None
    home_service_fee: Optional[float] = None

# Schema for service in response
class Service(ServiceBase):
    id: int
    salon_id: int
    is_active: bool
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Schema for service list response (with minimal information)
class ServiceBrief(BaseModel):
    id: int
    name: str
    category: str
    price: float
    duration_minutes: int
    is_active: bool
    image_url: Optional[str] = None
    
    class Config:
        orm_mode = True

# Schema for service search response
class ServiceSearchResult(ServiceBrief):
    salon_name: str
    salon_id: int
    salon_city: str
    similarity_score: Optional[float] = None
    
    class Config:
        orm_mode = True