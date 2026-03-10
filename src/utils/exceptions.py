"""
Custom exception classes for better error handling.
"""


class UniversityAssistantError(Exception):
    """Base exception for all custom errors."""
    pass


class ConfigurationError(UniversityAssistantError):
    """Configuration-related errors."""
    pass


class RetrievalError(UniversityAssistantError):
    """Retrieval pipeline errors."""
    pass


class VectorStoreError(UniversityAssistantError):
    """Vector store operation errors."""
    pass


class CacheError(UniversityAssistantError):
    """Caching operation errors."""
    pass


class MemoryError(UniversityAssistantError):
    """Memory management errors."""
    pass


class IngestionError(UniversityAssistantError):
    """Document ingestion errors."""
    pass


class GuardrailViolationError(UniversityAssistantError):
    """Guardrail validation errors."""
    pass


class LLMError(UniversityAssistantError):
    """LLM interaction errors."""
    pass


class RAGError(UniversityAssistantError):
    """RAG pipeline errors."""
    pass


class AgentRoutingError(UniversityAssistantError):
    """Agent routing errors."""
    pass
