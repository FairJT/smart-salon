from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base
from app.models.base import BaseModel

class UserRole(enum.Enum):
    """Enum for user roles"""
    CLIENT = "client"
    SALON_OWNER = "salon_owner"
    STYLIST = "stylist"
    ADMIN = "admin"

class User(Base, BaseModel):
    """User model for clients, salon owners, and stylists"""
    
    # Basic user information
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # User role and status
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CLIENT)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile information
    profile_image_url = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # Relationships
    # A user can own multiple salons (if role is SALON_OWNER)
    owned_salons = relationship("Salon", back_populates="owner", cascade="all, delete-orphan")
    
    # A user can have multiple appointments (if role is CLIENT)
    appointments = relationship("Appointment", back_populates="client", cascade="all, delete-orphan")
    
    # A user can post multiple ratings
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    
    # A user can have multiple chat logs
    chat_logs = relationship("ChatLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.id}: {self.email} ({self.role})>"