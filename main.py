# main.py
"""
Enrichment Service Main Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import settings
from routes import router as api_router
from core import redis_client, pubsub_client, supabase
from utils.monitoring import setup_monitoring

# Setup logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    # Startup
    logger.info(f"Starting Enrichment Service {settings.APP_VERSION}")
    
    try:
        # Initialize monitoring
        setup_monitoring()
        
        # Test connections
        await redis_client.get("health_check")
        logger.info("✅ Redis connection verified")
        
        # Start background worker if in worker mode
        if settings.SERVICE_MODE == "worker":
            from workers import start_worker
            await start_worker()
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    logger.info(f"✅ Enrichment Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enrichment Service")


# Create FastAPI application
app = FastAPI(
    title="Jaydai Enrichment Service",
    description="Message enrichment with AI classification and analysis",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routes
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)