from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from app.database import get_db
from app.models import User, Salon, Service, UserRole
from app.schemas import (
    Service as ServiceSchema,
    ServiceCreate,
    ServiceUpdate,
    ServiceBrief,
    ServiceSearchResult
)
from app.auth import (
    get_current_active_user,
    salon_owner_required,
    get_salon_staff
)
from app.chatbot.embeddings import EmbeddingService
from app.chatbot.faiss_index import faiss_index
from app.chatbot.openai_client import OpenAIClient

router = APIRouter(
    prefix="/services",
    tags=["Services"],
)

@router.post("", response_model=ServiceSchema, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    salon_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(salon_owner_required(salon_id))
):
    """
    Create a new service for a salon (salon owner only)
    
    Args:
        service_data: Service creation data
        salon_id: Salon ID
        db: Database session
        current_user: Current authenticated salon owner
        
    Returns:
        Created service data
        
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
    
    # Create new service
    new_service = Service(
        **service_data.dict(),
        salon_id=salon_id,
        is_active=True
    )
    
    # Save to database
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    
    # Generate embedding for the service
    embedding = EmbeddingService.generate_service_embedding(new_service)
    new_service.embedding_vector = embedding
    db.commit()
    
    # Rebuild FAISS index if it's initialized
    if faiss_index.initialized:
        faiss_index.build_index(db)
    
    return new_service

@router.get("", response_model=List[ServiceBrief])
async def list_services(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get a list of services with optional filtering
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        category: Filter by category
        min_price: Filter by minimum price
        max_price: Filter by maximum price
        is_active: Filter by active status
        db: Database session
        
    Returns:
        List of service brief data
    """
    query = db.query(Service).filter(Service.is_active == is_active)
    
    # Apply category filter if provided
    if category:
        query = query.filter(func.lower(Service.category) == category.lower())
    
    # Apply price filters if provided
    if min_price is not None:
        query = query.filter(Service.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Service.price <= max_price)
    
    # Apply pagination
    services = query.offset(skip).limit(limit).all()
    
    return services

@router.get("/search", response_model=List[ServiceSearchResult])
async def search_services(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Search for services using FAISS similarity search
    
    Args:
        query: Search query text
        limit: Maximum number of results to return
        db: Database session
        
    Returns:
        List of service search results
    """
    # Initialize FAISS index if not already initialized
    if not faiss_index.initialized:
        faiss_index.build_index(db)
    
    # Search for similar services
    results = faiss_index.search(query, top_k=limit)
    
    # Get detailed service information
    service_details = faiss_index.get_service_details(results, db)
    
    return service_details

@router.get("/{service_id}", response_model=ServiceSchema)
async def get_service(
    service_id: int,
    db: Session = Depends(get_db)
):
    """
    Get service by ID
    
    Args:
        service_id: Service ID
        db: Database session
        
    Returns:
        Service data
        
    Raises:
        HTTPException: If service not found
    """
    service = db.query(Service).filter(Service.id == service_id).first()
    
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    return service

@router.put("/{service_id}", response_model=ServiceSchema)
async def update_service(
    service_id: int,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update service by ID (salon owner or staff only)
    
    Args:
        service_id: Service ID
        service_data: Updated service data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated service data
        
    Raises:
        HTTPException: If service not found or user not authorized
    """
    # Get the service
    service = db.query(Service).filter(Service.id == service_id).first()
    
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Check authorization - must be salon owner or administrator
    if (current_user.role != UserRole.ADMIN and 
        not db.query(Salon).filter(Salon.id == service.salon_id, Salon.owner_id == current_user.id).first()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this service"
        )
    
    # Update service data
    for key, value in service_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(service, key, value)
    
    # Save changes
    db.commit()
    db.refresh(service)
    
    # Update embedding if service content changed
    if any(key in service_data.dict(exclude_unset=True) for key in ['name', 'description', 'category']):
        embedding = EmbeddingService.generate_service_embedding(service)
        service.embedding_vector = embedding
        db.commit()
        
        # Rebuild FAISS index if it's initialized
        if faiss_index.initialized:
            faiss_index.build_index(db)
    
    return service

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete service by ID (salon owner or admin only)
    
    Args:
        service_id: Service ID
        db: Database session
        current_user: Current authenticated user
        
    Raises:
        HTTPException: If service not found or user not authorized
    """
    # Get the service
    service = db.query(Service).filter(Service.id == service_id).first()
    
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Check authorization - must be salon owner or administrator
    if (current_user.role != UserRole.ADMIN and 
        not db.query(Salon).filter(Salon.id == service.salon_id, Salon.owner_id == current_user.id).first()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this service"
        )
    
    # Delete service (or mark as inactive for better data integrity)
    service.is_active = False
    db.commit()
    
    # Rebuild FAISS index if it's initialized
    if faiss_index.initialized:
        faiss_index.build_index(db)
    
    return None