from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from app.database import get_db
from app.models import User, Salon, Service, Stylist, UserRole
from app.schemas import (
    Salon as SalonSchema,
    SalonCreate,
    SalonUpdate,
    SalonBrief,
    SalonBusinessHoursUpdate,
    ServiceBrief,
    StylistBrief
)
from app.auth import (
    get_current_active_user,
    get_salon_owner,
    salon_owner_required,
    get_admin_user
)

router = APIRouter(
    prefix="/salons",
    tags=["Salons"],
)

@router.post("", response_model=SalonSchema, status_code=status.HTTP_201_CREATED)
async def create_salon(
    salon_data: SalonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_salon_owner)
):
    """
    Create a new salon (salon owners only)
    
    Args:
        salon_data: Salon creation data
        db: Database session
        current_user: Current authenticated salon owner
        
    Returns:
        Created salon data
    """
    # Create new salon
    new_salon = Salon(
        **salon_data.dict(),
        owner_id=current_user.id,
        is_active=True
    )
    
    # Save to database
    db.add(new_salon)
    db.commit()
    db.refresh(new_salon)
    
    return new_salon

@router.get("", response_model=List[SalonBrief])
async def list_salons(
    skip: int = 0,
    limit: int = 20,
    city: Optional[str] = None,
    name: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get a list of salons with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        city: Filter by city
        name: Filter by name (partial match)
        is_active: Filter by active status
        db: Database session
        
    Returns:
        List of salon brief data
    """
    query = db.query(Salon).filter(Salon.is_active == is_active)
    
    # Apply city filter if provided
    if city:
        query = query.filter(func.lower(Salon.city) == city.lower())
    
    # Apply name filter if provided
    if name:
        query = query.filter(Salon.name.ilike(f"%{name}%"))
    
    # Apply pagination
    salons = query.offset(skip).limit(limit).all()
    
    return salons

@router.get("/my-salons", response_model=List[SalonBrief])
async def list_my_salons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_salon_owner)
):
    """
    Get a list of salons owned by the current user
    
    Args:
        db: Database session
        current_user: Current authenticated salon owner
        
    Returns:
        List of salon brief data
    """
    salons = db.query(Salon).filter(
        Salon.owner_id == current_user.id
    ).all()
    
    return salons

@router.get("/{salon_id}", response_model=SalonSchema)
async def get_salon(
    salon_id: int,
    db: Session = Depends(get_db)
):
    """
    Get salon by ID
    
    Args:
        salon_id: Salon ID
        db: Database session
        
    Returns:
        Salon data
        
    Raises:
        HTTPException: If salon not found
    """
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    
    if salon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )
    
    return salon

@router.put("/{salon_id}", response_model=SalonSchema)
async def update_salon(
    salon_id: int,
    salon_data: SalonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(salon_owner_required(salon_id))
):
    """
    Update salon by ID (salon owner only)
    
    Args:
        salon_id: Salon ID
        salon_data: Updated salon data
        db: Database session
        current_user: Current authenticated salon owner
        
    Returns:
        Updated salon data
        
    Raises:
        HTTPException: If salon not found
    """
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    
    if salon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )
    
    # Update salon data
    for key, value in salon_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(salon, key, value)
    
    # Save changes
    db.commit()
    db.refresh(salon)
    
    return salon

@router.put("/{salon_id}/business-hours", response_model=SalonSchema)
async def update_salon_business_hours(
    salon_id: int,
    hours_data: SalonBusinessHoursUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(salon_owner_required(salon_id))
):
    """
    Update salon business hours (salon owner only)
    
    Args:
        salon_id: Salon ID
        hours_data: Business hours data
        db: Database session
        current_user: Current authenticated salon owner
        
    Returns:
        Updated salon data
        
    Raises:
        HTTPException: If salon not found
    """
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    
    if salon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )
    
    # Update business hours
    salon.business_hours = hours_data.business_hours
    
    # Save changes
    db.commit()
    db.refresh(salon)
    
    return salon

@router.get("/{salon_id}/services", response_model=List[ServiceBrief])
async def list_salon_services(
    salon_id: int,
    is_active: bool = True,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of services offered by a salon
    
    Args:
        salon_id: Salon ID
        is_active: Filter by active status
        category: Filter by service category
        db: Database session
        
    Returns:
        List of service brief data
        
    Raises:
        HTTPException: If salon not found
    """
    # Check if salon exists
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    
    if salon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )
    
    # Build query
    query = db.query(Service).filter(
        Service.salon_id == salon_id,
        Service.is_active == is_active
    )
    
    # Apply category filter if provided
    if category:
        query = query.filter(func.lower(Service.category) == category.lower())
    
    # Get services
    services = query.all()
    
    return services

@router.get("/{salon_id}/stylists", response_model=List[StylistBrief])
async def list_salon_stylists(
    salon_id: int,
    is_active: bool = True,
    specialty: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a list of stylists working at a salon
    
    Args:
        salon_id: Salon ID
        is_active: Filter by active status
        specialty: Filter by stylist specialty
        db: Database session
        
    Returns:
        List of stylist brief data
        
    Raises:
        HTTPException: If salon not found
    """
    # Check if salon exists
    salon = db.query(Salon).filter(Salon.id == salon_id).first()
    
    if salon is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salon not found"
        )
    
    # Build query
    query = db.query(Stylist).filter(
        Stylist.salon_id == salon_id,
        Stylist.is_active == is_active
    )
    
    # Apply specialty filter if provided - more complex because specialties is JSON array
    # In a production environment, we would use a proper JSON query for this
    stylists = query.all()
    
    if specialty:
        specialty = specialty.lower()
        # Filter in Python (not ideal for large datasets)
        stylists = [
            s for s in stylists 
            if s.specialties and any(spec.lower() == specialty for spec in s.specialties)
        ]
    
    return stylists