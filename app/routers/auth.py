from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserCreate, Token, Login
from app.auth import hash_password, verify_password, create_access_token
from app.config import settings

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        JWT token for the new user
        
    Raises:
        HTTPException: If email is already registered
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with hashed password
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
        phone_number=user_data.phone_number,
        location=user_data.location,
        role=user_data.role,
        is_active=True,
        is_verified=False,  # User needs to verify email
    )
    
    # Validate role (only ADMIN can create ADMIN users)
    if db_user.role == UserRole.ADMIN:
        # In a real app, we'd check if the current user is an admin
        # For MVP, we'll just prevent admin creation via this route
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create admin user through registration"
        )
    
    # Save user to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)},
        expires_delta=access_token_expires
    )
    
    # Token expiration timestamp
    expires_at = datetime.utcnow() + access_token_expires
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "user_role": db_user.role.value,
        "expires_at": expires_at
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Get JWT token (OAuth2 compatible)
    
    Args:
        form_data: OAuth2 form data (username = email, password)
        db: Database session
        
    Returns:
        JWT token for the authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get user by email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # Check user and password
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Token expiration timestamp
    expires_at = datetime.utcnow() + access_token_expires
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_role": user.role.value,
        "expires_at": expires_at
    }

@router.post("/login", response_model=Token)
async def login(login_data: Login, db: Session = Depends(get_db)):
    """
    Login with email and password
    
    Args:
        login_data: Login data (email, password)
        db: Database session
        
    Returns:
        JWT token for the authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    # Check user and password
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Token expiration timestamp
    expires_at = datetime.utcnow() + access_token_expires
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "user_role": user.role.value,
        "expires_at": expires_at
    }