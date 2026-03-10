"""
System initialization module.
Initializes all components with proper dependency injection.
"""
from typing import Optional

from src.utils.logger import setup_logger, get_logger
from src.config import settings
from src.chunking import SemanticChunker
from src.retrieval import FAISSVectorStore, BM25Retriever, HybridRetriever, CrossEncoderReranker
from src.caching import CacheManager
from src.memory import MemoryManager
from src.rag_engine import RAGEngine
from src.ingestion_manager import IngestionManager
# Temporarily disabled for Python 3.14 compatibility
# from src.guardrails import InputGuardrails, OutputGuardrails

# Setup logging
setup_logger("university_assistant", log_file=settings.log_file, level=settings.log_level)
logger = get_logger(__name__)


class SystemInitializer:
    """Initializes and manages all system components."""
    
    def __init__(self):
        """Initialize system components."""
        logger.info("="* 60)
        logger.info("Initializing University Student Information Assistant")
        logger.info("="* 60)
        
        # Core components
        self.chunker: Optional[SemanticChunker] = None
        self.vector_store: Optional[FAISSVectorStore] = None
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.hybrid_retriever: Optional[HybridRetriever] = None
        self.reranker: Optional[CrossEncoderReranker] = None
        
        # Managers
        self.cache_manager: Optional[CacheManager] = None
        self.memory_manager: Optional[MemoryManager] = None
        self.ingestion_manager: Optional[IngestionManager] = None
        
        # Engine
        self.rag_engine: Optional[RAGEngine] = None
        
        # Guardrails
        self.input_guardrails: Optional[InputGuardrails] = None
        self.output_guardrails: Optional[OutputGuardrails] = None
    
    def initialize_all(self, load_initial_data: bool = True):
        """
        Initialize all components in proper order.
        
        Args:
            load_initial_data: Whether to load initial semantic_chunks.jsonl
        """
        try:
            # 1. Initialize chunker
            logger.info("Initializing semantic chunker...")
            self.chunker = SemanticChunker()
            
            # 2. Initialize vector stores and retrievers
            logger.info("Initializing vector stores...")
            self.vector_store = FAISSVectorStore()
            self.bm25_retriever = BM25Retriever()
            
            # 3. Initialize hybrid retriever
            logger.info("Initializing hybrid retriever...")
            self.hybrid_retriever = HybridRetriever(
                vector_store=self.vector_store,
                bm25_retriever=self.bm25_retriever
            )
            
            # 4. Initialize reranker
            logger.info("Initializing cross-encoder reranker...")
            self.reranker = CrossEncoderReranker()
            
            # 5. Initialize cache manager
            logger.info("Initializing cache manager...")
            self.cache_manager = CacheManager()
            
            # 6. Initialize memory manager
            logger.info("Initializing memory manager...")
            self.memory_manager = MemoryManager()
            
            # 6.5 Initialize proactive suggestions
            logger.info("Initializing proactive suggestion system...")
            from src.proactive.data_provider import StudentDataProvider
            from src.proactive.suggestion_engine import ProactiveSuggestionEngine
            
            self.data_provider = StudentDataProvider(self.memory_manager)
            self.suggestion_engine = ProactiveSuggestionEngine(self.data_provider)
            
            # 7. Initialize guardrails (disabled for Python 3.14 compatibility)
            # if settings.enable_input_guardrails:
            #     logger.info("Initializing input guardrails...")
            #     self.input_guardrails = InputGuardrails()
            # 
            # if settings.enable_output_guardrails:
            #     logger.info("Initializing output guardrails...")
            #     self.output_guardrails = OutputGuardrails()
            
            self.input_guardrails = None
            self.output_guardrails = None
            
            # 8. Initialize RAG engine
            logger.info("Initializing RAG engine...")
            self.rag_engine = RAGEngine(
                hybrid_retriever=self.hybrid_retriever,
                reranker=self.reranker,
                cache_manager=self.cache_manager,
                input_guardrails=self.input_guardrails,
                output_guardrails=self.output_guardrails,
                memory_manager=self.memory_manager
            )
            
            # 9. Initialize ingestion manager
            logger.info("Initializing ingestion manager...")
            self.ingestion_manager = IngestionManager(
                chunker=self.chunker,
                vector_store=self.vector_store,
                bm25_retriever=self.bm25_retriever,
                cache_manager=self.cache_manager
            )
            
            # 10. Load initial data
            if load_initial_data:
                logger.info("Loading initial dataset...")
                self.ingestion_manager.ingest_initial_data()
            
            logger.info("="* 60)
            logger.info("System initialization completed successfully!")
            logger.info("="* 60)
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise
    
    def start_file_watching(self):
        """Start automatic file watching for ingestion."""
        if self.ingestion_manager:
            self.ingestion_manager.start_watching()
    
    def stop_file_watching(self):
        """Stop automatic file watching."""
        if self.ingestion_manager:
            self.ingestion_manager.stop_watching()
    
    def shutdown(self):
        """Shutdown all components gracefully."""
        logger.info("Shutting down system...")
        
        # Stop file watcher
        if self.ingestion_manager and self.ingestion_manager.is_watching():
            self.ingestion_manager.stop_watching()
        
        # Save indices
        if self.vector_store:
            self.vector_store.save()
        if self.bm25_retriever:
            self.bm25_retriever.save()
        
        # Save semantic cache
        if self.cache_manager:
            self.cache_manager.save_semantic_cache()
        
        logger.info("System shutdown complete")


# Global system instance
system = SystemInitializer()
