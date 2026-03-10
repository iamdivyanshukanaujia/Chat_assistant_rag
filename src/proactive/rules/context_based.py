"""
Context-based rules for student-specific conditions.
"""
from typing import List, Dict, Any
from datetime import datetime
import uuid

from src.proactive.rules.base import BaseRule
from src.proactive.models import Suggestion


class AttendanceRule(BaseRule):
    """Alerts for low attendance."""
    
    def evaluate(self, student_data: Dict[str, Any], current_date: datetime) -> List[Suggestion]:
        """Generate attendance suggestions."""
        suggestions = []
        
        attendance = student_data.get("attendance_percentage", 100)
        min_attendance = student_data.get("min_attendance", 75)
        
        if attendance < min_attendance:
            # Critical alert
            suggestions.append(Suggestion(
                id=f"attendance_critical_{uuid.uuid4().hex[:8]}",
                type="alert",
                priority="critical",
                title="Attendance Alert",
                message=f"🚨 Your attendance is {attendance}% (minimum: {min_attendance}%). You may not be eligible for exams!",
                icon="🚨",
                action_text="View Attendance",
                metadata={"current_attendance": attendance, "required": min_attendance}
            ))
        
        elif attendance < min_attendance + 5:
            # Warning
            suggestions.append(Suggestion(
                id=f"attendance_warning_{uuid.uuid4().hex[:8]}",
                type="alert",
                priority="high",
                title="Attendance Warning",
                message=f"⚠️ Your attendance is {attendance}% - close to minimum {min_attendance}%. Don't skip classes!",
                icon="⚠️",
                metadata={"current_attendance": attendance}
            ))
        
        return suggestions


class ScholarshipEligibilityRule(BaseRule):
    """Alerts about scholarship eligibility."""
    
    def evaluate(self, student_data: Dict[str, Any], current_date: datetime) -> List[Suggestion]:
        """Generate scholarship suggestions."""
        suggestions = []
        
        cgpa = student_data.get("cgpa", 0.0)
        scholarship_eligible = student_data.get("scholarship_eligible", False)
        scholarship_criteria = student_data.get("scholarship_criteria", {})
        
        # Merit scholarship
        if scholarship_eligible and cgpa >= 8.0:
            merit_info = scholarship_criteria.get("merit_scholarship", {})
            amount = merit_info.get("amount", 25000)
            
            # Check if it's application season (July-August)
            if current_date.month in [7, 8]:
                suggestions.append(Suggestion(
                    id=f"scholarship_merit_{uuid.uuid4().hex[:8]}",
                    type="opportunity",
                    priority="high",
                    title="Scholarship Opportunity",
                    message=f"💰 You're eligible for Merit Scholarship (₹{amount:,})! Your CGPA ({cgpa:.1f}) qualifies you. Apply before Aug 15.",
                    icon="💰",
                    action_text="Apply Now",
                    action_url="/scholarships/merit"
                ))
        
        return suggestions


class CGPAPerformanceRule(BaseRule):
    """Recognition for good performance."""
    
    def evaluate(self, student_data: Dict[str, Any], current_date: datetime) -> List[Suggestion]:
        """Generate performance-based suggestions."""
        suggestions = []
        
        cgpa = student_data.get("cgpa", 0.0)
        dean_list_cgpa = student_data.get("dean_list_cgpa", 8.5)
        
        # Dean's List recognition
        if cgpa >= dean_list_cgpa:
            suggestions.append(Suggestion(
                id=f"deans_list_{uuid.uuid4().hex[:8]}",
                type="achievement",
                priority="medium",
                title="Congratulations!",
                message=f"⭐ Your CGPA ({cgpa:.1f}) qualifies you for Dean's List! Keep up the excellent work.",
                icon="⭐",
                metadata={"cgpa": cgpa}
            ))
        
        return suggestions


class PlacementEligibilityRule(BaseRule):
    """Alerts about placement eligibility."""
    
    def evaluate(self, student_data: Dict[str, Any], current_date: datetime) -> List[Suggestion]:
        """Generate placement eligibility suggestions."""
        suggestions = []
        
        year = student_data.get("year") or 1
        
        # Only for final year students during placement season
        if year >= 4 and current_date.month in [8, 9]:
            cgpa = student_data.get("cgpa", 0.0)
            attendance = student_data.get("attendance_percentage", 0)
            min_cgpa = student_data.get("min_cgpa_placement", 6.0)
            min_attendance = student_data.get("min_attendance", 75)
            
            eligible = cgpa >= min_cgpa and attendance >= min_attendance
            
            if not eligible:
                missing = []
                if cgpa < min_cgpa:
                    missing.append(f"CGPA {cgpa:.1f} < {min_cgpa}")
                if attendance < min_attendance:
                    missing.append(f"Attendance {attendance}% < {min_attendance}%")
                
                suggestions.append(Suggestion(
                    id=f"placement_ineligible_{uuid.uuid4().hex[:8]}",
                    type="alert",
                    priority="critical",
                    title="Placement Eligibility Issue",
                    message=f"⚠️ You're currently not eligible for placements. Missing: {', '.join(missing)}",
                    icon="⚠️",
                    metadata={"missing": missing}
                ))
            else:
                suggestions.append(Suggestion(
                    id=f"placement_eligible_{uuid.uuid4().hex[:8]}",
                    type="achievement",
                    priority="medium",
                    title="Placement Eligible",
                    message=f"✅ You meet all placement criteria (CGPA: {cgpa:.1f}, Attendance: {attendance}%). Good luck!",
                    icon="✅",
                    metadata={"cgpa": cgpa, "attendance": attendance}
                ))
        
        return suggestions
