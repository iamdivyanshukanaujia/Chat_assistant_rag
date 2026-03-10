"""
Entity memory for student profiles and tracked entities.
"""
from typing import Dict, Any, Optional, List
import json
import redis

from src.utils.logger import get_logger
from src.utils.exceptions import MemoryError
from src.config import settings

logger = get_logger(__name__)


class EntityMemory:
    """Manages student profile and entity tracking."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize entity memory.
        
        Args:
            redis_client: Redis client instance (optional)
        """
        if redis_client:
            self.redis = redis_client
        else:
            try:
                self.redis = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password if settings.redis_password else None,
                    db=settings.redis_db,
                    decode_responses=True
                )
                # Test connection
                self.redis.ping()
                logger.info("Connected to Redis for entity memory")
            except Exception as e:
                raise MemoryError(f"Failed to connect to Redis: {e}")
        
        self.prefix = f"{settings.memory_redis_prefix}:entity"
    
    def _make_key(self, session_id: str, entity_type: str) -> str:
        """Generate Redis key for entity."""
        return f"{self.prefix}:{session_id}:{entity_type}"
    
    def get_student_profile(self, session_id: str) -> Dict[str, Any]:
        """
        Get student profile for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Student profile dict
        """
        try:
            key = self._make_key(session_id, "profile")
            data = self.redis.get(key)
            
            if data:
                return json.loads(data)
            else:
                # Return empty profile
                return {
                    "name": None,
                    "program": None,  # BTech / MTech / MBA / PhD
                    "department": None,
                    "year": None,
                    "international_student": False,
                    "courses_of_interest": [],
                    "previously_asked_topics": []
                }
                
        except Exception as e:
            logger.error(f"Failed to get student profile: {e}")
            return {}
    
    def update_student_profile(
        self,
        session_id: str,
        profile_data: Dict[str, Any]
    ):
        """
        Update student profile.
        
        Args:
            session_id: Session identifier
            profile_data: Profile data to update
        """
        try:
            # Get existing profile
            current_profile = self.get_student_profile(session_id)
            
            # Merge updates
            current_profile.update(profile_data)
            
            # Save to Redis
            key = self._make_key(session_id, "profile")
            self.redis.set(key, json.dumps(current_profile, ensure_ascii=False))
            
            logger.info(f"Updated student profile for session {session_id}")
            
        except Exception as e:
            raise MemoryError(f"Failed to update student profile: {e}")
    
    def add_topic(self, session_id: str, topic: str):
        """
        Add a topic to previously asked topics.
        
        Args:
            session_id: Session identifier
            topic: Topic to add
        """
        try:
            profile = self.get_student_profile(session_id)
            
            topics = profile.get("previously_asked_topics", [])
            if topic not in topics:
                topics.append(topic)
                # Keep only last 20 topics
                topics = topics[-20:]
                profile["previously_asked_topics"] = topics
                
                self.update_student_profile(session_id, profile)
            
        except Exception as e:
            logger.error(f"Failed to add topic: {e}")
    
    def add_course_of_interest(self, session_id: str, course: str):
        """
        Add a course to courses of interest.
        
        Args:
            session_id: Session identifier
            course: Course to add
        """
        try:
            profile = self.get_student_profile(session_id)
            
            courses = profile.get("courses_of_interest", [])
            if course not in courses:
                courses.append(course)
                profile["courses_of_interest"] = courses
                
                self.update_student_profile(session_id, profile)
            
        except Exception as e:
            logger.error(f"Failed to add course: {e}")
    
    def get_entities(self, session_id: str) -> Dict[str, Any]:
        """
        Get all tracked entities for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dict of all entities
        """
        try:
            entities = {
                "profile": self.get_student_profile(session_id)
            }
            
            # Get custom entities
            pattern = f"{self.prefix}:{session_id}:custom:*"
            cursor = 0
            custom_entities = {}
            
            while True:
                cursor, keys = self.redis.scan(cursor, match=pattern, count=100)
                for key in keys:
                    entity_name = key.split(':')[-1]
                    data = self.redis.get(key)
                    if data:
                        custom_entities[entity_name] = json.loads(data)
                if cursor == 0:
                    break
            
            if custom_entities:
                entities["custom"] = custom_entities
            
            return entities
            
        except Exception as e:
            logger.error(f"Failed to get entities: {e}")
            return {}
    
    def set_custom_entity(
        self,
        session_id: str,
        entity_name: str,
        entity_data: Any
    ):
        """
        Set a custom entity.
        
        Args:
            session_id: Session identifier
            entity_name: Entity name
            entity_data: Entity data
        """
        try:
            key = f"{self.prefix}:{session_id}:custom:{entity_name}"
            self.redis.set(key, json.dumps(entity_data, ensure_ascii=False))
            logger.debug(f"Set custom entity: {entity_name}")
        except Exception as e:
            raise MemoryError(f"Failed to set custom entity: {e}")
    
    def clear_session(self, session_id: str):
        """Clear all entities for a session."""
        try:
            pattern = f"{self.prefix}:{session_id}:*"
            cursor = 0
            keys_to_delete = []
            
            while True:
                cursor, keys = self.redis.scan(cursor, match=pattern, count=100)
                keys_to_delete.extend(keys)
                if cursor == 0:
                    break
            
            if keys_to_delete:
                self.redis.delete(*keys_to_delete)
                logger.info(f"Cleared {len(keys_to_delete)} entities for session {session_id}")
            
        except Exception as e:
            raise MemoryError(f"Failed to clear session entities: {e}")
