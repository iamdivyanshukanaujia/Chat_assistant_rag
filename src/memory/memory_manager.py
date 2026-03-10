"""
Unified memory manager coordinating conversation and entity memory.
"""
from typing import Dict, Any, Optional
import redis

from src.utils.logger import get_logger
from src.utils.exceptions import MemoryError
from src.config import settings
from src.memory.conversation_memory import ConversationMemory
from src.memory.entity_memory import EntityMemory

logger = get_logger(__name__)


class MemoryManager:
    """Unified memory manager for conversation and entities."""
    
    def __init__(
        self,
        conversation_memory: Optional[ConversationMemory] = None,
        entity_memory: Optional[EntityMemory] = None
    ):
        """
        Initialize memory manager.
        
        Args:
            conversation_memory: Conversation memory instance (optional)
            entity_memory: Entity memory instance (optional)
        """
        # Create shared Redis client
        try:
            self.redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password if settings.redis_password else None,
                db=settings.redis_db,
                decode_responses=True
            )
            self.redis.ping()
            logger.info("Connected to Redis for memory management")
        except Exception as e:
            raise MemoryError(f"Failed to connect to Redis: {e}")
        
        # Initialize memory components
        self.conversation_memory = conversation_memory or ConversationMemory(self.redis)
        self.entity_memory = entity_memory or EntityMemory(self.redis)
        
        logger.info("Initialized MemoryManager")
    
    # Conversation Memory Methods
    
    def get_message_history(self, session_id: str):
        """Get chat message history for a session."""
        return self.conversation_memory.get_message_history(session_id)
    
    def get_conversation_summary(self, session_id: str, max_turns: int = 5) -> str:
        """Get conversation summary."""
        return self.conversation_memory.get_conversation_summary(session_id, max_turns)
    
    # Entity Memory Methods
    
    def get_student_profile(self, session_id: str) -> Dict[str, Any]:
        """Get student profile."""
        return self.entity_memory.get_student_profile(session_id)
    
    def update_student_profile(self, session_id: str, profile_data: Dict[str, Any]):
        """Update student profile."""
        self.entity_memory.update_student_profile(session_id, profile_data)
    
    def add_topic(self, session_id: str, topic: str):
        """Add topic to previously asked topics."""
        self.entity_memory.add_topic(session_id, topic)
    
    def add_course_of_interest(self, session_id: str, course: str):
        """Add course to courses of interest."""
        self.entity_memory.add_course_of_interest(session_id, course)
    
    def get_all_entities(self, session_id: str) -> Dict[str, Any]:
        """Get all tracked entities."""
        return self.entity_memory.get_entities(session_id)
    
    # Session Management
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete session context.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dict with conversation history and entities
        """
        return {
            "conversation_summary": self.get_conversation_summary(session_id),
            "student_profile": self.get_student_profile(session_id),
            "all_entities": self.get_all_entities(session_id)
        }
    
    def clear_session(self, session_id: str):
        """Clear all memory for a session."""
        logger.info(f"Clearing all memory for session: {session_id}")
        self.conversation_memory.clear_session(session_id)
        self.entity_memory.clear_session(session_id)
    
    def list_active_sessions(self):
        """List all active sessions."""
        return self.conversation_memory.list_active_sessions()
    
    # Context Building
    
    def build_context_string(self, session_id: str) -> str:
        """
        Build a context string for LLM prompting.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Formatted context string
        """
        profile = self.get_student_profile(session_id)
        
        context_parts = []
        
        # Student profile
        if profile.get("name"):
            context_parts.append(f"Student Name: {profile['name']}")
        if profile.get("program"):
            context_parts.append(f"Program: {profile['program']}")
        if profile.get("department"):
            context_parts.append(f"Department: {profile['department']}")
        if profile.get("year"):
            context_parts.append(f"Year: {profile['year']}")
        if profile.get("international_student"):
            context_parts.append("International Student: Yes")
        
        # Courses of interest
        courses = profile.get("courses_of_interest", [])
        if courses:
            context_parts.append(f"Courses of Interest: {', '.join(courses)}")
        
        # Previously asked topics
        topics = profile.get("previously_asked_topics", [])
        if topics:
            recent_topics = topics[-5:]  # Last 5 topics
            context_parts.append(f"Recent Topics: {', '.join(recent_topics)}")
        
        if context_parts:
            return "\n".join(["Student Context:"] + context_parts)
        else:
            return "No student context available."
