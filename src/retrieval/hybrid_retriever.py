"""
Hybrid retrieval combining BM25 and FAISS with weighted score fusion.
"""
from typing import List, Tuple, Dict
import numpy as np

from src.utils.logger import get_logger
from src.utils.exceptions import RetrievalError
from src.config import settings
from src.chunking import SemanticChunk
from src.retrieval.vector_store import FAISSVectorStore
from src.retrieval.bm25_retriever import BM25Retriever

logger = get_logger(__name__)


class HybridRetriever:
    """Hybrid retrieval combining keyword (BM25) and semantic (FAISS) search."""
    
    def __init__(
        self,
        vector_store: FAISSVectorStore,
        bm25_retriever: BM25Retriever,
        bm25_weight: float = None,
        faiss_weight: float = None
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store: FAISS vector store
            bm25_retriever: BM25 retriever
            bm25_weight: Weight for BM25 scores
            faiss_weight: Weight for FAISS scores
        """
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.bm25_weight = bm25_weight or settings.bm25_weight
        self.faiss_weight = faiss_weight or settings.faiss_weight
        
        # Normalize weights
        total_weight = self.bm25_weight + self.faiss_weight
        self.bm25_weight /= total_weight
        self.faiss_weight /= total_weight
        
        logger.info(
            f"Initialized HybridRetriever with weights: "
            f"BM25={self.bm25_weight:.2f}, FAISS={self.faiss_weight:.2f}"
        )
    
    def normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to 0-1 range using min-max normalization.
        
        Args:
            scores: List of scores
        
        Returns:
            Normalized scores
        """
        if not scores:
            return []
        
        scores_array = np.array(scores)
        min_score = scores_array.min()
        max_score = scores_array.max()
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        normalized = (scores_array - min_score) / (max_score - min_score)
        return normalized.tolist()
    
    def merge_results(
        self,
        bm25_results: List[Tuple[SemanticChunk, float]],
        faiss_results: List[Tuple[SemanticChunk, float]],
        k: int
    ) -> List[Tuple[SemanticChunk, float]]:
        """
        Merge and rank results from BM25 and FAISS using weighted score fusion.
        
        Args:
            bm25_results: BM25 retrieval results
            faiss_results: FAISS retrieval results
            k: Number of top results to return
        
        Returns:
            Merged and ranked results (deduplicated by content)
        """
        # Build a dictionary of chunks with their scores
        # Use content hash for deduplication instead of object id
        chunk_scores: Dict[str, Dict] = {}
        
        # Process BM25 results
        if bm25_results:
            bm25_scores = [score for _, score in bm25_results]
            normalized_bm25 = self.normalize_scores(bm25_scores)
            
            for (chunk, _), norm_score in zip(bm25_results, normalized_bm25):
                # Create unique key from content + source
                chunk_key = f"{chunk.source_file}|{chunk.section_title}|{chunk.content[:100]}"
                
                if chunk_key not in chunk_scores:
                    chunk_scores[chunk_key] = {
                        'chunk': chunk,
                        'bm25_score': 0.0,
                        'faiss_score': 0.0
                    }
                # Take max score if duplicate
                chunk_scores[chunk_key]['bm25_score'] = max(
                    chunk_scores[chunk_key]['bm25_score'],
                    norm_score
                )
        
        # Process FAISS results
        if faiss_results:
            faiss_scores = [score for _, score in faiss_results]
            normalized_faiss = self.normalize_scores(faiss_scores)
            
            for (chunk, _), norm_score in zip(faiss_results, normalized_faiss):
                # Create unique key from content + source
                chunk_key = f"{chunk.source_file}|{chunk.section_title}|{chunk.content[:100]}"
                
                if chunk_key not in chunk_scores:
                    chunk_scores[chunk_key] = {
                        'chunk': chunk,
                        'bm25_score': 0.0,
                        'faiss_score': 0.0
                    }
                # Take max score if duplicate
                chunk_scores[chunk_key]['faiss_score'] = max(
                    chunk_scores[chunk_key]['faiss_score'],
                    norm_score
                )
        
        # Calculate weighted combined scores with document-type boosting
        ranked_chunks = []
        for chunk_data in chunk_scores.values():
            chunk = chunk_data['chunk']
            
            # Base combined score
            combined_score = (
                self.bm25_weight * chunk_data['bm25_score'] +
                self.faiss_weight * chunk_data['faiss_score']
            )
            
            # Boost student_handbook.json for general policy queries
            # This helps handbook content compete with placement-specific content
            if chunk.source_file == 'student_handbook.json' and chunk.category == 'handbook':
                combined_score *= 1.25  # 25% boost for general handbook content
            
            ranked_chunks.append((chunk, combined_score))
        
        # Sort by combined score
        ranked_chunks.sort(key=lambda x: x[1], reverse=True)
        
        return ranked_chunks[:k]
    
    def retrieve(
        self,
        query: str,
        k: int = None
    ) -> List[Tuple[SemanticChunk, float]]:
        """
        Perform hybrid retrieval.
        
        Args:
            query: Query text
            k: Number of results to return
        
        Returns:
            List of (chunk, score) tuples
        """
        k = k or settings.hybrid_retrieval_k
        
        try:
            logger.info(f"Performing hybrid retrieval for query: {query[:100]}...")
            
            # Retrieve from both sources
            # Get more candidates from each to ensure good coverage
            candidate_k = k * 2
            
            bm25_results = self.bm25_retriever.search(query, k=candidate_k)
            faiss_results = self.vector_store.search(query, k=candidate_k)
            
            logger.debug(f"BM25 retrieved {len(bm25_results)} results")
            logger.debug(f"FAISS retrieved {len(faiss_results)} results")
            
            # Merge and rank
            merged_results = self.merge_results(bm25_results, faiss_results, k)
            
            logger.info(f"Hybrid retrieval returned {len(merged_results)} results")
            return merged_results
            
        except Exception as e:
            raise RetrievalError(f"Failed to perform hybrid retrieval: {e}")
