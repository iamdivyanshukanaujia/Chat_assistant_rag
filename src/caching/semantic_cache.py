"""
Semantic caching using embedding similarity.
"""
import json
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from src.utils.logger import get_logger
from src.utils.exceptions import CacheError
from src.config import settings

logger = get_logger(__name__)


class SemanticCache:
    """Embedding-based semantic caching for similar queries."""
    
    def __init__(
        self,
        embedding_model: Optional[SentenceTransformer] = None,
        index_path: str = None,
        similarity_threshold: float = None
    ):
        """
        Initialize semantic cache.
        
        Args:
            embedding_model: SentenceTransformer model (optional)
            index_path: Path to save/load cache index
            similarity_threshold: Minimum similarity for cache hit
        """
        self.index_path = index_path or settings.semantic_cache_index_path
        self.similarity_threshold = similarity_threshold or settings.semantic_cache_similarity_threshold
        
        # Load or create embedding model
        if embedding_model:
            self.embedding_model = embedding_model
        else:
            model_name = settings.embedding_model
            logger.info(f"Loading embedding model for semantic cache: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
        
        self.dimension = settings.embedding_dimension
        
        # Initialize cache storage
        self.queries: List[str] = []
        self.answers: List[Dict[str, Any]] = []
        self.index: Optional[faiss.Index] = None
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing cache or create new one."""
        index_file = Path(self.index_path) / "semantic_cache.index"
        data_file = Path(self.index_path) / "cache_data.json"
        
        if index_file.exists() and data_file.exists():
            try:
                logger.info("Loading existing semantic cache...")
                
                # Load FAISS index
                self.index = faiss.read_index(str(index_file))
                
                # Load data
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.queries = data['queries']
                    self.answers = data['answers']
                
                logger.info(f"Loaded semantic cache with {len(self.queries)} entries")
                
            except Exception as e:
                logger.error(f"Failed to load semantic cache: {e}")
                self._create_new_cache()
        else:
            self._create_new_cache()
    
    def _create_new_cache(self):
        """Create a new semantic cache."""
        logger.info("Creating new semantic cache...")
        self.index = faiss.IndexFlatL2(self.dimension)
        self.queries = []
        self.answers = []
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached answer for semantically similar query.
        
        Args:
            query: Query text
        
        Returns:
            Cached answer dict or None if no similar query found
        """
        if not self.queries or self.index.ntotal == 0:
            logger.debug("Semantic cache is empty")
            return None
        
        try:
            # Embed query
            query_embedding = self.embedding_model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Search for similar queries
            distances, indices = self.index.search(
                query_embedding.astype('float32'),
                k=1
            )
            
            distance = distances[0][0]
            idx = indices[0][0]
            
            # Convert L2 distance to similarity
            similarity = 1 / (1 + distance)
            
            logger.debug(f"Semantic cache similarity: {similarity:.4f} (threshold: {self.similarity_threshold})")
            
            if similarity >= self.similarity_threshold and idx < len(self.answers):
                logger.info(f"Semantic cache hit! Similarity: {similarity:.4f}")
                logger.debug(f"Cached query: {self.queries[idx]}")
                logger.debug(f"Current query: {query}")
                
                return self.answers[idx]
            else:
                logger.debug("Semantic cache miss")
                return None
                
        except Exception as e:
            logger.error(f"Semantic cache get error: {e}")
            return None
    
    def set(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        confidence: float = 1.0
    ):
        """
        Add query-answer pair to semantic cache.
        
        Args:
            query: Query text
            answer: Answer text
            sources: Source chunks used
            confidence: Answer confidence score
        """
        # Skip short queries
        if len(query.split()) < 4:
            logger.debug("Skipping semantic cache for short query")
            return
        
        # Skip low confidence answers
        if confidence < settings.min_confidence_score:
            logger.debug(f"Skipping semantic cache for low confidence ({confidence:.2f})")
            return
        
        try:
            # Embed query
            query_embedding = self.embedding_model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Add to index
            self.index.add(query_embedding.astype('float32'))
            
            # Store data
            self.queries.append(query)
            self.answers.append({
                'answer': answer,
                'sources': sources,
                'confidence': confidence,
                'timestamp': time.time()
            })
            
            logger.debug(f"Added to semantic cache: {query[:100]}...")
            
        except Exception as e:
            logger.error(f"Semantic cache set error: {e}")
    
    def save(self):
        """Save semantic cache to disk."""
        try:
            # Ensure directory exists
            Path(self.index_path).mkdir(parents=True, exist_ok=True)
            
            index_file = Path(self.index_path) / "semantic_cache.index"
            data_file = Path(self.index_path) / "cache_data.json"
            
            # Save FAISS index
            faiss.write_index(self.index, str(index_file))
            
            # Save data
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'queries': self.queries,
                    'answers': self.answers
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved semantic cache with {len(self.queries)} entries")
            
        except Exception as e:
            raise CacheError(f"Failed to save semantic cache: {e}")
    
    def clear(self):
        """Clear the semantic cache."""
        self._create_new_cache()
        logger.info("Cleared semantic cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get semantic cache statistics."""
        return {
            "total_entries": len(self.queries),
            "similarity_threshold": self.similarity_threshold,
            "index_path": self.index_path
        }
