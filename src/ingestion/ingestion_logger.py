"""
Structured logging for ingestion events.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.utils.logger import setup_logger
from src.config import settings

# Create specialized logger for ingestion
ingestion_logger = setup_logger(
    "ingestion",
    log_file=str(Path(settings.log_file).parent / "ingestion.log"),
    level=settings.log_level
)


class IngestionLogger:
    """Structured logger for ingestion events."""
    
    @staticmethod
    def log_file_detected(file_path: str):
        """Log file detection event."""
        ingestion_logger.info(f"FILE_DETECTED: {file_path}")
    
    @staticmethod
    def log_processing_started(file_path: str):
        """Log processing start."""
        ingestion_logger.info(f"PROCESSING_STARTED: {file_path}")
    
    @staticmethod
    def log_processing_completed(
        file_path: str,
        chunks_created: int,
        duration_seconds: float
    ):
        """Log successful processing."""
        ingestion_logger.info(
            f"PROCESSING_COMPLETED: {file_path} | "
            f"Chunks: {chunks_created} | "
            f"Duration: {duration_seconds:.2f}s"
        )
    
    @staticmethod
    def log_processing_failed(file_path: str, error: str):
        """Log processing failure."""
        ingestion_logger.error(
            f"PROCESSING_FAILED: {file_path} | Error: {error}"
        )
    
    @staticmethod
    def log_index_update(index_type: str, vectors_added: int):
        """Log index update."""
        ingestion_logger.info(
            f"INDEX_UPDATED: {index_type} | Vectors added: {vectors_added}"
        )
    
    @staticmethod
    def log_cache_invalidated(cache_type: Optional[str] = None):
        """Log cache invalidation."""
        if cache_type:
            ingestion_logger.info(f"CACHE_INVALIDATED: {cache_type}")
        else:
            ingestion_logger.info("CACHE_INVALIDATED: ALL")
    
    @staticmethod
    def log_ingestion_summary(
        files_processed: int,
        files_failed: int,
        total_chunks: int,
        total_duration_seconds: float
    ):
        """Log ingestion batch summary."""
        ingestion_logger.info(
            f"INGESTION_SUMMARY | "
            f"Files processed: {files_processed} | "
            f"Files failed: {files_failed} | "
            f"Total chunks: {total_chunks} | "
            f"Duration: {total_duration_seconds:.2f}s"
        )
