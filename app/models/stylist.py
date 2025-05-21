from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, JSON, Table
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel

# Association table for many-to-many relationship between stylists and services
stylist_service = Table(
    "stylist_service",
    Base.metadata,
    Column("stylist_id", Integer, ForeignKey("stylist.id"), primary_key=True),
    Column("service_id", Integer, ForeignKey("service.id"), primary_key=True)
)

class Stylist(Base, BaseModel):
    """Stylist model representing beauty professionals working at salons"""
    
    # Basic stylist information
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)  # If the stylist is also a user
    salon_id = Column(Integer, ForeignKey("salon.id"), nullable=False)
    
    # Personal information
    full_name = Column(String, nullable=False)
    bio = Column(String, nullable=True)
    
    # Professional information
    years_of_experience = Column(Integer, nullable=True)
    specialties = Column(JSON, nullable=True)  # List of specialties: ["haircut", "coloring", ...]
    
    # Media
    profile_image_url = Column(String, nullable=True)
    portfolio_images = Column(JSON, nullable=True, default=list)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Working schedule - stored as JSON with format:
    # {
    #   "monday": [{"start": "09:00", "end": "13:00"}, {"start": "14:00", "end": "18:00"}],
    #   "tuesday": [...],
    #   ...
    # }
    working_hours = Column(JSON, nullable=True)
    
    # Relationships
    salon = relationship("Salon", back_populates="stylists")
    user = relationship("User", foreign_keys=[user_id])
    
    # Many-to-many relationship with services (a stylist can offer multiple services)
    services = relationship(
        "Service", 
        secondary=stylist_service, 
        back_populates="stylists"
    )
    
    # Appointments assigned to this stylist
    appointments = relationship("Appointment", back_populates="stylist")
    
    def __repr__(self):
        return f"<Stylist {self.id}: {self.full_name} at Salon {self.salon_id}>"