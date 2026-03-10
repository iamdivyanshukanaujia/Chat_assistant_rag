"""
Integrated ingestion manager coordinating all ingestion components.
"""
import time
from typing import List, Optional
from pathlib import Path

from src.utils.logger import get_logger
from src.utils.exceptions import IngestionError
from src.chunking import SemanticChunker, SemanticChunk
from src.retrieval import FAISSVectorStore, BM25Retriever
from src.caching import CacheManager
from src.ingestion import DocumentProcessor, FileWatcher, IngestionLogger
from src.config import settings

logger = get_logger(__name__)


class IngestionManager:
    """Manages the complete ingestion pipeline with auto-watching."""
    
    def __init__(
        self,
        chunker: Optional[SemanticChunker] = None,
        vector_store: Optional[FAISSVectorStore] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize ingestion manager.
        
        Args:
            chunker: Semantic chunker instance
            vector_store: FAISS vector store
            bm25_retriever: BM25 retriever
            cache_manager: Cache manager
        """
        self.chunker = chunker or SemanticChunker()
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.cache_manager = cache_manager
        
        self.document_processor = DocumentProcessor(self.chunker)
        self.file_watcher = FileWatcher(
            watch_dir=settings.watch_dir,
            on_new_file=self._handle_new_file
        )
        
        logger.info("Initialized IngestionManager")
    
    def _handle_new_file(self, file_path: str):
        """
        Handle a new file detected by the watcher.
        
        Args:
            file_path: Path to the new file
        """
        try:
            logger.info(f"Processing new file: {file_path}")
            IngestionLogger.log_processing_started(file_path)
            
            start_time = time.time()
            
            # Process document
            chunks = self.document_processor.process_document(file_path)
            
            if not chunks:
                logger.warning(f"No chunks created from {file_path}")
                return
            
            # Update indexes
            self._update_indexes(chunks)
            
            # Append to chunks.file
            self._append_to_chunks_file(chunks)
            
            # Invalidate caches
            if self.cache_manager:
                self.cache_manager.invalidate_rag_cache()
                IngestionLogger.log_cache_invalidated("RAG")
            
            duration = time.time() - start_time
            IngestionLogger.log_processing_completed(file_path, len(chunks), duration)
            
            logger.info(f"Successfully ingested {file_path} with {len(chunks)} chunks")
            
        except Exception as e:
            IngestionLogger.log_processing_failed(file_path, str(e))
            logger.error(f"Failed to process {file_path}: {e}")
    
    def _update_indexes(self, chunks: List[SemanticChunk]):
        """Update FAISS and BM25 indexes."""
        try:
            # Update FAISS
            if self.vector_store:
                self.vector_store.add_chunks(chunks)
                self.vector_store.save()
                IngestionLogger.log_index_update("FAISS", len(chunks))
            
            # Update BM25
            if self.bm25_retriever:
                self.bm25_retriever.add_chunks(chunks)
                self.bm25_retriever.save()
                IngestionLogger.log_index_update("BM25", len(chunks))
                
        except Exception as e:
            raise IngestionError(f"Failed to update indexes: {e}")
    
    def _append_to_chunks_file(self, chunks: List[SemanticChunk]):
        """Append chunks to the semantic_chunks.jsonl file."""
        try:
            self.chunker.append_chunks(chunks, settings.semantic_chunks_file)
        except Exception as e:
            logger.error(f"Failed to append chunks to file: {e}")
    
    def ingest_initial_data(self):
        """Load and ingest the initial semantic_chunks.jsonl file."""
        try:
            logger.info(f"Loading initial data from {settings.semantic_chunks_file}")
            
            if not Path(settings.semantic_chunks_file).exists():
                logger.warning(f"Initial chunks file not found: {settings.semantic_chunks_file}")
                return
            
            # Load existing chunks
            chunks = self.chunker.load_existing_chunks(settings.semantic_chunks_file)
            
            if not chunks:
                logger.warning("No chunks found in initial file")
                return
            
            logger.info(f"Loaded {len(chunks)} chunks from initial file")
            
            # Update indexes
            self._update_indexes(chunks)
            
            logger.info("Initial data ingestion completed")
            
        except Exception as e:
            raise IngestionError(f"Failed to ingest initial data: {e}")
    
    def ingest_file(self, file_path: str) -> int:
        """
        Manually ingest a single file.
        
        Args:
            file_path: Path to file
        
        Returns:
            Number of chunks created
        """
        self._handle_new_file(file_path)
        return 0  # Would need to track and return actual count
    
    def ingest_directory(self, directory_path: str) -> int:
        """
        Ingest all supported files in a directory.
        
        Args:
            directory_path: Path to directory
        
        Returns:
            Number of files processed
        """
        try:
            dir_path = Path(directory_path)
            if not dir_path.exists() or not dir_path.is_dir():
                raise IngestionError(f"Invalid directory: {directory_path}")
            
            # Find all supported files
            supported_extensions = ['.pdf', '.docx', '.txt', '.md', '.json', '.csv']
            files = []
            for ext in supported_extensions:
                files.extend(dir_path.glob(f'*{ext}'))
            
            logger.info(f"Found {len(files)} files to ingest")
            
            files_processed = 0
            files_failed = 0
            total_chunks = 0
            start_time = time.time()
            
            for file_path in files:
                try:
                    self._handle_new_file(str(file_path))
                    files_processed += 1
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    files_failed += 1
            
            duration = time.time() - start_time
            IngestionLogger.log_ingestion_summary(
                files_processed, files_failed, total_chunks, duration
            )
            
            return files_processed
            
        except Exception as e:
            raise IngestionError(f"Failed to ingest directory: {e}")
    
    def start_watching(self):
        """Start the file watcher."""
        logger.info("Starting file watcher...")
        self.file_watcher.start()
    
    def stop_watching(self):
        """Stop the file watcher."""
        logger.info("Stopping file watcher...")
        self.file_watcher.stop()
    
    def is_watching(self) -> bool:
        """Check if file watcher is running."""
        return self.file_watcher.is_running()
