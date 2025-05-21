from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime

from app.models.user import UserRole

# Base User schema with common attributes
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    location: Optional[str] = None
    
# Schema for creating a new user
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.CLIENT
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        # Add more password validation rules as needed
        return v

# Schema for updating a user
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    location: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_active: Optional[bool] = None
    
# Schema for changing user password
class UserChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        # Add more password validation rules as needed
        return v

# Schema for user role update (admin only)
class UserRoleUpdate(BaseModel):
    role: UserRole

# Schema for user in response (without sensitive info)
class User(UserBase):
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# Schema for token response
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    user_role: str
    expires_at: datetime

# Schema for login
class Login(BaseModel):
    email: EmailStr
    password: str