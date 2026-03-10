"""
Unified cache manager coordinating traditional and semantic caching.
"""
from typing import Optional, Dict, Any, List

from src.utils.logger import get_logger
from src.caching.traditional_cache import TraditionalCache
from src.caching.semantic_cache import SemanticCache
from src.config import settings

logger = get_logger(__name__)


class CacheManager:
    """Unified cache manager with two-tier caching."""
    
    def __init__(
        self,
        traditional_cache: Optional[TraditionalCache] = None,
        semantic_cache: Optional[SemanticCache] = None
    ):
        """
        Initialize cache manager.
        
        Args:
            traditional_cache: Traditional cache instance (optional)
            semantic_cache: Semantic cache instance (optional)
        """
        self.traditional_cache = traditional_cache or TraditionalCache()
        
        if settings.enable_semantic_cache:
            self.semantic_cache = semantic_cache or SemanticCache()
        else:
            self.semantic_cache = None
        
        logger.info("Initialized CacheManager")
    
    def get_answer(
        self,
        query: str,
        use_semantic: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached answer using two-tier strategy.
        
        Flow:
        1. Check traditional Redis cache
        2. If miss, check semantic cache
        3. Return answer or None
        
        Args:
            query: Query text
            use_semantic: Whether to use semantic cache
        
        Returns:
            Cached answer dict or None
        """
        # 1. Check traditional cache
        cached = self.traditional_cache.get("RAG_CACHE", query)
        if cached:
            logger.info("Traditional cache hit")
            return cached
        
        # 2. Check semantic cache
        if use_semantic and self.semantic_cache and settings.enable_semantic_cache:
            cached = self.semantic_cache.get(query)
            if cached:
                logger.info("Semantic cache hit - skipping RAG pipeline")
                return cached
        
        logger.debug("Cache miss - will execute RAG pipeline")
        return None
    
    def set_answer(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        confidence: float = 1.0,
        store_in_semantic: bool = True
    ):
        """
        Store answer in both caches.
        
        Args:
            query: Query text
            answer: Answer text
            sources: Source chunks
            confidence: Answer confidence score
            store_in_semantic: Whether to store in semantic cache
        """
        answer_data = {
            'answer': answer,
            'sources': sources,
            'confidence': confidence
        }
        
        # Store in traditional cache
        self.traditional_cache.set("RAG_CACHE", query, answer_data)
        
        # Store in semantic cache
        if (store_in_semantic and self.semantic_cache and 
            settings.enable_semantic_cache):
            self.semantic_cache.set(query, answer, sources, confidence)
    
    def invalidate_all(self):
        """Invalidate all caches."""
        logger.info("Invalidating all caches...")
        
        # Invalidate traditional cache
        self.traditional_cache.invalidate()
        
        # Clear semantic cache
        if self.semantic_cache:
            self.semantic_cache.clear()
        
        logger.info("All caches invalidated")
    
    def invalidate_rag_cache(self):
        """Invalidate only RAG-related caches."""
        logger.info("Invalidating RAG cache...")
        self.traditional_cache.invalidate("RAG_CACHE")
        
        if self.semantic_cache:
            self.semantic_cache.clear()
    
    def save_semantic_cache(self):
        """Persist semantic cache to disk."""
        if self.semantic_cache:
            self.semantic_cache.save()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined cache statistics."""
        stats = {
            'traditional': self.traditional_cache.get_stats()
        }
        
        if self.semantic_cache:
            stats['semantic'] = self.semantic_cache.get_stats()
        
        return stats
    
    # Convenience methods for specific cache types
    
    def get_course(self, course_code: str) -> Optional[Dict[str, Any]]:
        """Get cached course information."""
        return self.traditional_cache.get("COURSE_CACHE", course_code)
    
    def set_course(self, course_code: str, course_data: Dict[str, Any]):
        """Cache course information."""
        self.traditional_cache.set("COURSE_CACHE", course_code, course_data)
    
    def get_fee_info(self) -> Optional[Dict[str, Any]]:
        """Get cached fee information."""
        return self.traditional_cache.get("FEE_CACHE", "general")
    
    def set_fee_info(self, fee_data: Dict[str, Any]):
        """Cache fee information."""
        self.traditional_cache.set("FEE_CACHE", "general", fee_data)
    
    def get_timetable(self, date: str) -> Optional[Dict[str, Any]]:
        """Get cached timetable."""
        return self.traditional_cache.get("TIMETABLE_CACHE", date)
    
    def set_timetable(self, date: str, timetable_data: Dict[str, Any]):
        """Cache timetable."""
        self.traditional_cache.set("TIMETABLE_CACHE", date, timetable_data)
