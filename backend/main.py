"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.config import settings
from src.system import system
from src.utils.logger import get_logger
from backend.routes import chat_routes, memory_routes, ingestion_routes, monitoring_routes

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up FastAPI application...")
    
    # Initialize system
    system.initialize_all(load_initial_data=True)
    
    # Initialize suggestion routes with engine (after system is ready)
    from backend.routes import suggestion_routes
    suggestion_routes.init_suggestion_routes(system.suggestion_engine)
    
    # Initialize profile routes with data provider
    from backend.routes import profile_routes
    profile_routes.init_profile_routes(system.data_provider)
    
    # Start file watcher
    system.start_file_watching()
    
    logger.info("FastAPI application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    system.shutdown()
    logger.info("FastAPI application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="University Student Information Assistant API",
    description="RAG-based API for university student queries with hybrid retrieval and semantic caching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
from backend.routes import chat_routes, memory_routes, suggestion_routes
from backend.routes import ingestion_routes, monitoring_routes, profile_routes

app.include_router(chat_routes.router)
app.include_router(memory_routes.router)
app.include_router(suggestion_routes.router)
app.include_router(ingestion_routes.router)
app.include_router(monitoring_routes.router)
app.include_router(profile_routes.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "University Student Information Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
