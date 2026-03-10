"""
Document processing pipeline for ingestion.
"""
from typing import List, Optional
from pathlib import Path
import traceback

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader
)

from src.utils.logger import get_logger
from src.utils.exceptions import IngestionError
from src.chunking import SemanticChunker, SemanticChunk
from src.config import settings

logger = get_logger(__name__)


class DocumentProcessor:
    """Processes documents for ingestion into the RAG system."""
    
    def __init__(self, chunker: Optional[SemanticChunker] = None):
        """
        Initialize document processor.
        
        Args:
            chunker: Semantic chunker instance (optional)
        """
        self.chunker = chunker or SemanticChunker()
        
        # File type to loader mapping
        self.loaders = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.txt': TextLoader,
            '.md': UnstructuredMarkdownLoader
        }
    
    def can_process(self, file_path: str) -> bool:
        """
        Check if file can be processed.
        
        Args:
            file_path: Path to file
        
        Returns:
            True if file type is supported
        """
        suffix = Path(file_path).suffix.lower()
        return suffix in self.loaders
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from document.
        
        Args:
            file_path: Path to document
        
        Returns:
            Extracted text
        """
        try:
            suffix = Path(file_path).suffix.lower()
            
            if suffix not in self.loaders:
                raise IngestionError(f"Unsupported file type: {suffix}")
            
            loader_class = self.loaders[suffix]
            loader = loader_class(file_path)
            
            # Load documents
            documents = loader.load()
            
            # Concatenate all page content
            text = "\n\n".join([doc.page_content for doc in documents])
            
            logger.info(f"Extracted {len(text)} characters from {Path(file_path).name}")
            return text
            
        except Exception as e:
            raise IngestionError(f"Failed to extract text from {file_path}: {e}")
    
    def infer_metadata(self, file_path: str, text: str) -> dict:
        """
        Infer document metadata from filename and content.
        
        Args:
            file_path: Path to file
            text: Document text
        
        Returns:
            Metadata dict with category and program_level
        """
        filename = Path(file_path).stem.lower()
        text_lower = text.lower()
        
        # Infer program level
        program_level = "General"
        if any(term in filename or term in text_lower[:1000] for term in ["btech", "b.tech", "bachelor"]):
            program_level = "BTech"
        elif any(term in filename or term in text_lower[:1000] for term in ["mtech", "m.tech", "master"]):
            program_level = "MTech"
        elif any(term in filename or term in text_lower[:1000] for term in ["phd", "ph.d", "doctoral"]):
            program_level = "PhD"
        elif any(term in filename or term in text_lower[:1000] for term in ["mba"]):
            program_level = "MBA"
        
        # Infer category
        category = "general"
        if any(term in filename for term in ["syllabus", "curriculum", "course"]):
            category = "syllabus"
        elif any(term in filename for term in ["hostel", "accommodation", "residence"]):
            category = "hostel"
        elif any(term in filename for term in ["placement", "recruitment", "career"]):
            category = "placement"
        elif any(term in filename for term in ["rule", "regulation", "policy"]):
            category = "rules"
        elif any(term in filename for term in ["safety", "lab", "laboratory"]):
            category = "safety"
        elif any(term in filename for term in ["fee", "tuition", "payment"]):
            category = "fees"
        elif any(term in filename for term in ["calendar", "schedule", "timetable"]):
            category = "calendar"
        elif any(term in filename for term in ["international", "visa", "foreign"]):
            category = "international"
        elif any(term in filename for term in ["handbook", "guide"]):
            category = "handbook"
        
        logger.debug(f"Inferred metadata: program={program_level}, category={category}")
        
        return {
            "program_level": program_level,
            "category": category
        }
    
    def process_document(
        self,
        file_path: str,
        program_level: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[SemanticChunk]:
        """
        Process a document into semantic chunks.
        
        Args:
            file_path: Path to document
            program_level: Program level (optional, will be inferred)
            category: Category (optional, will be inferred)
        
        Returns:
            List of semantic chunks
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Check if file exists
            if not Path(file_path).exists():
                raise IngestionError(f"File not found: {file_path}")
            
            # Extract text
            text = self.extract_text(file_path)
            
            if not text.strip():
                logger.warning(f"No text extracted from {file_path}")
                return []
            
            # Infer metadata if not provided
            if not program_level or not category:
                inferred = self.infer_metadata(file_path, text)
                program_level = program_level or inferred["program_level"]
                category = category or inferred["category"]
            
            # Create chunks
            chunks = self.chunker.chunk_document(
                text=text,
                source_file=Path(file_path).name,
                category=category,
                program_level=program_level
            )
            
            logger.info(
                f"Created {len(chunks)} chunks from {Path(file_path).name} "
                f"({program_level}, {category})"
            )
            
            return chunks
            
        except IngestionError:
            raise
        except Exception as e:
            logger.error(f"Error processing document: {traceback.format_exc()}")
            raise IngestionError(f"Failed to process document: {e}")
    
    def process_multiple(
        self,
        file_paths: List[str]
    ) -> List[SemanticChunk]:
        """
        Process multiple documents.
        
        Args:
            file_paths: List of file paths
        
        Returns:
            Combined list of chunks from all documents
        """
        all_chunks = []
        
        for file_path in file_paths:
            try:
                if self.can_process(file_path):
                    chunks = self.process_document(file_path)
                    all_chunks.extend(chunks)
                else:
                    logger.warning(f"Skipping unsupported file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                # Continue with other files
        
        logger.info(f"Processed {len(file_paths)} files, created {len(all_chunks)} total chunks")
        return all_chunks
