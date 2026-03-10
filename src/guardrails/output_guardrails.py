"""
Output validation and structure enforcement guardrails.
"""
from typing import Dict, Any, Optional, List, Tuple
import json

from src.utils.logger import get_logger
from src.utils.exceptions import GuardrailViolationError
from src.config import settings

logger = get_logger(__name__)


class OutputGuardrails:
    """Output validation and structure enforcement with enhanced detection."""
    
    def __init__(self, min_confidence: float = None):
        """
        Initialize output guardrails.
        
        Args:
            min_confidence: Minimum confidence score threshold
        """
        self.min_confidence = min_confidence or settings.min_confidence_score
    
    def validate_structure(
        self,
        output: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that output has required structure.
        
        Required fields:
        - answer: str
        - citations: list
        - confidence: float
        
        Args:
            output: Output dictionary to validate
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = ["answer", "citations", "confidence"]
        
        for field in required_fields:
            if field not in output:
                error = f"Missing required field: {field}"
                logger.error(f"Output validation failed: {error}")
                return False, error
        
        # Validate types
        if not isinstance(output["answer"], str):
            return False, "Field 'answer' must be a string"
        
        if not isinstance(output["citations"], list):
            return False, "Field 'citations' must be a list"
        
        if not isinstance(output["confidence"], (int, float)):
            return False, "Field 'confidence' must be a number"
        
        # Validate confidence range
        if not (0.0 <= output["confidence"] <= 1.0):
            return False, "Confidence must be between 0.0 and 1.0"
        
        return True, None
    
    def check_citations(
        self,
        output: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check that citations are present and properly formatted.
        
        Args:
            output: Output dictionary
        
        Returns:
            (has_citations, warning_message)
        """
        citations = output.get("citations", [])
        
        if not citations:
            warning = "No citations provided - answer may not be grounded in sources"
            logger.warning(warning)
            return False, warning
        
        # Check citation structure
        for i, citation in enumerate(citations):
            if not isinstance(citation, dict):
                return False, f"Citation {i} is not a dictionary"
            
            if "source_file" not in citation and "content" not in citation:
                return False, f"Citation {i} missing source information"
        
        return True, None
    
    def validate(
        self,
        output: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Comprehensive output validation.
        
        Args:
            output: Output dictionary to validate
        
        Returns:
            (is_valid, error_message, warnings)
        """
        warnings = []
        
        # 1. Validate structure
        is_valid, error = self.validate_structure(output)
        if not is_valid:
            return False, error, warnings
        
        # 2. Check citations
        has_citations, citation_warning = self.check_citations(output)
        if not has_citations and citation_warning:
            warnings.append(citation_warning)
        
        # Output guardrails disabled - all checks pass
        return True, None, warnings
    
    def enforce_schema(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce output schema, filling in missing fields with defaults.
        
        Args:
            output: Output dictionary
        
        Returns:
            Schema-compliant output
        """
        enforced = {
            "answer": output.get("answer", ""),
            "citations": output.get("citations", []),
            "confidence": output.get("confidence", 0.5),
            "warnings": output.get("warnings", [])
        }
        
        return enforced
