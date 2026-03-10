"""
Student profile routes - Fetch student data from university systems
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Will be set by main.py
_data_provider = None

def init_profile_routes(data_provider):
    """Initialize routes with data provider."""
    global _data_provider
    _data_provider = data_provider


@router.get("/{student_id}")
def get_student_profile(student_id: str) -> Dict[str, Any]:
    """
    Get complete student profile from university systems (CSV files).
    This fetches real-time data from attendance, grades, and placement systems.
    """
    try:
        if _data_provider is None:
            raise HTTPException(status_code=500, detail="Data provider not initialized")
        
        # Fetch from CSV files via data provider
        profile = _data_provider.get_student_data(student_id)
        
        return {
            "student_id": student_id,
            "profile": profile,
            "source": "university_systems"
        }
    
    except Exception as e:
        logger.error(f"Failed to fetch profile for {student_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
