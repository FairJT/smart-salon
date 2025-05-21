from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel

class ChatLog(Base, BaseModel):
    """Model for storing chat interactions between users and the AI assistant"""
    
    # User information
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Chat content
    message = Column(Text, nullable=False)  # User's message
    response = Column(Text, nullable=False)  # AI's response
    
    # Context and metadata
    intent = Column(String, nullable=True)  # Classified intent of the message
    entities = Column(JSON, nullable=True)  # Extracted entities from the message
    context = Column(JSON, nullable=True)  # Context information used for the response
    
    # Service search details
    search_query = Column(String, nullable=True)  # Search query derived from the message
    recommended_services = Column(JSON, nullable=True)  # IDs of services recommended
    recommended_salons = Column(JSON, nullable=True)  # IDs of salons recommended
    recommended_stylists = Column(JSON, nullable=True)  # IDs of stylists recommended
    
    # Relationships
    user = relationship("User", back_populates="chat_logs")
    
    def __repr__(self):
        return f"<ChatLog {self.id}: User {self.user_id}>"