"""
Section-based semantic chunking system.
Processes documents while preserving hierarchy, headings, and metadata.
"""
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import tiktoken

from src.utils.logger import get_logger
from src.utils.exceptions import IngestionError
from src.config import settings

logger = get_logger(__name__)


@dataclass
class SemanticChunk:
    """Represents a semantic chunk with metadata."""
    content: str
    section_title: str
    subsection: Optional[str]
    program_level: str  # BTech / MTech / PhD / General
    category: str  # syllabus / hostel / placement / rules / safety / etc.
    source_file: str
    chunk_index: int = 0
    token_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "content": self.content,
            "section_title": self.section_title,
            "subsection": self.subsection,
            "program_level": self.program_level,
            "category": self.category,
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
            "token_count": self.token_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticChunk':
        """Create from dictionary."""
        return cls(
            content=data["content"],
            section_title=data["section_title"],
            subsection=data.get("subsection"),
            program_level=data["program_level"],
            category=data["category"],
            source_file=data["source_file"],
            chunk_index=data.get("chunk_index", 0),
            token_count=data.get("token_count", 0)
        )


class SemanticChunker:
    """Section-based semantic chunking with hierarchy preservation."""
    
    def __init__(
        self,
        min_size: int = None,
        max_size: int = None,
        overlap: int = None
    ):
        """
        Initialize semantic chunker.
        
        Args:
            min_size: Minimum chunk size in tokens
            max_size: Maximum chunk size in tokens
            overlap: Overlap size in tokens
        """
        self.min_size = min_size or settings.chunk_min_size
        self.max_size = max_size or settings.chunk_max_size
        self.overlap = overlap or settings.chunk_overlap
        
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to load tiktoken, using word count: {e}")
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: approximate with word count
            return len(text.split())
    
    def split_long_content(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> List[SemanticChunk]:
        """
        Split long content into multiple chunks while preserving context.
        
        Args:
            content: Content to split
            metadata: Metadata to attach to chunks
        
        Returns:
            List of semantic chunks
        """
        tokens = self.count_tokens(content)
        
        if tokens <= self.max_size:
            chunk = SemanticChunk(
                content=content,
                section_title=metadata["section_title"],
                subsection=metadata.get("subsection"),
                program_level=metadata["program_level"],
                category=metadata["category"],
                source_file=metadata["source_file"],
                chunk_index=0,
                token_count=tokens
            )
            return [chunk]
        
        # Split into sentences for better chunking
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > self.max_size and current_chunk:
                # Save current chunk
                chunk_content = " ".join(current_chunk)
                chunks.append(SemanticChunk(
                    content=chunk_content,
                    section_title=metadata["section_title"],
                    subsection=metadata.get("subsection"),
                    program_level=metadata["program_level"],
                    category=metadata["category"],
                    source_file=metadata["source_file"],
                    chunk_index=chunk_index,
                    token_count=self.count_tokens(chunk_content)
                ))
                
                # Start new chunk with overlap
                if self.overlap > 0 and len(current_chunk) > 1:
                    # Keep last sentence for overlap
                    current_chunk = current_chunk[-1:]
                    current_tokens = self.count_tokens(current_chunk[0])
                else:
                    current_chunk = []
                    current_tokens = 0
                
                chunk_index += 1
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            chunks.append(SemanticChunk(
                content=chunk_content,
                section_title=metadata["section_title"],
                subsection=metadata.get("subsection"),
                program_level=metadata["program_level"],
                category=metadata["category"],
                source_file=metadata["source_file"],
                chunk_index=chunk_index,
                token_count=self.count_tokens(chunk_content)
            ))
        
        return chunks
    
    def load_existing_chunks(self, file_path: str) -> List[SemanticChunk]:
        """
        Load existing chunks from JSONL file.
        
        Args:
            file_path: Path to JSONL file
        
        Returns:
            List of semantic chunks
        """
        chunks = []
        
        if not Path(file_path).exists():
            logger.warning(f"Chunks file not found: {file_path}")
            return chunks
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        chunks.append(SemanticChunk.from_dict(data))
            
            logger.info(f"Loaded {len(chunks)} existing chunks from {file_path}")
            return chunks
            
        except Exception as e:
            raise IngestionError(f"Failed to load chunks: {e}")
    
    def save_chunks(self, chunks: List[SemanticChunk], file_path: str):
        """
        Save chunks to JSONL file.
        
        Args:
            chunks: List of semantic chunks
            file_path: Output file path
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for chunk in chunks:
                    json.dump(chunk.to_dict(), f, ensure_ascii=False)
                    f.write('\n')
            
            logger.info(f"Saved {len(chunks)} chunks to {file_path}")
            
        except Exception as e:
            raise IngestionError(f"Failed to save chunks: {e}")
    
    def append_chunks(self, new_chunks: List[SemanticChunk], file_path: str):
        """
        Append new chunks to existing JSONL file.
        
        Args:
            new_chunks: New chunks to append
            file_path: Output file path
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'a', encoding='utf-8') as f:
                for chunk in new_chunks:
                    json.dump(chunk.to_dict(), f, ensure_ascii=False)
                    f.write('\n')
            
            logger.info(f"Appended {len(new_chunks)} chunks to {file_path}")
            
        except Exception as e:
            raise IngestionError(f"Failed to append chunks: {e}")
    
    def chunk_document(
        self,
        text: str,
        source_file: str,
        category: str,
        program_level: str = "General"
    ) -> List[SemanticChunk]:
        """
        Chunk a document with section-aware splitting.
        
        Args:
            text: Document text
            source_file: Source file name
            category: Document category
            program_level: Program level (BTech/MTech/PhD/General)
        
        Returns:
            List of semantic chunks
        """
        chunks = []
        
        # Split by major headings (assuming markdown-like format)
        sections = re.split(r'\n(?=#{1,3}\s+)', text)
        
        for section in sections:
            if not section.strip():
                continue
            
            # Extract section title
            title_match = re.match(r'^(#{1,3})\s+(.+?)(?:\n|$)', section)
            if title_match:
                section_title = title_match.group(2).strip()
                content = section[title_match.end():].strip()
            else:
                section_title = "Untitled Section"
                content = section.strip()
            
            # Check for subsections
            subsection_match = re.match(r'^(#{4,6})\s+(.+?)(?:\n|$)', content)
            subsection = subsection_match.group(2).strip() if subsection_match else None
            
            # Create metadata
            metadata = {
                "section_title": section_title,
                "subsection": subsection,
                "program_level": program_level,
                "category": category,
                "source_file": source_file
            }
            
            # Split if content is too long
            section_chunks = self.split_long_content(content, metadata)
            chunks.extend(section_chunks)
        
        logger.info(f"Created {len(chunks)} chunks from {source_file}")
        return chunks
