"""
Input validation guardrails using Presidio for PII detection.
"""
import re
from typing import Optional, Tuple, List
from presidio_analyzer import AnalyzerEngine

from src.utils.logger import get_logger
from src.utils.exceptions import GuardrailViolationError

logger = get_logger(__name__)


class InputGuardrails:
    """Input validation and safety checks using Guardrails AI."""
    
    # Medical content keywords (for semantic validation)
    MEDICAL_KEYWORDS = [
        "medical", "medicine", "disease", "symptom", "diagnosis",
        "treatment", "prescription", "doctor", "health", "surgery",
        "medication", "illness", "therapy", "therapy"
    ]
    
    # Mental health keywords (critical - requires immediate response)
    MENTAL_HEALTH_KEYWORDS = [
        "suicide", "suicidal", "kill myself", "end my life",
        "depression", "anxiety", "self-harm", "self harm", "cutting",
        "mental health crisis", "want to die", "hopeless", "no reason to live"
    ]
    
    # Crisis patterns (more specific)
    CRISIS_PATTERNS = [
        r"\b(kill|hurt|harm)\s+(myself|my\s?self)\b",
        r"\b(suicide|suicidal)\b",
        r"\bno\s+reason\s+to\s+live\b",
        r"\bwant\s+to\s+die\b"
    ]
    
    def __init__(self, toxicity_threshold: float = 0.7):
        """
        Initialize input guardrails.
        
        Args:
            toxicity_threshold: Threshold for toxicity detection (0.0-1.0)
        """
        self.toxicity_threshold = toxicity_threshold
        
        # Initialize Presidio for PII detection
        try:
            self.pii_analyzer = AnalyzerEngine()
            logger.info("Initialized PII detection with Presidio")
        except Exception as e:
            logger.warning(f"Failed to initialize PII analyzer: {e}")
            self.pii_analyzer = None
        
        # Initialize Detoxify for toxicity detection
        try:
            from detoxify import Detoxify
            self.toxicity_model = Detoxify('original')
            logger.info("Initialized ML-based toxicity detection with Detoxify")
        except Exception as e:
            logger.warning(f"Failed to initialize Detoxify: {e}")
            self.toxicity_model = None
    
    def check_toxicity(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check for toxic/harmful content using ML-based detection.
        
        Args:
            query: User query
        
        Returns:
            (is_safe, violation_message)
        """
        # Use ML model if available
        if self.toxicity_model:
            try:
                results = self.toxicity_model.predict(query)
                
                # Check multiple toxic categories
                is_toxic = (
                    results['toxicity'] > self.toxicity_threshold or
                    results['obscene'] > self.toxicity_threshold or
                    results['insult'] > self.toxicity_threshold or
                    results['severe_toxicity'] > 0.5
                )
                
                if is_toxic:
                    logger.warning(f"ML toxicity detected - scores: {results}")
                    return False, "⚠️ Please keep your language professional and respectful."
                
            except Exception as e:
                logger.error(f"Toxicity detection failed: {e}, falling back to keyword check")
                # Fall through to keyword-based check
        
        # Fallback: keyword-based detection (if ML model unavailable)
        harmful_keywords = [
            "hack", "crack", "exploit", "cheat", "steal",
            "illegal", "weapon", "violence", "attack", "bomb"
        ]
        
        query_lower = query.lower()
        
        for keyword in harmful_keywords:
            if keyword in query_lower:
                # Check context - allow educational content
                educational_context = ["course", "learn", "study", "class", 
                                      "security", "ethical", "education"]
                if any(edu in query_lower for edu in educational_context):
                    logger.info(f"Keyword '{keyword}' detected but in educational context")
                    continue
                
                logger.warning(f"Harmful keyword detected: {keyword}")
                return False, f"Query contains potentially harmful content"
        
        return True, None

    
    def check_pii(self, query: str) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Check for Personally Identifiable Information (PII).
        
        Args:
            query: User query
        
        Returns:
            (has_pii, warning_message, detected_entities)
        """
        if not self.pii_analyzer:
            return False, None, None
        
        try:
            # Analyze for PII
            results = self.pii_analyzer.analyze(
                text=query,
                language="en",
                entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", 
                         "US_SSN", "US_PASSPORT", "PERSON", "LOCATION"]
            )
            
            if results:
                detected = [result.entity_type for result in results]
                warning = (
                    f"⚠️ PII Detected: Your query contains {', '.join(set(detected))}. "
                    "Avoid sharing sensitive personal information."
                )
                logger.warning(f"PII detected: {detected}")
                return True, warning, detected
            
            return False, None, None
            
        except Exception as e:
            logger.error(f"PII check failed: {e}")
            return False, None, None
    
    def check_medical_content(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query contains medical content requiring disclaimer.
        
        Args:
            query: User query
        
        Returns:
            (is_medical, disclaimer)
        """
        query_lower = query.lower()
        
        for keyword in self.MEDICAL_KEYWORDS:
            if keyword in query_lower:
                disclaimer = (
                    "⚕️ Medical Disclaimer: I can provide general information, "
                    "but please consult a healthcare professional for medical advice."
                )
                logger.info("Medical content detected, adding disclaimer")
                return True, disclaimer
        
        return False, None
    
    def check_mental_health_crisis(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query indicates mental health crisis requiring immediate resources.
        
        Args:
            query: User query
        
        Returns:
            (is_crisis, referral_message)
        """
        query_lower = query.lower()
        
        # Check crisis patterns first (regex)
        for pattern in self.CRISIS_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return True, self._get_crisis_resources()
        
        # Check keywords
        for keyword in self.MENTAL_HEALTH_KEYWORDS:
            if keyword in query_lower:
                # Distinguish crisis from general mental health
                if any(crisis_word in query_lower for crisis_word in 
                      ["suicide", "kill myself", "want to die", "end my life", "self-harm"]):
                    return True, self._get_crisis_resources()
                else:
                    # General mental health
                    return True, self._get_mental_health_resources()
        
        return False, None
    
    def _get_crisis_resources(self) -> str:
        """Get crisis intervention resources."""
        return (
            "🆘 URGENT: If you're experiencing a mental health crisis, please contact:\n\n"
            "• **988 Suicide & Crisis Lifeline**: Call/Text 988 (24/7)\n"
            "• **Crisis Text Line**: Text HOME to 741741\n"
            "• **Campus Counseling Center**: [Insert contact info]\n"
            "• **Emergency Services**: 911\n\n"
            "You are not alone, and help is available immediately."
        )
    
    def _get_mental_health_resources(self) -> str:
        """Get general mental health resources."""
        return (
            "🧠 Mental Health Support: The university offers counseling services:\n\n"
            "• **Campus Counseling Center**: [Insert hours and contact]\n"
            "• **Student Wellness Programs**: [Insert link]\n"
            "• **Peer Support Groups**: [Insert info]\n\n"
            "Taking care of your mental health is important."
        )
    
    def check_query_length(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query length is within acceptable range.
        
        Args:
            query: User query
        
        Returns:
            (is_valid, error_message)
        """
        query_stripped = query.strip()
        
        if len(query_stripped) < 3:
            return False, "Query is too short. Please provide more details."
        
        if len(query) > 2000:
            return False, "Query is too long. Please keep it under 2000 characters."
        
        return True, None
    
    def validate(self, query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Comprehensive input validation.
        
        Args:
            query: User query
        
        Returns:
            (is_valid, error_message, disclaimer)
        """
        # 1. Check query length
        is_valid, error = self.check_query_length(query)
        if not is_valid:
            return False, error, None
        
        # 2. CRITICAL: Check for mental health crisis FIRST
        is_crisis, crisis_message = self.check_mental_health_crisis(query)
        if is_crisis:
            # Allow query but add urgent resources
            return True, None, crisis_message
        
        # 3. Check toxicity
        is_safe, toxicity_error = self.check_toxicity(query)
        if not is_safe:
            return False, toxicity_error, None
        
        # 4. Check for PII (warn but don't block)
        has_pii, pii_warning, _ = self.check_pii(query)
        if has_pii:
            # Log warning but allow query
            logger.warning(pii_warning)
        
        # 5. Check for medical content
        is_medical, medical_disclaimer = self.check_medical_content(query)
        
        # Priority for disclaimers: crisis > medical > pii
        disclaimer = medical_disclaimer or (pii_warning if has_pii else None)
        
        return True, None, disclaimer
