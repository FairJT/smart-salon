import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    # App settings
    APP_NAME: str = "Smart Beauty Salon API"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "A smart platform for beauty salons, stylists, and clients"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smart_salon.db")
    
    # JWT Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # OpenAI API
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]  # In production, specify your frontend domain
    
    # Testing
    TESTING: bool = os.getenv("TESTING", "False").lower() in ("true", "1", "t")

# Create settings instance
settings = Settings()