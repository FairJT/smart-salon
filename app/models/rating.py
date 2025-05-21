from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, Enum, Text
from sqlalchemy.orm import relationship
import enum

from app.database import Base
from app.models.base import BaseModel

class RatingTargetType(enum.Enum):
    """Enum for rating target types"""
    SALON = "salon"
    SERVICE = "service"
    STYLIST = "stylist"

class Rating(Base, BaseModel):
    """Rating model for salons, services, and stylists"""
    
    # Rating details
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    target_type = Column(Enum(RatingTargetType), nullable=False)
    target_id = Column(Integer, nullable=False)  # ID of the salon, service, or stylist
    appointment_id = Column(Integer, ForeignKey("appointment.id"), nullable=True)  # Optional link to appointment
    
    # Rating scores (1-5 stars)
    overall_score = Column(Float, nullable=False)
    
    # Optional detailed scores for different aspects
    cleanliness_score = Column(Float, nullable=True)
    service_quality_score = Column(Float, nullable=True)
    value_for_money_score = Column(Float, nullable=True)
    professionalism_score = Column(Float, nullable=True)
    
    # Review content
    comment = Column(Text, nullable=True)
    
    # Media
    images = Column(String, nullable=True)  # JSON array of image URLs
    
    # Status
    is_verified = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="ratings")
    
    def __repr__(self):
        return f"<Rating {self.id}: {self.overall_score}/5 for {self.target_type.value} {self.target_id}>"