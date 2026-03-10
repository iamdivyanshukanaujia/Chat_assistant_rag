"""
Memory routes for entity and profile management.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from src.system import system
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/entities/{session_id}")
async def get_entities(session_id: str) -> Dict[str, Any]:
    """
    Get tracked entities for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Tracked entities and profile
    """
    try:
        profile = system.memory_manager.get_student_profile(session_id)
        
        return {
            "session_id": session_id,
            "profile": {
                "program": profile.get("program"),
                "department": profile.get("department"),
                "year": profile.get("year"),
                "international_student": profile.get("international_student", False)
            },
            "topics_asked": profile.get("previously_asked_topics", []),
            "courses_interested": profile.get("courses_of_interest", [])
        }
        
    except Exception as e:
        logger.error(f"Get entities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profile/{session_id}")
async def update_profile(session_id: str, profile_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Manually update student profile.
    
    Args:
        session_id: Session identifier
        profile_data: Profile data to update
    
    Returns:
        Success message
    """
    try:
        system.memory_manager.update_student_profile(session_id, profile_data)
        return {"message": f"Profile updated for session {session_id}"}
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entities/{session_id}")
async def clear_entities(session_id: str) -> Dict[str, str]:
    """
    Clear all entities for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Success message
    """
    try:
        system.memory_manager.entity_memory.clear_session(session_id)
        return {"message": f"Cleared entities for session {session_id}"}
        
    except Exception as e:
        logger.error(f"Clear entities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
