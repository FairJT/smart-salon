from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User, ChatLog
from app.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistory,
    ChatHistoryItem,
    AIRecommendation
)
from app.auth import get_current_active_user

from app.chatbot.openai_client import OpenAIClient
from app.chatbot.faiss_index import faiss_index
from app.chatbot.context import ChatContext
from app.chatbot.prompts import SystemPrompts

router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"],
)

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    message_data: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a message to the chatbot
    
    Args:
        message_data: Message data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Chatbot response
    """
    # Initialize FAISS index if not already initialized
    if not faiss_index.initialized:
        faiss_index.build_index(db)
    
    # Initialize chat context
    chat_context = ChatContext(current_user.id)
    chat_context.load_recent_history(db)
    
    # Extract search query from user message
    search_query = OpenAIClient.extract_search_query(message_data.message)
    
    # Search for similar services
    search_results = faiss_index.search(search_query, top_k=5)
    service_details = faiss_index.get_service_details(search_results, db)
    
    # Prepare system prompt based on search results
    if service_details:
        system_prompt = SystemPrompts.get_service_recommendation_prompt(service_details, message_data.message)
    else:
        system_prompt = SystemPrompts.get_no_results_prompt(message_data.message)
    
    # Add user message to context
    chat_context.add_message("user", message_data.message)
    
    # Prepare messages for AI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message_data.message}
    ]
    
    # Get AI response
    ai_response = OpenAIClient.chat_completion(messages)
    
    if not ai_response:
        ai_response = "I'm sorry, I'm having trouble processing your request right now. Could you try again?"
    
    # Add AI response to context
    chat_context.add_message("assistant", ai_response)
    
    # Save interaction to database
    context_data = {
        "search_query": search_query,
        "service_results": [s["id"] for s in service_details],
        "location": message_data.location
    }
    
    chat_context.save_interaction(db, message_data.message, ai_response, context_data)
    
    # Prepare response
    response = ChatMessageResponse(
        message=ai_response,
        intent="service_recommendation" if service_details else "general_inquiry",
        recommended_services=service_details[:3] if service_details else None,
        generated_at=datetime.utcnow()
    )
    
    return response

@router.get("/history", response_model=ChatHistory)
async def get_chat_history(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get chat history for the current user
    
    Args:
        page: Page number
        page_size: Items per page
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Paginated chat history
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count
    total = db.query(ChatLog).filter(ChatLog.user_id == current_user.id).count()
    
    # Get chat logs
    chat_logs = db.query(ChatLog).filter(
        ChatLog.user_id == current_user.id
    ).order_by(ChatLog.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Create history items
    items = [
        ChatHistoryItem(
            id=log.id,
            message=log.message,
            response=log.response,
            created_at=log.created_at
        )
        for log in chat_logs
    ]
    
    # Create response
    response = ChatHistory(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )
    
    return response

@router.post("/recommend", response_model=AIRecommendation)
async def get_ai_recommendations(
    message_data: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get AI recommendations based on a message
    
    Args:
        message_data: Message data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        AI recommendations
    """
    # Initialize FAISS index if not already initialized
    if not faiss_index.initialized:
        faiss_index.build_index(db)
    
    # Extract search query from user message
    search_query = OpenAIClient.extract_search_query(message_data.message)
    
    # Search for similar services
    search_results = faiss_index.search(search_query, top_k=10)
    service_details = faiss_index.get_service_details(search_results, db)
    
    # Prepare system prompt for explanation
    system_prompt = f"""
    You are a helpful beauty salon assistant. 
    The user has queried: "{message_data.message}"
    
    Based on their query, create a brief explanation of why the following beauty services might be relevant to them.
    Keep your response to 2-3 sentences, focusing on how these services match their needs.
    Be conversational and helpful, but concise.
    """
    
    # Prepare messages for AI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Please explain why these services might be relevant to my request."}
    ]
    
    # Get AI response
    explanation = OpenAIClient.chat_completion(messages, max_tokens=150)
    
    if not explanation:
        explanation = "Here are some services that might interest you based on your request."
    
    # Create response
    response = AIRecommendation(
        services=service_details,
        message=explanation,
        query_text=search_query
    )
    
    return response