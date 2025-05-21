import json
import logging
from typing import List, Dict, Any, Tuple, Optional

from sqlalchemy.orm import Session

from app.models import Service
from app.chatbot.openai_client import OpenAIClient

# Set up logging
logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for handling text embeddings for similarity search"""
    
    @staticmethod
    def generate_service_embedding(service: Service) -> List[float]:
        """
        Generate an embedding vector for a service
        
        Args:
            service: Service model instance
            
        Returns:
            Embedding vector as list of floats
        """
        # Create a rich text representation of the service
        service_text = f"""
        Service Name: {service.name}
        Category: {service.category}
        Description: {service.description or 'No description available'}
        Price: {service.price}
        Duration: {service.duration_minutes} minutes
        """
        
        # Generate embedding using OpenAI
        embedding = OpenAIClient.create_embedding(service_text)
        
        return embedding
    
    @staticmethod
    def generate_embeddings_for_all_services(db: Session) -> None:
        """
        Generate embeddings for all services in the database
        
        Args:
            db: Database session
        """
        # Get all active services
        services = db.query(Service).filter(Service.is_active == True).all()
        
        logger.info(f"Generating embeddings for {len(services)} services")
        
        count = 0
        for service in services:
            if not service.embedding_vector:
                # Generate embedding
                embedding = EmbeddingService.generate_service_embedding(service)
                
                # Store embedding in database
                service.embedding_vector = embedding
                
                count += 1
                
                # Commit every 10 services to avoid long transactions
                if count % 10 == 0:
                    db.commit()
                    logger.info(f"Generated embeddings for {count} services")
        
        # Final commit
        db.commit()
        logger.info(f"Finished generating embeddings for {count} services")
    
    @staticmethod
    def update_service_embedding(service: Service, db: Session) -> None:
        """
        Update the embedding vector for a service
        
        Args:
            service: Service model instance
            db: Database session
        """
        # Generate new embedding
        embedding = EmbeddingService.generate_service_embedding(service)
        
        # Update embedding in database
        service.embedding_vector = embedding
        db.commit()
        
        logger.info(f"Updated embedding for service {service.id} - {service.name}")