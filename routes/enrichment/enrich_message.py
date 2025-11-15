# routes/enrichment/enrich_message.py
"""
Message enrichment endpoint
"""
from fastapi import HTTPException, BackgroundTasks
from . import router
from dtos import EnrichmentRequestDTO, EnrichmentResponseDTO
from services import EnrichmentService
from core import pubsub_client
import logging

logger = logging.getLogger(__name__)


@router.post("/enrich", response_model=EnrichmentResponseDTO)
async def enrich_message(
    request: EnrichmentRequestDTO,
    background_tasks: BackgroundTasks
):
    """
    Enrich a single message
    Returns immediately with job ID
    """
    try:
        # Quick validation
        if not request.content or len(request.content) < 10:
            return EnrichmentResponseDTO(
                job_id="skipped",
                status="skipped",
                message_id=request.message_id,
                result={"reason": "Content too short"}
            )
        
        enrichment_service = EnrichmentService()
        
        # For high priority or if pub/sub not available, process synchronously
        if request.priority == "high" or not pubsub_client.publisher:
            result = await enrichment_service.enrich_message(request)
            return result
        
        # For normal/low priority with pub/sub available
        try:
            message = request.dict()
            job_id = await pubsub_client.publish(message)
            
            logger.info(f"Enrichment job {job_id} queued for message {request.message_id}")
            
            return EnrichmentResponseDTO(
                job_id=job_id,
                status="processing",
                message_id=request.message_id
            )
        except Exception as pub_error:
            # If pub/sub fails, process synchronously as fallback
            logger.warning(f"Pub/Sub failed, processing synchronously: {pub_error}")
            result = await enrichment_service.enrich_message(request)
            return result
        
    except Exception as e:
        logger.error(f"Enrichment request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))