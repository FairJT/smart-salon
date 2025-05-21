import numpy as np
import faiss
import logging
from typing import List, Dict, Any, Tuple, Optional
import os
import pickle
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Service, Salon
from app.chatbot.openai_client import OpenAIClient

# Set up logging
logger = logging.getLogger(__name__)

class FAISSIndex:
    """Service for FAISS vector similarity search"""
    
    def __init__(self):
        """Initialize FAISS index"""
        self.index = None
        self.service_ids = []
        self.initialized = False
        self.last_updated = None
        
    def build_index(self, db: Session) -> None:
        """
        Build FAISS index from service embeddings in the database
        
        Args:
            db: Database session
        """
        # Get all active services with embeddings
        services = db.query(Service).filter(
            Service.is_active == True,
            Service.embedding_vector.is_not(None)
        ).all()
        
        if not services:
            logger.warning("No services with embeddings found in the database")
            return
        
        # Extract embeddings and service IDs
        embeddings = []
        service_ids = []
        
        for service in services:
            if service.embedding_vector:
                embeddings.append(service.embedding_vector)
                service_ids.append(service.id)
        
        if not embeddings:
            logger.warning("No valid embeddings found in the database")
            return
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Get dimensionality of embeddings
        d = embeddings_array.shape[1]
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(d)
        
        # Add vectors to the index
        self.index.add(embeddings_array)
        
        # Store service IDs
        self.service_ids = service_ids
        
        # Set initialization flag
        self.initialized = True
        self.last_updated = datetime.utcnow()
        
        logger.info(f"FAISS index built with {len(service_ids)} services")
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for similar services using FAISS
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of tuples (service_id, similarity_score)
        """
        if not self.initialized or self.index is None:
            logger.warning("FAISS index not initialized")
            return []
        
        # Generate embedding for the query
        query_embedding = OpenAIClient.create_embedding(query)
        
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return []
        
        # Convert to numpy array
        query_array = np.array([query_embedding]).astype('float32')
        
        # Search the index
        distances, indices = self.index.search(query_array, min(top_k, len(self.service_ids)))
        
        # Convert to list of tuples (service_id, similarity_score)
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            distance = distances[0][i]
            
            # Convert distance to similarity score (lower distance = higher similarity)
            similarity = 1.0 / (1.0 + distance)
            
            if idx < len(self.service_ids):
                service_id = self.service_ids[idx]
                results.append((service_id, similarity))
        
        return results
    
    def get_service_details(self, results: List[Tuple[int, float]], db: Session) -> List[Dict[str, Any]]:
        """
        Get detailed information for search results
        
        Args:
            results: List of tuples (service_id, similarity_score)
            db: Database session
            
        Returns:
            List of dictionaries with service details
        """
        if not results:
            return []
        
        # Get service IDs
        service_ids = [service_id for service_id, _ in results]
        
        # Get services from database
        services = db.query(Service).filter(Service.id.in_(service_ids)).all()
        
        # Get salons for these services
        salon_ids = [service.salon_id for service in services]
        salons = db.query(Salon).filter(Salon.id.in_(salon_ids)).all()
        
        # Create salon ID to name mapping
        salon_map = {salon.id: salon for salon in salons}
        
        # Create similarity score mapping
        similarity_map = {service_id: score for service_id, score in results}
        
        # Create result list
        result_list = []
        for service in services:
            salon = salon_map.get(service.salon_id)
            if salon:
                result_list.append({
                    "id": service.id,
                    "name": service.name,
                    "category": service.category,
                    "price": service.price,
                    "duration_minutes": service.duration_minutes,
                    "image_url": service.image_url,
                    "is_active": service.is_active,
                    "salon_id": salon.id,
                    "salon_name": salon.name,
                    "salon_city": salon.city,
                    "similarity_score": similarity_map.get(service.id, 0)
                })
        
        # Sort by similarity score
        result_list.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return result_list

# Singleton instance
faiss_index = FAISSIndex()