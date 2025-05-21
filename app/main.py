from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import logging
import os

from app.config import settings
from app.database import get_db, init_db
from app.models import User, UserRole
from app.auth.password import hash_password

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.routers import (
    auth,
    users,
    salons,
    services,
    stylists,
    appointments,
    ratings,
    chatbot,
)

# API routes
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(salons.router, prefix="/api", tags=["Salons"])
app.include_router(services.router, prefix="/api", tags=["Services"])
app.include_router(stylists.router, prefix="/api", tags=["Stylists"])
app.include_router(appointments.router, prefix="/api", tags=["Appointments"])
app.include_router(ratings.router, prefix="/api", tags=["Ratings"])
app.include_router(chatbot.router, prefix="/api", tags=["Chatbot"])

# Serve static files (for UI if needed)
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Create admin user on startup in development mode
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    if settings.ENVIRONMENT == "development":
        logger.info("Development mode: Initializing database")
        init_db()
        
        # Create test users if in development
        with get_db_context() as db:
            # Check if admin exists
            admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
            
            if not admin:
                logger.info("Creating test admin user")
                admin_user = User(
                    email="admin@example.com",
                    full_name="Admin User",
                    password_hash=hash_password("adminpassword"),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                )
                db.add(admin_user)
                
                # Create a test salon owner
                salon_owner = User(
                    email="salon@example.com",
                    full_name="Salon Owner",
                    password_hash=hash_password("password"),
                    role=UserRole.SALON_OWNER,
                    is_active=True,
                    is_verified=True,
                )
                db.add(salon_owner)
                
                # Create a test client
                client = User(
                    email="client@example.com",
                    full_name="Test Client",
                    password_hash=hash_password("password"),
                    role=UserRole.CLIENT,
                    is_active=True,
                    is_verified=True,
                )
                db.add(client)
                
                # Create a test stylist
                stylist = User(
                    email="stylist@example.com",
                    full_name="Test Stylist",
                    password_hash=hash_password("password"),
                    role=UserRole.STYLIST,
                    is_active=True,
                    is_verified=True,
                )
                db.add(stylist)
                
                db.commit()
                logger.info("Test users created successfully")


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - redirects to API docs"""
    return {"message": f"Welcome to {settings.APP_NAME}", "docs_url": "/api/docs"}