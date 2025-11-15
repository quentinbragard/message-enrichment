# routes/enrichment/enrich_batch.py (updated)
"""
Batch enrichment endpoint
"""
from typing import List
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime
from . import router
from dtos import BatchEnrichmentRequestDTO, BatchEnrichmentResponseDTO
from services import EnrichmentService
from core import pubsub_client
import logging

logger = logging.getLogger(__name__)


@router.post("/enrich/batch", response_model=BatchEnrichmentResponseDTO)
async def enrich_batch(
    request: BatchEnrichmentRequestDTO,
    background_tasks: BackgroundTasks
):
    """
    Enrich multiple messages in batch
    
    Features:
    - Batch processing up to 100 messages
    - Parallel or sequential processing
    - Context sharing within conversations
    - Deduplication
    - Webhook notifications
    - Partial results on failure
    """
    try:
        enrichment_service = EnrichmentService()
        
        # For high priority, process immediately
        if request.priority == "high":
            result = await enrichment_service.enrich_batch(request)
            return result
        
        # For normal/low priority, queue for background processing
        background_tasks.add_task(
            enrichment_service.enrich_batch,
            request
        )
        
        # Return immediate response with batch ID
        return BatchEnrichmentResponseDTO(
            batch_id=request.batch_id or f"batch_{hash(str(request.messages))}", 
            status="processing",
            organization_id=request.organization_id,
            total_messages=len(request.messages),
            processed_messages=0,
            successful_messages=0,
            failed_messages=0,
            started_at=datetime.utcnow()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Batch enrichment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/{batch_id}/status", response_model=BatchEnrichmentResponseDTO)
async def get_batch_status(
    batch_id: str,
    include_results: bool = False
):
    """
    Get status of a batch enrichment job
    """
    try:
        enrichment_service = EnrichmentService()
        result = await enrichment_service.get_batch_status(
            batch_id,
            include_results
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {e}")
        raise HTTPException(status_code=500, detail=str(e))