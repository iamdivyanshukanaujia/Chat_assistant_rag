"""
Health check and monitoring routes.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.models import HealthResponse, CacheMetrics
from src.system import system
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["monitoring"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        System health status
    """
    try:
        # Check component health
        components = {
            "rag_engine": system.rag_engine is not None,
            "vector_store": system.vector_store is not None,
            "bm25_retriever": system.bm25_retriever is not None,
            "cache_manager": system.cache_manager is not None,
            "memory_manager": system.memory_manager is not None,
            "ingestion_manager": system.ingestion_manager is not None
        }
        
        all_healthy = all(components.values())
        
        return HealthResponse(
            status="healthy" if all_healthy else "degraded",
            version="1.0.0",
            components=components
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            components={}
        )


@router.get("/metrics/cache", response_model=CacheMetrics)
async def get_cache_metrics() -> CacheMetrics:
    """
    Get cache statistics.
    
    Returns:
        Cache metrics
    """
    try:
        stats = system.cache_manager.get_stats()
        return CacheMetrics(**stats)
        
    except Exception as e:
        logger.error(f"Get cache metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/retrieval")
async def get_retrieval_metrics() -> Dict[str, Any]:
    """
    Get retrieval performance stats.
    
    Returns:
        Retrieval metrics
    """
    try:
        vector_stats = system.vector_store.get_stats()
        bm25_stats = system.bm25_retriever.get_stats()
        
        return {
            "vector_store": vector_stats,
            "bm25": bm25_stats
        }
        
    except Exception as e:
        logger.error(f"Get retrieval metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
