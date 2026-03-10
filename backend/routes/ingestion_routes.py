"""
Ingestion control routes.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from backend.models import IngestionRequest, IngestionStatus
from src.system import system
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


@router.post("/trigger")
async def trigger_ingestion(request: IngestionRequest) -> Dict[str, Any]:
    """
    Manually trigger ingestion of a file or directory.
    
    Args:
        request: Ingestion request with file_path or directory_path
    
    Returns:
        Ingestion result
    """
    try:
        if request.file_path:
            logger.info(f"Triggering file ingestion: {request.file_path}")
            system.ingestion_manager.ingest_file(request.file_path)
            return {"message": f"File ingestion triggered: {request.file_path}"}
            
        elif request.directory_path:
            logger.info(f"Triggering directory ingestion: {request.directory_path}")
            files_processed = system.ingestion_manager.ingest_directory(request.directory_path)
            return {
                "message": f"Directory ingestion completed",
                "files_processed": files_processed
            }
        else:
            raise HTTPException(status_code=400, detail="Must provide file_path or directory_path")
            
    except Exception as e:
        logger.error(f"Ingestion trigger error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=IngestionStatus)
async def get_status() -> IngestionStatus:
    """
    Get ingestion status.
    
    Returns:
        Ingestion status
    """
    try:
        is_watching = system.ingestion_manager.is_watching()
        
        return IngestionStatus(
            is_watching=is_watching,
            message="File watcher is running" if is_watching else "File watcher is stopped"
        )
        
    except Exception as e:
        logger.error(f"Get status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_logs(lines: int = 50) -> Dict[str, List[str]]:
    """
    Get recent ingestion logs.
    
    Args:
        lines: Number of lines to retrieve
    
    Returns:
        Log lines
    """
    try:
        from pathlib import Path
        import os
        
        log_file = Path(system.settings.log_file).parent / "ingestion.log"
        
        if not log_file.exists():
            return {"logs": ["No ingestion logs found"]}
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        return {"logs": [line.strip() for line in recent_lines]}
        
    except Exception as e:
        logger.error(f"Get logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
