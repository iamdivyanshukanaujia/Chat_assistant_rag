"""
Fee Extractor - Extract fee information from fee documents.
Simple version that matches actual document structure.
"""
import re
from typing import Dict, List
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


def extract_fee_structure(file_path: str = "data/source/fees.txt") -> Dict[str, Dict]:
    """
    Extract fee amounts for different programs.
    
    Args:
        file_path: Path to fees document
    
    Returns:
        Dictionary of {program: {tuition: amount, hostel: amount, ...}}
    """
    fees = {}
    
    if not Path(file_path).exists():
        logger.warning(f"Fees file not found: {file_path}")
        return fees
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_program = None
        
        for line in lines:
            # Check for program headers like "B.Tech – Computer Science"
            program_match = re.match(r'(B\.?Tech|M\.?Tech|PhD|MBA)', line, re.IGNORECASE)
            if program_match:
                program = program_match.group(1)
                current_program = _normalize_program_name(program)
                if current_program not in fees:
                    fees[current_program] = {}
            
            # Extract tuition fees
            if current_program:
                tuition_match = re.search(r'Tuition\s+fee[:\sa-z]*:\s*₹?([\d,]+)', line, re.IGNORECASE)
                if tuition_match:
                    amount = int(tuition_match.group(1).replace(',', ''))
                    fees[current_program]['tuition'] = amount
                
                # Extract hostel fees
                hostel_match = re.search(r'Hostel\s+fee[:\sa-z]*:\s*₹?([\d,]+)', line, re.IGNORECASE)
                if hostel_match:
                    amount = int(hostel_match.group(1).replace(',', ''))
                    fees[current_program]['hostel'] = amount
                
                # Extract exam fees
                exam_match = re.search(r'Exam\s+fee[:\sa-z]*:\s*₹?([\d,]+)', line, re.IGNORECASE)
                if exam_match:
                    amount = int(exam_match.group(1).replace(',', ''))
                    fees[current_program]['exam'] = amount
        
        logger.info(f"Extracted fees for {len(fees)} programs: {list(fees.keys())}")
        return fees
        
    except Exception as e:
        logger.error(f"Failed to extract fees: {e}", exc_info=True)
        return fees


def _normalize_program_name(program: str) -> str:
    """Normalize program names to standard format."""
    program_lower = program.lower().replace('.', '').replace(' ', '')
    
    if 'btech' in program_lower:
        return "BTech"
    elif 'mtech' in program_lower:
        return "MTech"
    elif 'phd' in program_lower:
        return "PhD"
    elif 'mba' in program_lower:
        return "MBA"
    
    return program.strip()
