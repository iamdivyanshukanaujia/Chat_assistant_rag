"""
BM25 keyword-based retriever.
Uses rank-bm25 library for keyword recall.
"""
import pickle
from typing import List, Tuple
from pathlib import Path

from rank_bm25 import BM25Okapi

from src.utils.logger import get_logger
from src.utils.exceptions import RetrievalError
from src.config import settings
from src.chunking import SemanticChunk

logger = get_logger(__name__)


class BM25Retriever:
    """BM25-based keyword retriever."""
    
    def __init__(self, index_path: str = None):
        """
        Initialize BM25 retriever.
        
        Args:
            index_path: Path to save/load BM25 index
        """
        self.index_path = index_path or settings.faiss_index_path
        self.bm25 = None
        self.chunks = []
        self.tokenized_corpus = []
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create new one."""
        index_file = Path(self.index_path) / "bm25.pkl"
        
        if index_file.exists():
            try:
                logger.info("Loading existing BM25 index...")
                with open(index_file, 'rb') as f:
                    data = pickle.load(f)
                    self.bm25 = data['bm25']
                    self.chunks = data['chunks']
                    self.tokenized_corpus = data['tokenized_corpus']
                
                logger.info(f"Loaded BM25 index with {len(self.chunks)} documents")
                
            except Exception as e:
                logger.error(f"Failed to load BM25 index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new BM25 index."""
        logger.info("Creating new BM25 index...")
        self.bm25 = None
        self.chunks = []
        self.tokenized_corpus = []
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.
        Simple whitespace + lowercase tokenization.
        
        Args:
            text: Text to tokenize
        
        Returns:
            List of tokens
        """
        # Simple tokenization (can be improved with NLTK or spaCy)
        return text.lower().split()
    
    def add_chunks(self, chunks: List[SemanticChunk]):
        """
        Add semantic chunks to BM25 index.
        
        Args:
            chunks: List of semantic chunks
        """
        if not chunks:
            return
        
        try:
            logger.info(f"Adding {len(chunks)} chunks to BM25 index...")
            
            # Tokenize all chunks
            for chunk in chunks:
                tokens = self.tokenize(chunk.content)
                self.tokenized_corpus.append(tokens)
                self.chunks.append(chunk)
            
            # Re-create BM25 index
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            
            logger.info(f"BM25 index now contains {len(self.chunks)} documents")
            
        except Exception as e:
            raise RetrievalError(f"Failed to add chunks to BM25: {e}")
    
    def search(
        self,
        query: str,
        k: int = 10
    ) -> List[Tuple[SemanticChunk, float]]:
        """
        Search for relevant chunks using BM25.
        
        Args:
            query: Query text
            k: Number of results to return
        
        Returns:
            List of (chunk, score) tuples
        """
        if not self.bm25 or not self.chunks:
            logger.warning("BM25 index is empty")
            return []
        
        try:
            # Tokenize query
            query_tokens = self.tokenize(query)
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top k indices
            top_k = min(k, len(self.chunks))
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:top_k]
            
            # Return chunks with scores
            results = []
            for idx in top_indices:
                results.append((self.chunks[idx], float(scores[idx])))
            
            return results
            
        except Exception as e:
            raise RetrievalError(f"Failed to search with BM25: {e}")
    
    def save(self):
        """Save BM25 index to disk."""
        try:
            # Ensure directory exists
            Path(self.index_path).mkdir(parents=True, exist_ok=True)
            
            index_file = Path(self.index_path) / "bm25.pkl"
            
            with open(index_file, 'wb') as f:
                pickle.dump({
                    'bm25': self.bm25,
                    'chunks': self.chunks,
                    'tokenized_corpus': self.tokenized_corpus
                }, f)
            
            logger.info(f"Saved BM25 index to {self.index_path}")
            
        except Exception as e:
            raise RetrievalError(f"Failed to save BM25 index: {e}")
    
    def clear(self):
        """Clear the index."""
        self._create_new_index()
        logger.info("Cleared BM25 index")
    
    def get_stats(self) -> dict:
        """Get BM25 index statistics."""
        return {
            "total_documents": len(self.chunks),
            "index_path": self.index_path
        }
