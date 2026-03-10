"""
Deadline Extractor - Extract academic deadlines from calendar documents.
"""
import re
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


def extract_deadlines(file_path: str = "data/source/academic_calendar.txt") -> List[Dict]:
    """
    Extract deadlines from academic calendar.
    
    Args:
        file_path: Path to academic calendar file
    
    Returns:
        List of deadline dictionaries with event, date, priority
    """
    deadlines = []
    
    if not Path(file_path).exists():
        logger.warning(f"Calendar file not found: {file_path}")
        return deadlines
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Multiple patterns for different formats in the actual calendar
        patterns = [
            # "Event: DD Month YYYY" (e.g., "Classes begin: 18 July 2025")
            r'([A-Za-z][a-zA-Z\s\-/]+):\s+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
            # "Event opens/closes/begins/ends: DD Month YYYY"
            r'([A-Za-z][a-zA-Z\s]+(?:opens|closes|begins|ends|deadline)):\s+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
            # "Event scheduled between: DD Month – DD Month YYYY"
            r'([A-Za-z][a-zA-Z\s]+):\s+(\d{1,2}\s+[A-Z][a-z]+)\s+–\s+\d{1,2}\s+([A-Z][a-z]+\s+\d{4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            
            for match_groups in matches:
                try:
                    event = match_groups[0].strip()
                    
                    # Handle different date formats
                    if len(match_groups) == 2:
                        # Format: "DD Month YYYY"
                        date_str = match_groups[1].strip()
                    else:
                        # Format with range, use end date
                        date_str = match_groups[2].strip()
                    
                    # Parse date: "18 July 2025"
                    try:
                        date = datetime.strptime(date_str, "%d %B %Y")
                    except ValueError:
                        # Try without leading zero: "1 July 2025"
                        try:
                            date = datetime.strptime(date_str, "%d %b %Y")
                        except ValueError:
                            continue
                    
                    priority = _determine_priority(event)
                    
                    deadlines.append({
                        "event": event,
                        "date": date.isoformat(),
                        "priority": priority,
                        "source": "academic_calendar"
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to parse deadline: {match_groups}, error: {e}")
                    continue
        
        logger.info(f"Extracted {len(deadlines)} deadlines from {file_path}")
        return deadlines
        
    except Exception as e:
        logger.error(f"Failed to extract deadlines: {e}")
        return deadlines


def _determine_priority(event: str) -> str:
    """
    Determine if event is high/medium/low priority.
    
    Args:
        event: Event name
    
    Returns:
        Priority level: "high", "medium", or "low"
    """
    high_priority_keywords = [
        "registration", "exam", "fee", "payment", "deadline", 
        "submission", "application", "enrollment"
    ]
    
    medium_priority_keywords = [
        "holiday", "vacation", "break", "orientation", "ceremony"
    ]
    
    event_lower = event.lower()
    
    for keyword in high_priority_keywords:
        if keyword in event_lower:
            return "high"
    
    for keyword in medium_priority_keywords:
        if keyword in event_lower:
            return "medium"
    
    return "low"


def get_upcoming_deadlines(deadlines: List[Dict], days: int = 30) -> List[Dict]:
    """
    Filter deadlines to only upcoming ones within N days.
    
    Args:
        deadlines: List of all deadlines
        days: Number of days to look ahead
    
    Returns:
        Filtered and sorted list of upcoming deadlines
    """
    today = datetime.now()
    upcoming = []
    
    for deadline in deadlines:
        try:
            deadline_date = datetime.fromisoformat(deadline["date"])
            days_until = (deadline_date - today).days
            
            if 0 <= days_until <= days:
                deadline_copy = deadline.copy()
                deadline_copy["days_until"] = days_until
                upcoming.append(deadline_copy)
        except Exception as e:
            logger.debug(f"Failed to process deadline: {deadline}, error: {e}")
            continue
    
    # Sort by date (soonest first)
    upcoming.sort(key=lambda d: d.get("days_until", 999))
    
    return upcoming
