import openai
import logging
from typing import List, Dict, Any, Optional

from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)

# Configure OpenAI client
openai.api_key = settings.OPENAI_API_KEY

class OpenAIClient:
    """Client for interacting with OpenAI API"""
    
    @staticmethod
    def create_embedding(text: str) -> List[float]:
        """
        Create an embedding vector for the given text using OpenAI's API
        
        Args:
            text: Text to create embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = openai.Embedding.create(
                input=text,
                model="text-embedding-ada-002"
            )
            
            # Extract the embedding vector from the response
            embedding = response["data"][0]["embedding"]
            return embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            # Return an empty vector as fallback
            return []
    
    @staticmethod
    def chat_completion(
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Optional[str]:
        """
        Generate a chat completion using OpenAI's API
        
        Args:
            messages: List of message dictionaries (role and content)
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in the response
            
        Returns:
            Generated response text or None if an error occurs
        """
        try:
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract the response text
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            return None
    
    @staticmethod
    def extract_search_query(user_message: str) -> str:
        """
        Extract a search query from a user message
        
        Args:
            user_message: User's chat message
            
        Returns:
            Search query extracted from the message
        """
        try:
            # Create a system message to guide the model
            system_message = {
                "role": "system",
                "content": """
                You are a specialized AI that extracts search queries from user messages.
                Given a user message, extract the key beauty service or salon-related search query.
                Only return the search query, nothing else.
                Example:
                User: "I'm looking for a good place to get a haircut in Tehran"
                You: "haircut in Tehran"
                Keep it concise and focused on beauty services, salons, or stylists.
                """
            }
            
            # Add the user message
            user = {"role": "user", "content": user_message}
            
            # Generate the search query
            response = openai.ChatCompletion.create(
                model=settings.OPENAI_MODEL,
                messages=[system_message, user],
                temperature=0.3,
                max_tokens=50
            )
            
            # Extract the response text
            search_query = response.choices[0].message.content.strip()
            
            # Log the extracted query
            logger.info(f"Extracted search query: '{search_query}' from message: '{user_message}'")
            
            return search_query
            
        except Exception as e:
            logger.error(f"Error extracting search query: {str(e)}")
            # Fall back to using the original message
            return user_message