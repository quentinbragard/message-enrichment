# routes/health.py
"""
Health check endpoints
"""
from fastapi import APIRouter
from core import redis_client, supabase
from config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Jaydai Enrichment Service",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }
    
    # Check Redis
    try:
        await redis_client.get("health_check")
        health_status["checks"]["redis"] = "ok"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Supabase
    try:
        supabase.table("messages").select("id").limit(1).execute()
        health_status["checks"]["supabase"] = "ok"
    except Exception as e:
        health_status["checks"]["supabase"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    try:
        # Quick checks
        await redis_client.get("ready_check")
        return {"ready": True}
    except Exception:
        return {"ready": False}