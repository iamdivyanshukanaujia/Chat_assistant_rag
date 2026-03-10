"""
Pydantic models for request/response validation.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request model."""
    session_id: str = Field(..., description="Unique session identifier")
    query: str = Field(..., description="User query", min_length=1)
    use_cache: bool = Field(default=True, description="Whether to use caching")


class Citation(BaseModel):
    """Citation model."""
    source_id: int
    source_file: str
    section_title: str
    subsection: Optional[str] = None
    program_level: str
    category: str
    content: str
    relevance_score: float


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str
    citations: List[Citation] = []
    confidence: float
    warnings: List[str] = []
    error: Optional[str] = None
    session_id: Optional[str] = None


class StudentProfile(BaseModel):
    """Student profile model."""
    name: Optional[str] = None
    program: Optional[str] = None  # BTech / MTech / MBA / PhD
    department: Optional[str] = None
    year: Optional[int] = None
    international_student: bool = False
    courses_of_interest: List[str] = []
    previously_asked_topics: List[str] = []


class ProfileUpdateRequest(BaseModel):
    """Profile update request."""
    session_id: str
    profile_data: Dict[str, Any]


class IngestionRequest(BaseModel):
    """Ingestion request model."""
    file_path: Optional[str] = None
    directory_path: Optional[str] = None


class IngestionStatus(BaseModel):
    """Ingestion status model."""
    is_watching: bool
    files_processed: int = 0
    message: str = ""


class CacheMetrics(BaseModel):
    """Cache metrics model."""
    traditional: Dict[str, Any]
    semantic: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    components: Dict[str, bool]
