"""
FAISS vector store manager with HuggingFace embeddings.
Handles index persistence, batch embedding, and similarity search.
"""
import os
import pickle
from typing import List, Dict, Any, Tuple
import numpy as np
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

from src.utils.logger import get_logger
from src.utils.exceptions import VectorStoreError
from src.config import settings
from src.chunking import SemanticChunk

logger = get_logger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for semantic search."""
    
    def __init__(
        self,
        index_path: str = None,
        embedding_model: str = None,
        dimension: int = None
    ):
        """
        Initialize FAISS vector store.
        
        Args:
            index_path: Path to save/load FAISS index
            embedding_model: HuggingFace model name for embeddings
            dimension: Embedding dimension
        """
        self.index_path = index_path or settings.faiss_index_path
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.dimension = dimension or settings.embedding_dimension
        
        # Load embedding model
        logger.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Initialize or load FAISS index
        self.index = None
        self.chunks = []
        self.chunk_metadata = []
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create new one."""
        index_file = Path(self.index_path) / "faiss.index"
        metadata_file = Path(self.index_path) / "metadata.pkl"
        
        if index_file.exists() and metadata_file.exists():
            try:
                logger.info("Loading existing FAISS index...")
                self.index = faiss.read_index(str(index_file))
                
                with open(metadata_file, 'rb') as f:
                    data = pickle.load(f)
                    self.chunks = data['chunks']
                    self.chunk_metadata = data['metadata']
                
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
                
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index."""
        logger.info("Creating new FAISS index...")
        # Using L2 distance (can also use METRIC_INNER_PRODUCT for cosine similarity)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = []
        self.chunk_metadata = []
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed texts using SentenceTransformer.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            Numpy array of embeddings
        """
        try:
            embeddings = self.embedding_model.encode(
                texts,
                show_progress_bar=len(texts) > 100,
                convert_to_numpy=True,
                normalize_embeddings=True  # For cosine similarity
            )
            return embeddings
            
        except Exception as e:
            raise VectorStoreError(f"Failed to embed texts: {e}")
    
    def add_chunks(self, chunks: List[SemanticChunk]):
        """
        Add semantic chunks to the vector store.
        
        Args:
            chunks: List of semantic chunks
        """
        if not chunks:
            return
        
        try:
            logger.info(f"Adding {len(chunks)} chunks to FAISS index...")
            
            # Extract texts
            texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.embed_texts(texts)
            
            # Add to FAISS index
            self.index.add(embeddings.astype('float32'))
            
            # Store chunks and metadata
            self.chunks.extend(chunks)
            for chunk in chunks:
                self.chunk_metadata.append(chunk.to_dict())
            
            logger.info(f"FAISS index now contains {self.index.ntotal} vectors")
            
        except Exception as e:
            raise VectorStoreError(f"Failed to add chunks: {e}")
    
    def search(
        self,
        query: str,
        k: int = 10
    ) -> List[Tuple[SemanticChunk, float]]:
        """
        Search for similar chunks.
        
        Args:
            query: Query text
            k: Number of results to return
        
        Returns:
            List of (chunk, distance) tuples
        """
        if self.index.ntotal == 0:
            logger.warning("FAISS index is empty")
            return []
        
        try:
            # Embed query
            query_embedding = self.embed_texts([query])
            
            # Search
            distances, indices = self.index.search(
                query_embedding.astype('float32'),
                min(k, self.index.ntotal)
            )
            
            # Retrieve chunks
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < len(self.chunks):
                    # Convert L2 distance to similarity score (0-1)
                    # Using normalized embeddings, so L2 distance relates to cosine
                    similarity = 1 / (1 + dist)
                    results.append((self.chunks[idx], float(similarity)))
            
            return results
            
        except Exception as e:
            raise VectorStoreError(f"Failed to search: {e}")
    
    def save(self):
        """Save FAISS index and metadata to disk."""
        try:
            # Ensure directory exists
            Path(self.index_path).mkdir(parents=True, exist_ok=True)
            
            index_file = Path(self.index_path) / "faiss.index"
            metadata_file = Path(self.index_path) / "metadata.pkl"
            
            # Save index
            faiss.write_index(self.index, str(index_file))
            
            # Save metadata
            with open(metadata_file, 'wb') as f:
                pickle.dump({
                    'chunks': self.chunks,
                    'metadata': self.chunk_metadata
                }, f)
            
            logger.info(f"Saved FAISS index to {self.index_path}")
            
        except Exception as e:
            raise VectorStoreError(f"Failed to save index: {e}")
    
    def clear(self):
        """Clear the index."""
        self._create_new_index()
        logger.info("Cleared FAISS index")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "model": self.embedding_model_name,
            "index_path": self.index_path
        }
