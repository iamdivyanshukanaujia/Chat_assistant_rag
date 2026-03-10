"""
Conversation memory using RunnableWithMessageHistory.
Stores chat history in Redis.
"""
from typing import List, Dict, Any, Optional
import json
import redis
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.utils.logger import get_logger
from src.utils.exceptions import MemoryError
from src.config import settings

logger = get_logger(__name__)


class RedisChatMessageHistory(BaseChatMessageHistory):
    """Chat message history stored in Redis."""
    
    def __init__(self, session_id: str, redis_client: redis.Redis):
        """
        Initialize Redis chat message history.
        
        Args:
            session_id: Unique session identifier
            redis_client: Redis client instance
        """
        self.session_id = session_id
        self.redis = redis_client
        self.key = f"{settings.memory_redis_prefix}:chat:{session_id}"
        self.max_messages = settings.max_conversation_history * 2  # *2 for user+ai pairs
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve messages from Redis."""
        try:
            data = self.redis.get(self.key)
            if not data:
                return []
            
            messages_data = json.loads(data)
            messages = []
            
            for msg_data in messages_data:
                if msg_data['type'] == 'human':
                    messages.append(HumanMessage(content=msg_data['content']))
                elif msg_data['type'] == 'ai':
                    messages.append(AIMessage(content=msg_data['content']))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve messages: {e}")
            return []
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the history."""
        try:
            # Get existing messages
            current_messages = []
            data = self.redis.get(self.key)
            if data:
                current_messages = json.loads(data)
            
            # Add new message
            msg_type = 'human' if isinstance(message, HumanMessage) else 'ai'
            current_messages.append({
                'type': msg_type,
                'content': message.content
            })
            
            # Trim if exceeds max
            if len(current_messages) > self.max_messages:
                current_messages = current_messages[-self.max_messages:]
            
            # Save to Redis
            self.redis.set(self.key, json.dumps(current_messages, ensure_ascii=False))
            logger.debug(f"Added message to session {self.session_id}")
            
        except Exception as e:
            raise MemoryError(f"Failed to add message: {e}")
    
    def clear(self) -> None:
        """Clear all messages from the history."""
        try:
            self.redis.delete(self.key)
            logger.info(f"Cleared chat history for session {self.session_id}")
        except Exception as e:
            raise MemoryError(f"Failed to clear messages: {e}")


class ConversationMemory:
    """Manages conversation history using Redis."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize conversation memory.
        
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
                logger.info("Connected to Redis for conversation memory")
            except Exception as e:
                raise MemoryError(f"Failed to connect to Redis: {e}")
    
    def get_message_history(self, session_id: str) -> RedisChatMessageHistory:
        """
        Get message history for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Chat message history instance
        """
        return RedisChatMessageHistory(session_id, self.redis)
    
    def get_conversation_summary(self, session_id: str, max_turns: int = 5) -> str:
        """
        Get a summary of recent conversation.
        
        Args:
            session_id: Session identifier
            max_turns: Maximum number of turns to include
        
        Returns:
            Conversation summary
        """
        try:
            history = self.get_message_history(session_id)
            messages = history.messages
            
            if not messages:
                return "No previous conversation."
            
            # Get last N turns (N pairs of user/ai messages)
            recent_messages = messages[-(max_turns * 2):]
            
            summary_lines = []
            for i in range(0, len(recent_messages), 2):
                if i + 1 < len(recent_messages):
                    user_msg = recent_messages[i].content[:100]
                    ai_msg = recent_messages[i + 1].content[:100]
                    summary_lines.append(f"User: {user_msg}...")
                    summary_lines.append(f"Assistant: {ai_msg}...")
            
            return "\n".join(summary_lines)
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return "Error retrieving conversation summary."
    
    def clear_session(self, session_id: str):
        """Clear all data for a session."""
        try:
            history = self.get_message_history(session_id)
            history.clear()
            logger.info(f"Cleared session: {session_id}")
        except Exception as e:
            raise MemoryError(f"Failed to clear session: {e}")
    
    def list_active_sessions(self) -> List[str]:
        """List all active session IDs."""
        try:
            pattern = f"{settings.memory_redis_prefix}:chat:*"
            cursor = 0
            sessions = []
            
            while True:
                cursor, keys = self.redis.scan(cursor, match=pattern, count=100)
                for key in keys:
                    session_id = key.split(':')[-1]
                    sessions.append(session_id)
                if cursor == 0:
                    break
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
