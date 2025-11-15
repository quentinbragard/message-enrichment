# routes/__init__.py
from fastapi import APIRouter
from .enrichment import router as enrichment_router
from .health import router as health_router

router = APIRouter()

router.include_router(enrichment_router)
router.include_router(health_router)

__all__ = ["router"]