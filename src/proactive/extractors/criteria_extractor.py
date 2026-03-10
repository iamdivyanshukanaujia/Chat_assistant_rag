"""
Criteria Extractor - Extract academic criteria (CGPA, attendance) from handbooks.
"""
import re
from typing import Dict
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


def extract_academic_criteria(
    handbook_path: str = "data/source/student_handbook.txt",
    placement_path: str = "data/source/placement_guidelines.txt"
) -> Dict[str, any]:
    """
    Extract academic criteria like minimum CGPA, attendance requirements.
    
    Args:
        handbook_path: Path to student handbook
        placement_path: Path to placement guidelines
    
    Returns:
        Dictionary of criteria {min_attendance: 75, min_cgpa_placement: 6.0, ...}
    """
    criteria = {}
    
    # Extract from handbook
    if Path(handbook_path).exists():
        try:
            with open(handbook_path, 'r', encoding='utf-8') as f:
                handbook = f.read()
            
            # Extract attendance requirement
            # Patterns: "minimum 75% attendance", "75% attendance required", "attendance of 75%"
            attendance_patterns = [
                r'(?:minimum|min)\s+(\d{2,3})%?\s+attendance',
                r'(\d{2,3})%\s+attendance\s+(?:required|mandatory)',
                r'attendance\s+of\s+(\d{2,3})%',
            ]
            
            for pattern in attendance_patterns:
                match = re.search(pattern, handbook, re.IGNORECASE)
                if match:
                    criteria['min_attendance'] = int(match.group(1))
                    break
            
            # Extract Dean's List CGPA
            # Pattern: "Dean's List: 8.5 CGPA" or "Dean List - CGPA 8.5"
            deans_patterns = [
                r'Dean[\'s]*\s+List[:\s\-]+(?:CGPA\s+)?(\d\.\d)',
                r'(?:CGPA|GPA)\s+(?:of\s+)?(\d\.\d)\s+for\s+Dean',
            ]
            
            for pattern in deans_patterns:
                match = re.search(pattern, handbook, re.IGNORECASE)
                if match:
                    criteria['dean_list_cgpa'] = float(match.group(1))
                    break
            
            # Extract general passing CGPA
            passing_patterns = [
                r'(?:minimum|min)\s+(?:CGPA|GPA)\s+(?:of\s+)?(\d\.\d)',
                r'passing\s+(?:CGPA|GPA)[:\s]+(\d\.\d)',
            ]
            
            for pattern in passing_patterns:
                match = re.search(pattern, handbook, re.IGNORECASE)
                if match:
                    if 'min_cgpa' not in criteria:  # Don't overwrite if already found
                        criteria['min_cgpa'] = float(match.group(1))
                    break
            
        except Exception as e:
            logger.error(f"Failed to extract from handbook: {e}")
    
    # Extract from placement guidelines
    if Path(placement_path).exists():
        try:
            with open(placement_path, 'r', encoding='utf-8') as f:
                placement = f.read()
            
            # Extract placement eligibility CGPA
            # Patterns: "minimum CGPA of 6.0", "CGPA: 6.0 required"
            placement_cgpa_patterns = [
                r'(?:minimum|min)\s+(?:CGPA|GPA)\s+(?:of\s+)?(\d\.\d)',
                r'(?:CGPA|GPA)[:\s]+(\d\.\d)\s+(?:required|mandatory)',
                r'eligibility[:\s]+(?:CGPA|GPA)\s+(\d\.\d)',
            ]
            
            for pattern in placement_cgpa_patterns:
                match = re.search(pattern, placement, re.IGNORECASE)
                if match:
                    criteria['min_cgpa_placement'] = float(match.group(1))
                    break
            
            # Extract attendance for placement
            for pattern in attendance_patterns:
                match = re.search(pattern, placement, re.IGNORECASE)
                if match and 'min_attendance_placement' not in criteria:
                    criteria['min_attendance_placement'] = int(match.group(1))
                    break
            
        except Exception as e:
            logger.error(f"Failed to extract from placement guide: {e}")
    
    # Apply defaults for missing criteria
    if 'min_attendance' not in criteria:
        criteria['min_attendance'] = 75  # Standard university requirement
        logger.info("Using default min_attendance: 75%")
    
    if 'min_cgpa' not in criteria:
        criteria['min_cgpa'] = 5.0  # Standard passing
        logger.info("Using default min_cgpa: 5.0")
    
    if 'min_cgpa_placement' not in criteria:
        criteria['min_cgpa_placement'] = 6.0  # Standard placement eligibility
        logger.info("Using default min_cgpa_placement: 6.0")
    
    if 'dean_list_cgpa' not in criteria:
        criteria['dean_list_cgpa'] = 8.5  # Standard excellence threshold
        logger.info("Using default dean_list_cgpa: 8.5")
    
    logger.info(f"Extracted academic criteria: {criteria}")
    return criteria


def extract_scholarship_criteria() -> Dict[str, Dict]:
    """
    Extract scholarship eligibility criteria.
    
    Returns:
        Dictionary of scholarship types and their criteria
    """
    # This could be extended to parse from documents
    # For now, returning standard criteria
    return {
        "merit_scholarship": {
            "min_cgpa": 8.0,
            "amount": 25000,
            "description": "For students with CGPA >= 8.0"
        },
        "need_based_scholarship": {
            "income_criteria": "Family income < 5 lakhs/year",
            "amount": 50000,
            "description": "Financial assistance for economically disadvantaged students"
        },
        "research_scholarship": {
            "min_papers": 1,
            "amount": 30000,
            "description": "For students with published research papers"
        }
    }
