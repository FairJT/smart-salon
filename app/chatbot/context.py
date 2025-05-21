from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import User, ChatLog
from app.chatbot.openai_client import OpenAIClient
from app.chatbot.prompts import SystemPrompts

class ChatContext:
    """Class for managing chat context and history"""
    
    def __init__(self, user_id: int):
        """
        Initialize chat context for a user
        
        Args:
            user_id: User ID
        """
        self.user_id = user_id
        self.messages = []
        self.initialized = False
    
    def load_recent_history(self, db: Session, limit: int = 5) -> None:
        """
        Load recent chat history from the database
        
        Args:
            db: Database session
            limit: Maximum number of recent messages to load
        """
        # Get the user's recent chat logs
        recent_logs = db.query(ChatLog).filter(
            ChatLog.user_id == self.user_id
        ).order_by(ChatLog.created_at.desc()).limit(limit).all()
        
        # Reverse to get chronological order
        recent_logs = recent_logs[::-1]
        
        # Clear existing messages
        self.messages = []
        
        # Add system prompt
        self.messages.append({
            "role": "system",
            "content": SystemPrompts.get_base_system_prompt()
        })
        
        # Add recent messages to context
        for log in recent_logs:
            # Add user message
            self.messages.append({
                "role": "user",
                "content": log.message
            })
            
            # Add assistant response
            self.messages.append({
                "role": "assistant",
                "content": log.response
            })
        
        self.initialized = True
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the context
        
        Args:
            role: Message role ("user" or "assistant")
            content: Message content
        """
        self.messages.append({
            "role": role,
            "content": content
        })
    
    def get_formatted_messages(self) -> List[Dict[str, str]]:
        """
        Get the formatted message history for the OpenAI API
        
        Returns:
            List of message dictionaries
        """
        return self.messages
    
    def save_interaction(self, db: Session, user_message: str, assistant_response: str, 
                         context: Optional[Dict[str, Any]] = None) -> None:
        """
        Save a chat interaction to the database
        
        Args:
            db: Database session
            user_message: User's message
            assistant_response: Assistant's response
            context: Optional context information
        """
        # Create a new chat log
        chat_log = ChatLog(
            user_id=self.user_id,
            message=user_message,
            response=assistant_response,
            intent=None,  # Could extract intent in a more sophisticated implementation
            context=context
        )
        
        # Add to database
        db.add(chat_log)
        db.commit()