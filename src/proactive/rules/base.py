"""
Base rule class for all suggestion rules.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

from src.proactive.models import Suggestion


class BaseRule(ABC):
    """Base class for all suggestion rules."""
    
    def __init__(self, priority: str = "medium"):
        """
        Initialize rule.
        
        Args:
            priority: Default priority for suggestions from this rule
        """
        self.priority = priority
    
    @abstractmethod
    def evaluate(self, student_data: Dict[str, Any], current_date: datetime) -> List[Suggestion]:
        """
        Evaluate rule and return suggestions.
        
        Args:
            student_data: Complete student profile from data provider
            current_date: Current datetime
        
        Returns:
            List of suggestions (empty if rule doesn't trigger)
        """
        pass
    
    def should_show(self, suggestion: Suggestion, student_data: Dict) -> bool:
        """
        Check if suggestion should be shown to this student.
        Can be overridden for additional filtering.
        
        Args:
            suggestion: Generated suggestion
            student_data: Student profile
        
        Returns:
            True if suggestion should be shown
        """
        return True
