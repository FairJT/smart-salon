from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, UserRole
from app.schemas import User as UserSchema, UserUpdate, UserChangePassword, UserRoleUpdate
from app.auth import (
    get_current_active_user, 
    get_admin_user, 
    hash_password, 
    verify_password
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/me", response_model=UserSchema)
async def get_user_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the current authenticated user's profile
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile data
    """
    return current_user

@router.put("/me", response_model=UserSchema)
async def update_user_me(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update the current authenticated user's profile
    
    Args:
        user_data: Updated user data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated user profile
    """
    # Update user data
    for key, value in user_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(current_user, key, value)
    
    # Save changes
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: UserChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Change the current user's password
    
    Args:
        password_data: Password change data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )
    
    # Hash new password
    current_user.password_hash = hash_password(password_data.new_password)
    
    # Save changes
    db.commit()
    
    return {"message": "Password changed successfully"}

# Admin routes

@router.get("", response_model=List[UserSchema])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: UserRole = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get a list of users (admin only)
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        role: Filter users by role
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        List of users
    """
    query = db.query(User)
    
    # Apply role filter if provided
    if role:
        query = query.filter(User.role == role)
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return users

@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Get user by ID (admin only)
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        User data
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update user by ID (admin only)
    
    Args:
        user_id: User ID
        user_data: Updated user data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Updated user data
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user data
    for key, value in user_data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(user, key, value)
    
    # Save changes
    db.commit()
    db.refresh(user)
    
    return user

@router.put("/{user_id}/role", response_model=UserSchema)
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Update user role (admin only)
    
    Args:
        user_id: User ID
        role_data: New role data
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Updated user data
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user role
    user.role = role_data.role
    
    # Save changes
    db.commit()
    db.refresh(user)
    
    return user

@router.put("/{user_id}/activate", response_model=UserSchema)
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Activate a user (admin only)
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Updated user data
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Activate user
    user.is_active = True
    
    # Save changes
    db.commit()
    db.refresh(user)
    
    return user

@router.put("/{user_id}/deactivate", response_model=UserSchema)
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user)
):
    """
    Deactivate a user (admin only)
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated admin user
        
    Returns:
        Updated user data
        
    Raises:
        HTTPException: If user not found or is trying to deactivate themselves
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Deactivate user
    user.is_active = False
    
    # Save changes
    db.commit()
    db.refresh(user)
    
    return user