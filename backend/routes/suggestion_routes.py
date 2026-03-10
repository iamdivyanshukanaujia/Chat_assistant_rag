"""
Suggestion routes for proactive suggestions API.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional

from src.proactive.suggestion_engine import ProactiveSuggestionEngine
from src.proactive.data_provider import StudentDataProvider
from src.memory.memory_manager import MemoryManager
from src.utils.logger import get_logger

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])
logger = get_logger(__name__)

# Initialize suggestion engine (will be set by system initialization)
_suggestion_engine: Optional[ProactiveSuggestionEngine] = None


def init_suggestion_routes(engine: ProactiveSuggestionEngine):
    """
    Initialize suggestion routes with engine instance.
    
    Args:
        engine: ProactiveSuggestionEngine instance
    """
    global _suggestion_engine
    _suggestion_engine = engine
    logger.info("Suggestion routes initialized")


@router.get("/{student_id}")
async def get_suggestions(
    student_id: str,
    max_results: int = 10,
    priority: Optional[str] = None
) -> Dict:
    """
    Get proactive suggestions for a student.
    
    Args:
        student_id: Student ID
        max_results: Maximum number of suggestions
        priority: Optional priority filter (critical, high, medium, low)
    
    Returns:
        {suggestions: [...], count: N}
    """
    if not _suggestion_engine:
        raise HTTPException(status_code=500, detail="Suggestion engine not initialized")
    
    try:
        priority_filter = [priority] if priority else None
        
        suggestions = _suggestion_engine.get_suggestions(
            student_id=student_id,
            max_suggestions=max_results,
            priority_filter=priority_filter
        )
        
        logger.info(f"Returned {len(suggestions)} suggestions for {student_id}")
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "student_id": student_id
        }
    
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/critical")
async def get_critical_alerts(student_id: str) -> Dict:
    """
    Get only critical alerts for a student.
    
    Args:
        student_id: Student ID
    
    Returns:
        {suggestions: [...], count: N}
    """
    if not _suggestion_engine:
        raise HTTPException(status_code=500, detail="Suggestion engine not initialized")
    
    try:
        suggestions = _suggestion_engine.get_critical_alerts(student_id)
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "student_id": student_id
        }
    
    except Exception as e:
        logger.error(f"Error getting critical alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{student_id}/type/{suggestion_type}")
async def get_suggestions_by_type(
    student_id: str,
    suggestion_type: str
) -> Dict:
    """
    Get suggestions of a specific type.
    
    Args:
        student_id: Student ID
        suggestion_type: Type (deadline, alert, opportunity, reminder, achievement)
    
    Returns:
        {suggestions: [...], count: N}
    """
    if not _suggestion_engine:
        raise HTTPException(status_code=500, detail="Suggestion engine not initialized")
    
    try:
        suggestions = _suggestion_engine.get_suggestions_by_type(
            student_id,
            suggestion_type
        )
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "student_id": student_id,
            "type": suggestion_type
        }
    
    except Exception as e:
        logger.error(f"Error getting suggestions by type: {e}")
        raise HTTPException(status_code=500, detail=str(e))
