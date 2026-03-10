"""
Watchdog-based file monitoring for auto-ingestion.
"""
import time
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from src.utils.logger import get_logger
from src.config import settings
from src.ingestion.ingestion_logger import IngestionLogger

logger = get_logger(__name__)


class DocumentFileHandler(FileSystemEventHandler):
    """Handles file system events for document ingestion."""
    
    def __init__(self, on_new_file: Callable[[str], None]):
        """
        Initialize file handler.
        
        Args:
            on_new_file: Callback function for new files
        """
        super().__init__()
        self.on_new_file = on_new_file
        self.supported_extensions = {'.pdf', '.docx', '.txt', '.md', '.json', '.csv'}
        self.processing_files = set()  # Track files currently being processed
    
    def _is_supported_file(self, file_path: str) -> bool:
        """Check if file is supported."""
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def _should_process(self, file_path: str) -> bool:
        """Check if file should be processed."""
        # Check extension
        if not self._is_supported_file(file_path):
            return False
        
        # Check if already processing
        if file_path in self.processing_files:
            return False
        
        # Check if file exists and is readable
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return False
        
        # Check if file is empty
        if path.stat().st_size == 0:
            logger.debug(f"Skipping empty file: {file_path}")
            return False
        
        return True
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        if self._should_process(file_path):
            logger.info(f"New file detected: {file_path}")
            IngestionLogger.log_file_detected(file_path)
            
            # Wait a moment for file to finish writing
            time.sleep(1)
            
            # Mark as processing
            self.processing_files.add(file_path)
            
            try:
                # Trigger ingestion
                self.on_new_file(file_path)
            finally:
                # Remove from processing set
                self.processing_files.discard(file_path)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        if self._should_process(file_path):
            logger.info(f"File modified: {file_path}")
            IngestionLogger.log_file_detected(file_path)
            
            # Wait a moment for file to finish writing
            time.sleep(1)
            
            # Mark as processing
            self.processing_files.add(file_path)
            
            try:
                # Trigger ingestion
                self.on_new_file(file_path)
            finally:
                # Remove from processing set
                self.processing_files.discard(file_path)


class FileWatcher:
    """Watches directory for new documents and triggers ingestion."""
    
    def __init__(
        self,
        watch_dir: str = None,
        on_new_file: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize file watcher.
        
        Args:
            watch_dir: Directory to watch
            on_new_file: Callback for new files
        """
        self.watch_dir = watch_dir or settings.watch_dir
        self.on_new_file = on_new_file
        
        # Ensure directory exists
        Path(self.watch_dir).mkdir(parents=True, exist_ok=True)
        
        self.observer = None
        self.event_handler = None
    
    def set_callback(self, callback: Callable[[str], None]):
        """Set the callback function for new files."""
        self.on_new_file = callback
    
    def start(self):
        """Start watching the directory."""
        if not self.on_new_file:
            raise ValueError("No callback function set for on_new_file")
        
        logger.info(f"Starting file watcher on directory: {self.watch_dir}")
        
        # Create event handler
        self.event_handler = DocumentFileHandler(self.on_new_file)
        
        # Create observer
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            self.watch_dir,
            recursive=False  # Don't watch subdirectories
        )
        
        # Start observer
        self.observer.start()
        logger.info("File watcher started successfully")
    
    def stop(self):
        """Stop watching the directory."""
        if self.observer:
            logger.info("Stopping file watcher...")
            self.observer.stop()
            self.observer.join()
            logger.info("File watcher stopped")
    
    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self.observer is not None and self.observer.is_alive()
