"""
Centralized configuration management using Pydantic Settings.
Loads from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os

# Load .env file
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # LLM Provider Selection
    llm_provider: str = Field(default="azure", description="LLM provider: 'azure' or 'ollama'")
    
    # Azure OpenAI Configuration
    azure_openai_api_key: str = Field(default="", description="Azure OpenAI API Key")
    azure_openai_endpoint: str = Field(default="", description="Azure OpenAI Endpoint")
    azure_openai_deployment: str = Field(default="gpt-4o", description="Azure OpenAI Deployment Name")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", description="Azure OpenAI API Version")
    
    # Ollama Configuration
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    ollama_model: str = Field(default="mistral", description="Ollama model name")
    ollama_temperature: float = Field(default=0.7, description="LLM temperature")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: str = Field(default="", description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    
    # FAISS Configuration
    faiss_index_path: str = Field(default="./data/faiss_index", description="FAISS index directory")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model")
    embedding_dimension: int = Field(default=384, description="Embedding dimension")
    
    # Retrieval Configuration (Optimized for Academic Q&A)
    hybrid_retrieval_k: int = Field(default=15, description="Number of candidates for hybrid retrieval (optimized from 10)")
    reranker_top_k: int = Field(default=5, description="Top k after reranking (optimized from 3)")
    bm25_weight: float = Field(default=0.4, description="BM25 weight in hybrid retrieval (optimized from 0.3)")
    faiss_weight: float = Field(default=0.6, description="FAISS weight in hybrid retrieval (optimized from 0.7)")
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L6-v2", description="Reranker model")
    
    # Cache Configuration
    cache_ttl_seconds: int = Field(default=86400, description="Cache TTL (24 hours)")
    semantic_cache_similarity_threshold: float = Field(default=0.85, description="Semantic cache threshold")
    enable_semantic_cache: bool = Field(default=True, description="Enable semantic caching")
    semantic_cache_index_path: str = Field(default="./data/semantic_cache_index", description="Semantic cache index path")
    
    # Memory Configuration
    memory_redis_prefix: str = Field(default="university_assistant", description="Redis key prefix for memory")
    max_conversation_history: int = Field(default=50, description="Max conversation turns to keep")
    
    # Chunking Configuration (Optimized for Academic Content)
    chunk_min_size: int = Field(default=300, description="Minimum chunk size in tokens")
    chunk_max_size: int = Field(default=1000, description="Maximum chunk size in tokens (optimized from 800)")
    chunk_overlap: int = Field(default=100, description="Chunk overlap in tokens (optimized from 50)")
    
    # File Watching
    watch_dir: str = Field(default="./data/source", description="Directory to watch for new files")
    semantic_chunks_file: str = Field(default="./data/semantic_chunks.jsonl", description="Path to semantic chunks file")
    
    # Data Paths
    data_dir: str = Field(default="./data", description="Data directory")
    semantic_chunks_file: str = Field(default="./data/semantic_chunks.jsonl", description="Semantic chunks file")
    watch_dir: str = Field(default="./data", description="Directory to watch for new files")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    enable_cors: bool = Field(default=True, description="Enable CORS")
    allowed_origins: List[str] = Field(
        default=["http://localhost:8501", "http://localhost:3000"],
        description="Allowed CORS origins"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="./logs/app.log", description="Log file path")
    
    # Guardrails
    enable_input_guardrails: bool = Field(default=True, description="Enable input guardrails")
    enable_output_guardrails: bool = Field(default=False, description="Enable output guardrails")  # Disabled - too noisy
    min_confidence_score: float = Field(default=0.4, description="Minimum confidence score")  # Lowered threshold
    
    # Guardrails AI Configuration
    toxicity_threshold: float = Field(default=0.7, description="Toxicity detection threshold (0.0-1.0)")
    enable_pii_detection: bool = Field(default=True, description="Enable PII detection")
    pii_entities: List[str] = Field(
        default=["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN", "PERSON"],
        description="PII entities to detect"
    )
    hallucination_threshold: float = Field(default=0.3, description="Hallucination detection threshold")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def ensure_directories(self):
        """Ensure all required directories exist."""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.faiss_index_path, exist_ok=True)
        os.makedirs(self.semantic_cache_index_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()
