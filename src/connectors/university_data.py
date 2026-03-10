"""
Real-Time Data Connector - Simulates fetching from university systems.
In production, this would call actual university database APIs.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "university_systems"


class UniversityDataConnector:
    """Connects to university systems to fetch real-time student data."""
    
    def __init__(self):
        """Initialize connector."""
        self.attendance_file = DATA_DIR / "attendance_system.csv"
        self.grades_file = DATA_DIR / "grades_system.csv"
        self.placement_file = DATA_DIR / "placement_system.csv"
        
        logger.info("University Data Connector initialized")
        logger.info(f"  Attendance: {self.attendance_file.exists()}")
        logger.info(f"  Grades: {self.grades_file.exists()}")
        logger.info(f"  Placement: {self.placement_file.exists()}")
    
    def get_attendance_data(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time attendance from university attendance system.
        
        In production: API call to attendance.university.edu/api/student/{id}
        """
        try:
            if not self.attendance_file.exists():
                logger.warning(f"Attendance file not found: {self.attendance_file}")
                return None
            
            df = pd.read_csv(self.attendance_file)
            student = df[df['student_id'] == int(student_id)]
            
            if student.empty:
                return None
            
            record = student.iloc[0]
            return {
                "attendance_percentage": float(record['attendance_percentage']),
                "total_classes": int(record['total_classes']),
                "attended_classes": int(record['attended_classes']),
                "last_updated": record['last_updated']
            }
        except Exception as e:
            logger.error(f"Failed to fetch attendance for {student_id}: {e}")
            return None
    
    def get_academic_data(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch academic records from university ERP system.
        
        In production: API call to erp.university.edu/api/academics/{id}
        """
        try:
            if not self.grades_file.exists():
                logger.warning(f"Grades file not found: {self.grades_file}")
                return None
            
            df = pd.read_csv(self.grades_file)
            student = df[df['student_id'] == int(student_id)]
            
            if student.empty:
                return None
            
            record = student.iloc[0]
            return {
                "name": record['name'],
                "program": record['program'],
                "department": record['department'],
                "year": int(record['current_year']),
                "semester": int(record['current_semester']),
                "cgpa": float(record['cgpa']),
                "sgpa": float(record['sgpa_current']),
                "total_credits": int(record['total_credits']),
                "last_updated": record['last_updated']
            }
        except Exception as e:
            logger.error(f"Failed to fetch academic data for {student_id}: {e}")
            return None
    
    def get_placement_data(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch placement status from career services system.
        
        In production: API call to placement.university.edu/api/student/{id}
        """
        try:
            if not self.placement_file.exists():
                logger.warning(f"Placement file not found: {self.placement_file}")
                return None
            
            df = pd.read_csv(self.placement_file)
            student = df[df['student_id'] == int(student_id)]
            
            if student.empty:
                return None
            
            record = student.iloc[0]
            return {
                "placement_registered": record['registered_for_placement'] == 'Yes',
                "placement_status": record['placement_status'],
                "resume_uploaded": record['resume_uploaded'] == 'Yes',
                "mock_interviews": int(record['mock_interviews_attended']),
                "companies_applied": int(record['companies_applied']),
                "offers_received": int(record['offers_received']),
                "last_updated": record['last_updated']
            }
        except Exception as e:
            logger.error(f"Failed to fetch placement data for {student_id}: {e}")
            return None
    
    def get_complete_profile(self, student_id: str) -> Dict[str, Any]:
        """
        Fetch complete student profile from all university systems.
        This simulates real-time data aggregation.
        """
        profile = {"student_id": student_id}
        
        # Fetch from attendance system
        attendance = self.get_attendance_data(student_id)
        if attendance:
            profile.update(attendance)
            logger.info(f"Fetched attendance for {student_id}: {attendance['attendance_percentage']}%")
        
        # Fetch from academic system
        academic = self.get_academic_data(student_id)
        if academic:
            profile.update(academic)
            logger.info(f"Fetched academics for {student_id}: CGPA {academic['cgpa']}")
        
        # Fetch from placement system
        placement = self.get_placement_data(student_id)
        if placement:
            profile.update(placement)
            logger.info(f"Fetched placement for {student_id}: {placement['placement_status']}")
        
        return profile


# Singleton instance
_connector = None

def get_university_connector() -> UniversityDataConnector:
    """Get singleton connector instance."""
    global _connector
    if _connector is None:
        _connector = UniversityDataConnector()
    return _connector
