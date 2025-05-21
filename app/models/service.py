from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, JSON, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel

class Service(Base, BaseModel):
    """Service model representing beauty services offered by salons"""
    
    # Basic service information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Service details
    salon_id = Column(Integer, ForeignKey("salon.id"), nullable=False)
    category = Column(String, nullable=False)  # e.g., "haircut", "manicure", "facial"
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    # Additional service attributes
    is_active = Column(Boolean, default=True, nullable=False)
    image_url = Column(String, nullable=True)
    embedding_vector = Column(JSON, nullable=True)  # Store OpenAI embedding for similarity search
    
    # Booking and availability
    allows_online_booking = Column(Boolean, default=True, nullable=False)
    available_at_home = Column(Boolean, default=False, nullable=False)  # Whether service is available at customer's home
    home_service_fee = Column(Float, nullable=True)  # Additional fee for home service
    
    # Relationships
    salon = relationship("Salon", back_populates="services")
    appointments = relationship("Appointment", back_populates="service", cascade="all, delete-orphan")
    
    # Many-to-many relationship with stylists (a service can be offered by multiple stylists)
    stylists = relationship(
        "Stylist", 
        secondary="stylist_service", 
        back_populates="services"
    )
    
    def __repr__(self):
        return f"<Service {self.id}: {self.name} (${self.price:.2f})>"