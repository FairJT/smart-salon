from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user
from app.database import get_db
from app.models.user import User, UserRole

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Verify that the current user is active
    
    Args:
        current_user: User from JWT token
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

def role_required(*roles: UserRole):
    """
    Dependency factory for role-based access control
    
    Args:
        roles: Roles that are allowed to access the endpoint
        
    Returns:
        Dependency function that checks if the current user has one of the required roles
    """
    
    def role_checker(current_user: User = Depends(get_current_user)):
        """
        Check if the current user has one of the required roles
        
        Args:
            current_user: User from JWT token
            
        Returns:
            Current user if authorized
            
        Raises:
            HTTPException: If user does not have required role
        """
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role.value} not authorized to access this resource"
            )
        return current_user
    
    return role_checker

# Create specific role dependencies
get_admin_user = role_required(UserRole.ADMIN)
get_salon_owner = role_required(UserRole.SALON_OWNER)
get_stylist = role_required(UserRole.STYLIST)
get_client = role_required(UserRole.CLIENT)

# Combined roles
get_salon_staff = role_required(UserRole.SALON_OWNER, UserRole.STYLIST)
get_any_user = get_current_active_user  # Any active user

def is_salon_owner(salon_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> bool:
    """
    Check if the current user is the owner of the specified salon
    
    Args:
        salon_id: Salon ID to check
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        True if user is the salon owner, False otherwise
    """
    # Admin users can access any salon
    if current_user.role == UserRole.ADMIN:
        return True
    
    # Check if user is the owner of the salon
    if current_user.role == UserRole.SALON_OWNER:
        salon = db.query(Salon).filter(Salon.id == salon_id, Salon.owner_id == current_user.id).first()
        return salon is not None
    
    return False

def salon_owner_required(salon_id: int):
    """
    Dependency factory for salon ownership access control
    
    Args:
        salon_id: Salon ID to check
        
    Returns:
        Dependency function that checks if the current user owns the specified salon
    """
    
    def salon_owner_checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        """
        Check if the current user owns the specified salon
        
        Args:
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            Current user if authorized
            
        Raises:
            HTTPException: If user is not the salon owner
        """
        if not is_salon_owner(salon_id, current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this salon"
            )
        return current_user
    
    return salon_owner_checker