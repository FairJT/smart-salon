from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime

from app.models.rating import RatingTargetType

# Base Rating schema with common attributes
class RatingBase(BaseModel):
    target_type: RatingTargetType
    target_id: int
    overall_score: float = Field(..., ge=1, le=5)
    cleanliness_score: Optional[float] = Field(None, ge=1, le=5)
    service_quality_score: Optional[float] = Field(None, ge=1, le=5)
    value_for_money_score: Optional[float] = Field(None, ge=1, le=5)
    professionalism_score: Optional[float] = Field(None, ge=1, le=5)
    comment: Optional[str] = None

# Schema for creating a new rating
class RatingCreate(RatingBase):
    appointment_id: Optional[int] = None
    images: Optional[List[HttpUrl]] = None

# Schema for updating a rating
class RatingUpdate(BaseModel):
    overall_score: Optional[float] = Field(None, ge=1, le=5)
    cleanliness_score: Optional[float] = Field(None, ge=1, le=5)
    service_quality_score: Optional[float] = Field(None, ge=1, le=5)
    value_for_money_score: Optional[float] = Field(None, ge=1, le=5)
    professionalism_score: Optional[float] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    images: Optional[List[HttpUrl]] = None
    is_public: Optional[bool] = None

# Schema for admin rating update
class AdminRatingUpdate(RatingUpdate):
    is_verified: Optional[bool] = None

# Schema for rating in response
class Rating(RatingBase):
    id: int
    user_id: int
    appointment_id: Optional[int] = None
    images: Optional[List[str]] = None
    is_verified: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    # Include user info
    user_name: str
    
    class Config:
        orm_mode = True

# Schema for rating summary
class RatingSummary(BaseModel):
    average_overall: float
    average_cleanliness: Optional[float] = None
    average_service_quality: Optional[float] = None
    average_value_for_money: Optional[float] = None
    average_professionalism: Optional[float] = None
    total_ratings: int
    five_star_count: int
    four_star_count: int
    three_star_count: int
    two_star_count: int
    one_star_count: int