#!/usr/bin/env python
"""
Setup script for the Smart Beauty Salon platform.
This script initializes the database and creates test data.
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import application components
from app.database import engine, SessionLocal, Base, get_db_context
from app.models import (
    User, UserRole, Salon, Service, Stylist, 
    Appointment, AppointmentStatus, AppointmentType,
    Rating, RatingTargetType
)
from app.auth import hash_password
from app.chatbot.embeddings import EmbeddingService
from app.chatbot.faiss_index import faiss_index

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

def create_test_data():
    """Create test data for development"""
    with get_db_context() as db:
        # Check if data already exists
        if db.query(User).count() > 0:
            print("⚠️ Database already contains data. Skipping test data creation.")
            return
        
        print("Creating test users...")
        # Create admin user
        admin = User(
            email="admin@example.com",
            full_name="Admin User",
            password_hash=hash_password("adminpassword"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        
        # Create salon owner
        salon_owner = User(
            email="salon@example.com",
            full_name="Salon Owner",
            password_hash=hash_password("password"),
            role=UserRole.SALON_OWNER,
            is_active=True,
            is_verified=True,
        )
        db.add(salon_owner)
        
        # Create client
        client = User(
            email="client@example.com",
            full_name="Test Client",
            password_hash=hash_password("password"),
            role=UserRole.CLIENT,
            is_active=True,
            is_verified=True,
        )
        db.add(client)
        
        # Create stylist user
        stylist_user = User(
            email="stylist@example.com",
            full_name="Test Stylist",
            password_hash=hash_password("password"),
            role=UserRole.STYLIST,
            is_active=True,
            is_verified=True,
        )
        db.add(stylist_user)
        
        # Commit users
        db.commit()
        
        print("Creating test salon...")
        # Create a test salon
        salon = Salon(
            name="Beauty Haven",
            description="A premium beauty salon offering a wide range of services",
            owner_id=salon_owner.id,
            address="123 Beauty Street",
            city="Tehran",
            country="Iran",
            phone_number="+98123456789",
            email="info@beautyhaven.com",
            is_active=True,
            business_hours={
                "monday": {"open": "09:00", "close": "18:00"},
                "tuesday": {"open": "09:00", "close": "18:00"},
                "wednesday": {"open": "09:00", "close": "18:00"},
                "thursday": {"open": "09:00", "close": "18:00"},
                "friday": {"open": "09:00", "close": "18:00"},
                "saturday": {"open": "10:00", "close": "16:00"},
                "sunday": {"open": "10:00", "close": "16:00"}
            }
        )
        db.add(salon)
        db.commit()
        
        print("Creating test services...")
        # Create test services
        services = [
            Service(
                name="Women's Haircut",
                description="Professional women's haircut by our expert stylists",
                salon_id=salon.id,
                category="haircut",
                duration_minutes=60,
                price=50.0,
                is_active=True,
                allows_online_booking=True
            ),
            Service(
                name="Men's Haircut",
                description="Professional men's haircut by our expert stylists",
                salon_id=salon.id,
                category="haircut",
                duration_minutes=30,
                price=30.0,
                is_active=True,
                allows_online_booking=True
            ),
            Service(
                name="Hair Coloring",
                description="Professional hair coloring service",
                salon_id=salon.id,
                category="color",
                duration_minutes=120,
                price=100.0,
                is_active=True,
                allows_online_booking=True
            ),
            Service(
                name="Manicure",
                description="Professional manicure service",
                salon_id=salon.id,
                category="nails",
                duration_minutes=45,
                price=35.0,
                is_active=True,
                allows_online_booking=True,
                available_at_home=True,
                home_service_fee=15.0
            ),
            Service(
                name="Pedicure",
                description="Professional pedicure service",
                salon_id=salon.id,
                category="nails",
                duration_minutes=60,
                price=45.0,
                is_active=True,
                allows_online_booking=True,
                available_at_home=True,
                home_service_fee=15.0
            ),
            Service(
                name="Facial",
                description="Rejuvenating facial treatment",
                salon_id=salon.id,
                category="skin",
                duration_minutes=90,
                price=80.0,
                is_active=True,
                allows_online_booking=True
            ),
            Service(
                name="Makeup",
                description="Professional makeup for any occasion",
                salon_id=salon.id,
                category="makeup",
                duration_minutes=60,
                price=70.0,
                is_active=True,
                allows_online_booking=True,
                available_at_home=True,
                home_service_fee=20.0
            ),
            Service(
                name="Hair Treatment",
                description="Deep conditioning hair treatment",
                salon_id=salon.id,
                category="hair",
                duration_minutes=45,
                price=55.0,
                is_active=True,
                allows_online_booking=True
            ),
            Service(
                name="Hair Extensions",
                description="Professional hair extensions service",
                salon_id=salon.id,
                category="hair",
                duration_minutes=180,
                price=200.0,
                is_active=True,
                allows_online_booking=True
            ),
            Service(
                name="Eyebrow Threading",
                description="Precise eyebrow threading service",
                salon_id=salon.id,
                category="eyebrows",
                duration_minutes=15,
                price=15.0,
                is_active=True,
                allows_online_booking=True
            )
        ]
        
        db.add_all(services)
        db.commit()
        
        print("Creating test stylist...")
        # Create a test stylist
        stylist = Stylist(
            user_id=stylist_user.id,
            salon_id=salon.id,
            full_name=stylist_user.full_name,
            bio="Experienced stylist with over 5 years in the industry",
            years_of_experience=5,
            specialties=["haircut", "color", "hair"],
            is_active=True,
            working_hours={
                "monday": [{"start": "09:00", "end": "17:00"}],
                "tuesday": [{"start": "09:00", "end": "17:00"}],
                "wednesday": [{"start": "09:00", "end": "17:00"}],
                "thursday": [{"start": "09:00", "end": "17:00"}],
                "friday": [{"start": "09:00", "end": "17:00"}]
            }
        )
        db.add(stylist)
        db.commit()
        
        # Add services to stylist
        stylist.services = services[:5]  # First 5 services
        db.commit()
        
        print("✅ Test data created successfully")
        
        print("Generating service embeddings...")
        # Generate embeddings for services
        EmbeddingService.generate_embeddings_for_all_services(db)
        
        print("Building FAISS index...")
        # Build FAISS index
        faiss_index.build_index(db)
        
        print("✅ FAISS index built successfully")

def main():
    parser = argparse.ArgumentParser(description="Setup the Smart Beauty Salon platform")
    parser.add_argument("--create-tables", action="store_true", help="Create database tables")
    parser.add_argument("--create-test-data", action="store_true", help="Create test data for development")
    parser.add_argument("--all", action="store_true", help="Perform all setup operations")
    
    args = parser.parse_args()
    
    if args.all or args.create_tables:
        create_tables()
    
    if args.all or args.create_test_data:
        create_test_data()
    
    if not (args.all or args.create_tables or args.create_test_data):
        parser.print_help()

if __name__ == "__main__":
    main()