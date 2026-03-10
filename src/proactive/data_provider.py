"""
Student Data Provider - Unified data source for proactive suggestions.
Combines entity memory, document extraction, and reasonable defaults.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

from src.memory.memory_manager import MemoryManager
from src.proactive.extractors.deadline_extractor import extract_deadlines, get_upcoming_deadlines
from src.proactive.extractors.fee_extractor import extract_fee_structure
from src.proactive.extractors.criteria_extractor import extract_academic_criteria, extract_scholarship_criteria
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StudentDataProvider:
    """Provides complete student data from multiple sources."""
    
    def __init__(self, memory_manager: MemoryManager):
        """Initialize data provider."""
        self.memory_manager = memory_manager
        
        # Cache extracted data (read once at startup)
        logger.info("Extracting data from source documents...")
        
        self.all_deadlines = self._safe_extract(extract_deadlines, [])
        self.fee_structure = self._safe_extract(extract_fee_structure, {})
        self.academic_criteria = self._safe_extract(extract_academic_criteria, {})
        self.scholarship_criteria = self._safe_extract(extract_scholarship_criteria, {})
        
        logger.info(f"Data provider initialized:")
        logger.info(f"  - {len(self.all_deadlines)} deadlines")
        logger.info(f"  - {len(self.fee_structure)} fee programs")
        logger.info(f"  - {len(self.academic_criteria)} academic criteria")
    
    def _safe_extract(self, extractor_func, default):
        """Safely call extractor, return default on error."""
        try:
            return extractor_func()
        except Exception as e:
            logger.warning(f"Extractor {extractor_func.__name__} failed: {e}")
            return default
    
    def get_student_data(self, student_id: str) -> Dict[str, Any]:
        """
        Get complete student data from all sources.
        
        Priority:
        1. Real-time university systems (CSV files)
        2. Entity memory (fallback)
        3. Defaults (for demo/testing)
        """
        # NEW: Fetch from university systems (CSV files)
        from src.connectors.university_data import get_university_connector
        
        connector = get_university_connector()
        profile = connector.get_complete_profile(student_id)
        
        # Fallback to entity memory if no CSV data
        if not profile or "name" not in profile:
            logger.info(f"No CSV data for {student_id}, falling back to entity memory")
            session_id = hashlib.md5(student_id.lower().encode()).hexdigest()
            profile = self.memory_manager.get_student_profile(session_id)
            profile["student_id"] = student_id
        else:
            logger.info(f"Using real-time CSV data for {student_id}")
        
        # Add upcoming deadlines
        profile["upcoming_deadlines"] = self.get_upcoming_deadlines(days=30)
        
        # Add academic criteria
        profile.update(self.academic_criteria)
        
        # Add fee info for this program
        program = profile.get("program", "BTech")
        profile["fees"] = self.fee_structure.get(program, {})
        
        # Add scholarship info
        profile["scholarship_criteria"] = self.scholarship_criteria
        
        # Fill missing fields with defaults (for demo)
        self._apply_defaults(profile, student_id)
        
        return profile
    
    def _apply_defaults(self, profile: Dict, student_id: str):
        """Fill missing fields with reasonable defaults."""
        # CGPA (if not in memory)
        if "cgpa" not in profile:
            hash_val = int(hashlib.md5(f"{student_id}_cgpa".encode()).hexdigest()[:8], 16)
            profile["cgpa"] = 6.0 + (hash_val % 35) / 10.0
        
        # Attendance (if not in memory)
        if "attendance_percentage" not in profile:
            hash_val = int(hashlib.md5(student_id.encode()).hexdigest()[:8], 16)
            profile["attendance_percentage"] = 75 + (hash_val % 20)
        
        # Completed courses (if not tracked)
        if "completed_courses" not in profile:
            year = profile.get("year") or 1
            courses = []
            if year >= 2:
                courses = ["CS100", "CS101", "MATH101"]
            if year >= 3:
                courses.extend(["CS200", "CS210"])
            if year >= 4:
                courses.extend(["CS300", "CS310"])
            profile["completed_courses"] = courses
        
        # Scholarship status
        if "scholarship_eligible" not in profile:
            cgpa = profile.get("cgpa", 0)
            profile["scholarship_eligible"] = cgpa >= 8.0
        
        # Placement registration
        if "placement_registered" not in profile:
            year = profile.get("year") or 1
            profile["placement_registered"] = False if year >= 4 else None
    
    def get_upcoming_deadlines(self, days: int = 30) -> List[Dict]:
        """Get deadlines within next N days."""
        return get_upcoming_deadlines(self.all_deadlines, days)
    
    def get_scholarship_criteria(self) -> Dict:
        """Get scholarship eligibility criteria."""
        return self.scholarship_criteria
    
    def check_eligibility(self, student_id: str, requirement_type: str) -> Dict:
        """Check if student meets specific requirements."""
        profile = self.get_student_data(student_id)
        
        if requirement_type == "placement":
            min_cgpa = self.academic_criteria.get("min_cgpa_placement", 6.0)
            min_attendance = self.academic_criteria.get("min_attendance", 75)
            
            eligible = (
                profile.get("cgpa", 0) >= min_cgpa and
                profile.get("attendance_percentage", 0) >= min_attendance
            )
            
            missing = []
            if profile.get("cgpa", 0) < min_cgpa:
                missing.append(f"CGPA below {min_cgpa} (current: {profile.get('cgpa', 0):.1f})")
            if profile.get("attendance_percentage", 0) < min_attendance:
                missing.append(f"Attendance below {min_attendance}% (current: {profile.get('attendance_percentage', 0)}%)")
            
            return {
                "eligible": eligible,
                "reason": "All criteria met" if eligible else "Missing requirements",
                "missing": missing
            }
        
        elif requirement_type == "scholarship":
            min_cgpa = 8.0
            cgpa = profile.get("cgpa", 0)
            
            eligible = cgpa >= min_cgpa
            
            return {
                "eligible": eligible,
                "reason": f"CGPA {cgpa:.1f} >= {min_cgpa}" if eligible else f"CGPA {cgpa:.1f} < {min_cgpa}",
                "missing": [] if eligible else [f"Need CGPA >= {min_cgpa}"]
            }
        
        return {"eligible": False, "reason": "Unknown requirement type", "missing": []}
    
    def get_fee_info(self, student_id: str) -> Dict:
        """Get fee information for student's program."""
        profile = self.get_student_data(student_id)
        program = profile.get("program", "BTech")
        
        fees = self.fee_structure.get(program, {})
        
        return {
            "program": program,
            "fees": fees,
            "total": sum(fees.values()),
            "upcoming_deadline": self._get_fee_deadline()
        }
    
    def _get_fee_deadline(self) -> Optional[Dict]:
        """Get next fee payment deadline."""
        today = datetime.now()
        
        for deadline in self.all_deadlines:
            if "fee" in deadline.get("event", "").lower() or "payment" in deadline.get("event", "").lower():
                try:
                    deadline_date = datetime.fromisoformat(deadline["date"])
                    days_until = (deadline_date - today).days
                    
                    if 0 <= days_until <= 60:
                        return {
                            "event": deadline["event"],
                            "date": deadline["date"],
                            "days_until": days_until
                        }
                except:
                    pass
        
        return None
