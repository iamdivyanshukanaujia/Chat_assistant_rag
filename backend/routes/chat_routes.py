"""
Chat routes for conversational interface.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.models import ChatRequest, ChatResponse, Citation
from src.system import system
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.
    
    Args:
        request: Chat request with session_id and query
    
    Returns:
        Chat response with answer and citations
    """
    try:
        logger.info(f"Chat request from session {request.session_id}: {request.query[:100]}")
        
        # Get answer from RAG engine with session_id for memory
        result = system.rag_engine.answer_question(
            query=request.query,
            session_id=request.session_id
        )
        
        # Convert citations to Pydantic models
        citations = [Citation(**c) for c in result.get("sources", [])]
        
        return ChatResponse(
            answer=result["answer"],
            citations=citations,
            confidence=result.get("confidence", 0.5),
            warnings=result.get("warnings", []),
            error=result.get("error"),
            session_id=result.get("session_id")
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_history(session_id: str) -> Dict[str, Any]:
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Conversation history
    """
    try:
        message_history = system.memory_manager.get_message_history(session_id)
        messages = message_history.messages
        
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "type": "human" if msg.type == "human" else "ai",
                "content": msg.content
            })
        
        return {
            "session_id": session_id,
            "messages": formatted_messages,
            "message_count": len(formatted_messages)
        }
        
    except Exception as e:
        logger.error(f"Get history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{session_id}")
async def clear_history(session_id: str) -> Dict[str, str]:
    """
    Clear conversation history for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Success message
    """
    try:
        system.memory_manager.clear_session(session_id)
        return {"message": f"Cleared history for session {session_id}"}
        
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
