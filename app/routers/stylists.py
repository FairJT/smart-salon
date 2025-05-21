from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from app.database import get_db
from app.models import User, Salon, Service, Stylist, UserRole
from app.schemas import (
    Stylist as StylistSchema,
    StylistCreate,
    StylistUpdate,
    StylistBrief,
    StylistWithServices,
    StylistWorkingHoursUpdate,
    StylistServiceUpdate
)
from app.auth import (
    get_current_active_user,
    salon_owner_required,
    get_salon_staff
)

router = APIRouter(
    prefix="/stylists",
    tags=["Stylists"],
)

@router.post("", response_model=StylistSchema, status_code=status.HTTP_201_CREATED)
async def create_stylist(
    stylist_data: StylistCreate,
    salon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(salon_owner_required(salon_id))
):
    """
    Create a new stylist for a salon (salon owner only)
    
    Args:
        stylist_data: Stylist creation data
        salon_id: Salon ID
        db: Database session
        current_user: Current authenticated salon owner
        
    Returns:
        Created stylist data
        
    Raises:
        HTTPException: If salon not found
    """
    # Check if salon exists and is owned by current user
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    
    if salon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )
    
    # Create new stylist
    new_stylist = Stylist(
        **stylist_data.dict(),
        salon_id=salon_id,
        is_active=True
    )
    
    # Save to database
    db.add(new_stylist)
    db.commit()
    db.refresh(new_stylist)
    
    return new_stylist

@router.get("", response_model=List[StylistBrief])
async def list_stylists(
    skip: int = 0,
    limit: int = 20,
    salon_id: Optional[int] = None,
    specialty: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get a list of stylists with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        salon_id: Filter by salon ID
        specialty: Filter by specialty
        is_active: Filter by active status
        db: Database session
        
    Returns:
        List of stylist brief data
    """
    query = db.query(Stylist).filter(Stylist.is_active == is_active)
    
    # Apply salon filter if provided
    if salon_id:
        query = query.filter(Stylist.salon_id == salon_id)
    
    # Apply pagination
    stylists = query.offset(skip).limit(limit).all()
    
    # Apply specialty filter in Python if provided - not ideal for large datasets
    if specialty:
        specialty = specialty.lower()
        stylists = [
            s for s in stylists 
            if s.specialties and any(spec.lower() == specialty for spec in s.specialties)
        ]
    
    return stylists

@router.get("/{stylist_id}", response_model=StylistWithServices)
async def get_stylist(
    stylist_id: int,
    db: Session = Depends(get_db)
):
    """
    Get stylist by ID
    
    Args:
        stylist_id: Stylist ID
        db: Database session
        
    Returns:
        Stylist data with services
        
    Raises:
        HTTPException: If stylist not found
    """
    stylist = db.query(Stylist).filter(Stylist.id == stylist_id).first()
    
    if stylist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )
    
    return stylist

@router.put("/{stylist_id}", response_model=StylistSchema)
async def update_stylist(
    stylist_id: int,
    stylist_data: StylistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update stylist by ID (salon owner or staff only)
    
    Args:
        stylist_id: Stylist ID
        stylist_data: Updated stylist data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated stylist data
        
    Raises:
        HTTPException: If stylist not found or user not authorized
    """
    # Get the stylist
    stylist = db.query(Stylist).filter(Stylist.id == stylist_id).first()
    
    if stylist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )
    
    # Check authorization - must be salon owner, the stylist (if user linked), or administrator
    is_authorized = (
        current_user.role == UserRole.ADMIN or
        (stylist.user_id and stylist.user_id == current_user.id) or
        db.query(Salon).filter(Salon.id == stylist.salon_id, Salon.owner_id == current_user.id).first()
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this stylist"
        )
    
    # Update stylist data
    for key, value in stylist_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(stylist, key, value)
    
    # Save changes
    db.commit()
    db.refresh(stylist)
    
    return stylist

@router.put("/{stylist_id}/working-hours", response_model=StylistSchema)
async def update_stylist_working_hours(
    stylist_id: int,
    hours_data: StylistWorkingHoursUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update stylist working hours (salon owner or stylist only)
    
    Args:
        stylist_id: Stylist ID
        hours_data: Working hours data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated stylist data
        
    Raises:
        HTTPException: If stylist not found or user not authorized
    """
    # Get the stylist
    stylist = db.query(Stylist).filter(Stylist.id == stylist_id).first()
    
    if stylist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )
    
    # Check authorization - must be salon owner, the stylist (if user linked), or administrator
    is_authorized = (
        current_user.role == UserRole.ADMIN or
        (stylist.user_id and stylist.user_id == current_user.id) or
        db.query(Salon).filter(Salon.id == stylist.salon_id, Salon.owner_id == current_user.id).first()
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this stylist's working hours"
        )
    
    # Update working hours
    stylist.working_hours = hours_data.working_hours
    
    # Save changes
    db.commit()
    db.refresh(stylist)
    
    return stylist

@router.post("/{stylist_id}/services", response_model=StylistWithServices)
async def add_stylist_services(
    stylist_id: int,
    service_data: StylistServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_salon_staff)
):
    """
    Add services to a stylist (salon owner or staff only)
    
    Args:
        stylist_id: Stylist ID
        service_data: Service IDs to add
        db: Database session
        current_user: Current authenticated salon staff
        
    Returns:
        Updated stylist data with services
        
    Raises:
        HTTPException: If stylist not found, services not found, or user not authorized
    """
    # Get the stylist
    stylist = db.query(Stylist).filter(Stylist.id == stylist_id).first()
    
    if stylist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )
    
    # Check authorization - must be salon owner or administrator
    is_authorized = (
        current_user.role == UserRole.ADMIN or
        (current_user.role == UserRole.STYLIST and stylist.user_id == current_user.id) or
        db.query(Salon).filter(Salon.id == stylist.salon_id, Salon.owner_id == current_user.id).first()
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this stylist's services"
        )
    
    # Get the services
    services = db.query(Service).filter(
        Service.id.in_(service_data.service_ids),
        Service.salon_id == stylist.salon_id
    ).all()
    
    # Check if all services exist and belong to the same salon
    if len(services) != len(service_data.service_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more services not found or do not belong to the stylist's salon"
        )
    
    # Add services to stylist
    stylist.services = list(set(stylist.services + services))
    
    # Save changes
    db.commit()
    db.refresh(stylist)
    
    return stylist

@router.delete("/{stylist_id}/services", response_model=StylistWithServices)
async def remove_stylist_services(
    stylist_id: int,
    service_data: StylistServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_salon_staff)
):
    """
    Remove services from a stylist (salon owner or staff only)
    
    Args:
        stylist_id: Stylist ID
        service_data: Service IDs to remove
        db: Database session
        current_user: Current authenticated salon staff
        
    Returns:
        Updated stylist data with services
        
    Raises:
        HTTPException: If stylist not found or user not authorized
    """
    # Get the stylist
    stylist = db.query(Stylist).filter(Stylist.id == stylist_id).first()
    
    if stylist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )
    
    # Check authorization - must be salon owner or administrator
    is_authorized = (
        current_user.role == UserRole.ADMIN or
        (current_user.role == UserRole.STYLIST and stylist.user_id == current_user.id) or
        db.query(Salon).filter(Salon.id == stylist.salon_id, Salon.owner_id == current_user.id).first()
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this stylist's services"
        )
    
    # Get the services to remove
    services_to_remove = db.query(Service).filter(Service.id.in_(service_data.service_ids)).all()
    
    # Create a set of service IDs to remove
    service_ids_to_remove = {s.id for s in services_to_remove}
    
    # Filter out services to remove
    stylist.services = [s for s in stylist.services if s.id not in service_ids_to_remove]
    
    # Save changes
    db.commit()
    db.refresh(stylist)
    
    return stylist