"""
Cross-encoder reranker for refining retrieval results.
"""
from typing import List, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from src.utils.logger import get_logger
from src.utils.exceptions import RetrievalError
from src.config import settings
from src.chunking import SemanticChunk

logger = get_logger(__name__)


class CrossEncoderReranker:
    """Cross-encoder reranker using transformers."""
    
    def __init__(self, model_name: str = None):
        """
        Initialize cross-encoder reranker.
        
        Args:
            model_name: HuggingFace model name
        """
        self.model_name = model_name or settings.reranker_model
        
        logger.info(f"Loading cross-encoder model: {self.model_name}")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.eval()
            
            # Use GPU if available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            
            logger.info(f"Reranker model loaded on device: {self.device}")
            
        except Exception as e:
            raise RetrievalError(f"Failed to load reranker model: {e}")
    
    def score_pairs(
        self,
        query: str,
        chunks: List[SemanticChunk]
    ) -> List[float]:
        """
        Score query-chunk pairs using cross-encoder.
        
        Args:
            query: Query text
            chunks: List of semantic chunks
        
        Returns:
            List of relevance scores
        """
        if not chunks:
            return []
        
        try:
            # Prepare pairs
            pairs = [[query, chunk.content] for chunk in chunks]
            
            # Tokenize
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get scores
            with torch.no_grad():
                outputs = self.model(**inputs)
                scores = outputs.logits.squeeze(-1)
            
            # Convert to list
            scores = scores.cpu().numpy().tolist()
            
            # Handle single result case
            if isinstance(scores, float):
                scores = [scores]
            
            return scores
            
        except Exception as e:
            raise RetrievalError(f"Failed to score pairs: {e}")
    
    def rerank(
        self,
        query: str,
        candidates: List[Tuple[SemanticChunk, float]],
        top_k: int = None
    ) -> List[Tuple[SemanticChunk, float]]:
        """
        Rerank candidates using cross-encoder.
        
        Args:
            query: Query text
            candidates: List of (chunk, score) tuples from hybrid retrieval
            top_k: Number of top results to return
        
        Returns:
            Reranked list of (chunk, score) tuples
        """
        top_k = top_k or settings.reranker_top_k
        
        if not candidates:
            logger.warning("No candidates to rerank")
            return []
        
        try:
            logger.info(f"Reranking {len(candidates)} candidates to top {top_k}...")
            
            # Extract chunks
            chunks = [chunk for chunk, _ in candidates]
            
            # Score all pairs
            rerank_scores = self.score_pairs(query, chunks)
            
            # Combine with chunks
            reranked = list(zip(chunks, rerank_scores))
            
            # Sort by reranking score
            reranked.sort(key=lambda x: x[1], reverse=True)
            
            # Return top k
            result = reranked[:top_k]
            
            logger.info(f"Reranking complete, returning top {len(result)} results")
            return result
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}, returning original candidates")
            # Fallback to original ranking if reranking fails
            return candidates[:top_k]
