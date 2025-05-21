from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel

class Salon(Base, BaseModel):
    """Salon model representing beauty salons"""
    
    # Basic salon information
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Owner information
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Location information
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=True)
    country = Column(String, nullable=False, default="Iran")
    postal_code = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Contact information
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Media
    logo_url = Column(String, nullable=True)
    images = Column(JSON, nullable=True, default=list)
    
    # Business info
    is_active = Column(Boolean, default=True, nullable=False)
    business_hours = Column(JSON, nullable=True)  # Format: {"monday": {"open": "09:00", "close": "18:00"}, ...}
    
    # Relationships
    owner = relationship("User", back_populates="owned_salons")
    services = relationship("Service", back_populates="salon", cascade="all, delete-orphan")
    stylists = relationship("Stylist", back_populates="salon", cascade="all, delete-orphan")
    
    # Ratings are handled through a polymorphic relationship in the Rating model
    
    def __repr__(self):
        return f"<Salon {self.id}: {self.name}>"