"""
Simple entity extraction for student profiles.
Extracts program, department, and topics from queries.
"""
import re
from typing import Dict, Any, List

# Known programs
PROGRAMS = ["btech", "mtech", "mba", "phd", "b.tech", "m.tech", "bachelor", "master", "doctoral"]
PROGRAM_MAP = {
    "btech": "BTech", "b.tech": "BTech", "bachelor": "BTech",
    "mtech": "MTech", "m.tech": "MTech", "master": "MTech",
    "mba": "MBA",
    "phd": "PhD", "doctoral": "PhD"
}

# Common departments
DEPARTMENTS = ["cs", "cse", "computer science", "ee", "ece", "electrical", "me", "mechanical", 
               "ce", "civil", "ch", "chemical", "it", "information technology"]
DEPT_MAP = {
    "cs": "Computer Science", "cse": "Computer Science", "computer science": "Computer Science",
    "ee": "Electrical Engineering", "ece": "Electronics", "electrical": "Electrical Engineering",
    "me": "Mechanical Engineering", "mechanical": "Mechanical Engineering",
    "ce": "Civil Engineering", "civil": "Civil Engineering",
    "ch": "Chemical Engineering", "chemical": "Chemical Engineering",
    "it": "Information Technology", "information technology": "Information Technology"
}

# Topic keywords
TOPIC_KEYWORDS = {
    "hostel": "Hostel & Accommodation",
    "placement": "Placements & Jobs",
    "course": "Courses",
    "fee": "Fees & Finance",
    "library": "Library",
    "exam": "Exams",
    "grade": "Grades & CGPA",
    "cgpa": "Grades & CGPA",
    "scholarship": "Scholarships",
    "international": "International Students",
    "lab": "Labs & Facilities"
}


def extract_entities(query: str, answer: str = "") -> Dict[str, Any]:
    """
    Extract entities from query and answer.
    
    Args:
        query: User query
        answer: Assistant answer (optional)
    
    Returns:
        Dict with extracted entities
    """
    entities = {
        "program": None,
        "department": None,
        "topics": [],
        "is_international": False
    }
    
    text = (query + " " + answer).lower()
    
    # Extract program
    for prog_key, prog_value in PROGRAM_MAP.items():
        if prog_key in text:
            entities["program"] = prog_value
            break
    
    # Extract department
    for dept_key, dept_value in DEPT_MAP.items():
        if dept_key in text:
            entities["department"] = dept_value
            break
    
    # Extract topics
    for keyword, topic in TOPIC_KEYWORDS.items():
        if keyword in text:
            entities["topics"].append(topic)
    
    # Check if international student
    if "international" in text or "foreign" in text:
        entities["is_international"] = True
    
    return entities


def merge_profile(current: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge new entities into current profile.
    
    Args:
        current: Current profile
        new: Newly extracted entities
    
    Returns:
        Merged profile
    """
    merged = current.copy()
    
    # Update program if detected
    if new.get("program") and not merged.get("program"):
        merged["program"] = new["program"]
    
    # Update department if detected
    if new.get("department") and not merged.get("department"):
        merged["department"] = new["department"]
    
    # Add new topics (keep unique)
    current_topics = set(merged.get("previously_asked_topics", []))
    new_topics = set(new.get("topics", []))
    merged["previously_asked_topics"] = list(current_topics | new_topics)[-10:]  # Keep last 10
    
    # Update international status
    if new.get("is_international"):
        merged["international_student"] = True
    
    return merged
