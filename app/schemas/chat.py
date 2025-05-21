from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.schemas.service import ServiceSearchResult
from app.schemas.salon import SalonBrief

# Schema for chat message request
class ChatMessageRequest(BaseModel):
    message: str
    location: Optional[str] = None

# Schema for chat message response
class ChatMessageResponse(BaseModel):
    message: str
    intent: Optional[str] = None
    recommended_services: Optional[List[ServiceSearchResult]] = None
    recommended_salons: Optional[List[SalonBrief]] = None
    generated_at: datetime = datetime.utcnow()

# Schema for chat history
class ChatHistoryItem(BaseModel):
    id: int
    message: str
    response: str
    created_at: datetime
    
    class Config:
        orm_mode = True

# Schema for paginated chat history
class ChatHistory(BaseModel):
    items: List[ChatHistoryItem]
    total: int
    page: int
    page_size: int
    
# Schema for AI-generated recommendations
class AIRecommendation(BaseModel):
    services: List[ServiceSearchResult]
    message: str
    query_text: str