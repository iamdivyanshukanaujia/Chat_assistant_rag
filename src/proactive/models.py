"""
Suggestion data models for proactive suggestions.
"""
from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime


@dataclass
class Suggestion:
    """Represents a single proactive suggestion."""
    
    id: str
    type: Literal["deadline", "attendance", "opportunity", "reminder", "alert", "achievement"]
    priority: Literal["critical", "high", "medium", "low"]
    title: str
    message: str
    icon: str = "💡"  # Default icon
    action_text: Optional[str] = None
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata: dict = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "priority": self.priority,
            "title": self.title,
            "message": self.message,
            "icon": self.icon,
            "action_text": self.action_text,
            "action_url": self.action_url,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata or {}
        }
