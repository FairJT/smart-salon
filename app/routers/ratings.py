from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func, case

from app.database import get_db
from app.models import (
    User, Salon, Service, Stylist, Appointment, Rating, 
    RatingTargetType, AppointmentStatus, UserRole
)
from app.schemas import (
    Rating as RatingSchema,
    RatingCreate,
    RatingUpdate,
    AdminRatingUpdate,
    RatingSummary
)
from app.auth import (
    get_current_active_user,
    get_client,
    get_admin_user
)

router = APIRouter(
    prefix="/ratings",
    tags=["Ratings"],
)

@router.post("", response_model=RatingSchema, status_code=status.HTTP_201_CREATED)
async def create_rating(
    rating_data: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_client)
):
    """
    Create a new rating (clients only)
    
    Args:
        rating_data: Rating creation data
        db: Database session
        current_user: Current authenticated client
        
    Returns:
        Created rating data
        
    Raises:
        HTTPException: If target not found or user not authorized
    """
    # Validate target exists
    if rating_data.target_type == RatingTargetType.SALON:
        target = db.query(Salon).filter(Salon.id == rating_data.target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salon not found"
            )
    
    elif rating_data.target_type == RatingTargetType.SERVICE:
        target = db.query(Service).filter(Service.id == rating_data.target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
    
    elif rating_data.target_type == RatingTargetType.STYLIST:
        target = db.query(Stylist).filter(Stylist.id == rating_data.target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stylist not found"
            )
    
    # Check if appointment exists and belongs to user
    if rating_data.appointment_id:
        appointment = db.query(Appointment).filter(
            Appointment.id == rating_data.appointment_id,
            Appointment.client_id == current_user.id,
            Appointment.status == AppointmentStatus.COMPLETED
        ).first()
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found or not completed"
            )
    
    # Check if user has already rated this target
    existing_rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.target_type == rating_data.target_type,
        Rating.target_id == rating_data.target_id
    ).first()
    
    if existing_rating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already rated this target"
        )
    
    # Create new rating
    new_rating = Rating(
        user_id=current_user.id,
        target_type=rating_data.target_type,
        target_id=rating_data.target_id,
        appointment_id=rating_data.appointment_id,
        overall_score=rating_data.overall_score,
        cleanliness_score=rating_data.cleanliness_score,
        service_quality_score=rating_data.service_quality_score,
        value_for_money_score=rating_data.value_for_money_score,
        professionalism_score=rating_data.professionalism_score,
        comment=rating_data.comment,
        images=rating_data.images,
        is_verified=True,  # Auto-verify for now
        is_public=True
    )
    
    # Save to database
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    
    # Add user name to response
    setattr(new_rating, "user_name", current_user.full_name)
    
    return new_rating

@router.get("/my-ratings", response_model=List[RatingSchema])
async def get_my_ratings(
    skip: int = 0,
    limit: int = 20,
    target_type: Optional[RatingTargetType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_client)
):
    """
    Get current user's ratings
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        target_type: Filter by target type
        db: Database session
        current_user: Current authenticated client
        
    Returns:
        List of ratings
    """
    # Build query
    query = db.query(Rating).filter(Rating.user_id == current_user.id)
    
    # Apply target type filter
    if target_type:
        query = query.filter(Rating.target_type == target_type)
    
    # Apply pagination
    ratings = query.order_by(Rating.created_at.desc()).offset(skip).limit(limit).all()
    
    # Add user name to each rating
    for rating in ratings:
        setattr(rating, "user_name", current_user.full_name)
    
    return ratings

@router.get("/target/{target_type}/{target_id}", response_model=List[RatingSchema])
async def get_target_ratings(
    target_type: RatingTargetType,
    target_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get ratings for a specific target
    
    Args:
        target_type: Target type
        target_id: Target ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of ratings
        
    Raises:
        HTTPException: If target not found
    """
    # Validate target exists
    if target_type == RatingTargetType.SALON:
        target = db.query(Salon).filter(Salon.id == target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salon not found"
            )
    
    elif target_type == RatingTargetType.SERVICE:
        target = db.query(Service).filter(Service.id == target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
    
    elif target_type == RatingTargetType.STYLIST:
        target = db.query(Stylist).filter(Stylist.id == target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stylist not found"
            )
    
    # Build query
    query = db.query(Rating, User.full_name.label("user_name")).join(
        User, Rating.user_id == User.id
    ).filter(
        Rating.target_type == target_type,
        Rating.target_id == target_id,
        Rating.is_public == True
    )
    
    # Apply pagination
    results = query.order_by(Rating.created_at.desc()).offset(skip).limit(limit).all()
    
    # Convert results to Rating objects with user_name
    ratings = []
    for rating, user_name in results:
        setattr(rating, "user_name", user_name)
        ratings.append(rating)
    
    return ratings

@router.get("/summary/{target_type}/{target_id}", response_model=RatingSummary)
async def get_rating_summary(
    target_type: RatingTargetType,
    target_id: int,
    db: Session = Depends(get_db)
):
    """
    Get rating summary for a specific target
    
    Args:
        target_type: Target type
        target_id: Target ID
        db: Database session
        
    Returns:
        Rating summary
        
    Raises:
        HTTPException: If target not found
    """
    # Validate target exists
    if target_type == RatingTargetType.SALON:
        target = db.query(Salon).filter(Salon.id == target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salon not found"
            )
    
    elif target_type == RatingTargetType.SERVICE:
        target = db.query(Service).filter(Service.id == target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found"
            )
    
    elif target_type == RatingTargetType.STYLIST:
        target = db.query(Stylist).filter(Stylist.id == target_id).first()
        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stylist not found"
            )
    
    # Get rating summary
    summary = db.query(
        func.avg(Rating.overall_score).label("average_overall"),
        func.avg(Rating.cleanliness_score).label("average_cleanliness"),
        func.avg(Rating.service_quality_score).label("average_service_quality"),
        func.avg(Rating.value_for_money_score).label("average_value_for_money"),
        func.avg(Rating.professionalism_score).label("average_professionalism"),
        func.count(Rating.id).label("total_ratings"),
        func.sum(case((Rating.overall_score == 5, 1), else_=0)).label("five_star_count"),
        func.sum(case((Rating.overall_score == 4, 1), else_=0)).label("four_star_count"),
        func.sum(case((Rating.overall_score == 3, 1), else_=0)).label("three_star_count"),
        func.sum(case((Rating.overall_score == 2, 1), else_=0)).label("two_star_count"),
        func.sum(case((Rating.overall_score == 1, 1), else_=0)).label("one_star_count")
    ).filter(
        Rating.target_type == target_type,
        Rating.target_id == target_id,
        Rating.is_public == True
    ).first()
    
    # Convert to dictionary
    summary_dict = {
        "average_overall": round(float(summary.average_overall or 0), 1),
        "average_cleanliness": round(float(summary.average_cleanliness or 0), 1) if summary.average_cleanliness else None,
        "average_service_quality": round(float(summary.average_service_quality or 0), 1) if summary.average_service_quality else None,
        "average_value_for_money": round(float(summary.average_value_for_money or 0), 1) if summary.average_value_for_money else None,
        "average_professionalism": round(float(summary.average_professionalism or 0), 1) if summary.average_professionalism else None,
        "total_ratings": summary.total_ratings or 0,
        "five_star_count": summary.five_star_count or 0,
        "four_star_count": summary.four_star_count or 0,
        "three_star_count": summary.three_star_count or 0,
        "two_star_count": summary.two_star_count or 0,
        "one_star_count": summary.one_star_count or 0
    }
    
    return summary_dict

@router.put("/{rating_id}", response_model=RatingSchema)
async def update_rating(
    rating_id: int,
    rating_data: RatingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update rating by ID
    
    Args:
        rating_id: Rating ID
        rating_data: Updated rating data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated rating data
        
    Raises:
        HTTPException: If rating not found or user not authorized
    """
    # Get the rating
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    
    if rating is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    
    # Check authorization
    is_admin = current_user.role == UserRole.ADMIN
    is_owner = rating.user_id == current_user.id
    
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this rating"
        )
    
    # Update rating data
    for key, value in rating_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(rating, key, value)
    
    # Reset verification status if content changed and user is not admin
    if not is_admin and any(key in rating_data.dict(exclude_unset=True) for key in 
                          ['overall_score', 'cleanliness_score', 'service_quality_score', 
                           'value_for_money_score', 'professionalism_score', 'comment']):
        rating.is_verified = False
    
    # Save changes
    db.commit()
    db.refresh(rating)
    
    # Add user name to response
    user = db.query(User).filter(User.id == rating.user_id).first()
    setattr(rating, "user_name", user.full_name)
    
    return rating

@router.put("/admin/{rating_id}", response_model=RatingSchema)
async def admin_update_rating(
    rating_id: int,
    rating_data: AdminRatingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Admin update rating by ID (admin only)
    
    Args:
        rating_id: Rating ID
        rating_data: Updated rating data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Updated rating data
        
    Raises:
        HTTPException: If rating not found
    """
    # Get the rating
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    
    if rating is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    
    # Update rating data
    for key, value in rating_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(rating, key, value)
    
    # Save changes
    db.commit()
    db.refresh(rating)
    
    # Add user name to response
    user = db.query(User).filter(User.id == rating.user_id).first()
    setattr(rating, "user_name", user.full_name)
    
    return rating

@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete rating by ID
    
    Args:
        rating_id: Rating ID
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If rating not found or user not authorized
    """
    # Get the rating
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    
    if rating is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )
    
    # Check authorization
    is_admin = current_user.role == UserRole.ADMIN
    is_owner = rating.user_id == current_user.id
    
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this rating"
        )
    
    # Delete rating
    db.delete(rating)
    db.commit()
    
    return None