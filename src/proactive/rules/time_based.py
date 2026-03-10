"""
Time-based rules for deadlines and calendar events.
"""
from typing import List, Dict, Any
from datetime import datetime
import uuid

from src.proactive.rules.base import BaseRule
from src.proactive.models import Suggestion


class DeadlineRule(BaseRule):
    """Suggests upcoming deadlines."""
    
    def __init__(self):
        super().__init__(priority="high")
    
    def evaluate(self, student_data: Dict[str, Any], current_date: datetime) -> List[Suggestion]:
        """Generate deadline suggestions."""
        suggestions = []
        
        upcoming_deadlines = student_data.get("upcoming_deadlines", [])
        
        for deadline in upcoming_deadlines:
            days_until = deadline.get("days_until", 999)
            event = deadline.get("event", "Unknown")
            deadline_date = deadline.get("date", "")
            
            # Critical if within 3 days
            if days_until <= 3:
                priority = "critical"
                icon = "🚨"
                title = "URGENT Deadline"
            # High if within 7 days
            elif days_until <= 7:
                priority = "high"
                icon = "⚠️"
                title = "Upcoming Deadline"
            # Medium if within 14 days
            elif days_until <= 14:
                priority = "medium"
                icon = "📅"
                title = "Reminder"
            else:
                continue  # Skip deadlines too far out
            
            suggestions.append(Suggestion(
                id=f"deadline_{uuid.uuid4().hex[:8]}",
                type="deadline",
                priority=priority,
                title=title,
                message=f"{event} in {days_until} day{'s' if days_until != 1 else ''}",
                icon=icon,
                action_text="View Calendar",
                expires_at=datetime.fromisoformat(deadline_date) if deadline_date else None
            ))
        
        return suggestions


class PlacementSeasonRule(BaseRule):
    """Alerts about placement activities."""
    
    def evaluate(self, student_data: Dict[str, Any], current_date: datetime) -> List[Suggestion]:
        """Generate placement suggestions."""
        suggestions = []
        
        year = student_data.get("year") or 1
        placement_registered = student_data.get("placement_registered", False)
        
        # Alert final year students about placement
        if year >= 4:
            if current_date.month in [8, 9, 10, 11, 12]:  # Placement season
                if not placement_registered:
                    suggestions.append(Suggestion(
                        id=f"placement_register_{uuid.uuid4().hex[:8]}",
                        type="alert",
                        priority="high",
                        title="Placement Registration",
                        message="💼 Placement season is active! Register to participate in campus drives.",
                        icon="💼",
                        action_text="Register Now",
                        action_url="/placements"
                    ))
                else:
                    # Check upcoming deadlines for placement
                    for deadline in student_data.get("upcoming_deadlines", []):
                        if "placement" in deadline.get("event", "").lower():
                            days = deadline.get("days_until", 999)
                            if days <= 7:
                                suggestions.append(Suggestion(
                                    id=f"placement_deadline_{uuid.uuid4().hex[:8]}",
                                    type="reminder",
                                    priority="high",
                                    title="Placement Update",
                                    message=f"📊 {deadline['event']} in {days} days",
                                    icon="📊"
                                ))
        
        return suggestions
