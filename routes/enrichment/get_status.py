# routes/enrichment/get_status.py
"""
Get enrichment status endpoint
"""
from fastapi import HTTPException
from . import router
from repositories import EnrichmentRepository
import logging

logger = logging.getLogger(__name__)


@router.get("/status/{message_id}")
async def get_enrichment_status(message_id: str):
    """
    Get enrichment status for a message
    """
    try:
        repo = EnrichmentRepository()
        result = await repo.get_by_message_id(message_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Enrichment not found")
        
        return {
            "message_id": message_id,
            "status": "completed",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))