from fastapi import HTTPException
from . import router
from dtos import ChatEnrichmentRequest, ChatEnrichmentResponse
from services.simple_classification_service import SimpleClassificationService
import logging

logger = logging.getLogger(__name__)


@router.post("/enrich-chat", response_model=ChatEnrichmentResponse)
async def enrich_chat(request: ChatEnrichmentRequest):
    """First-turn chat classification using gpt-4.1-nano."""
    try:
        service = SimpleClassificationService()
        result = await service.classify(
            user_message=request.user_message,
            assistant_response=request.assistant_response,
        )

        return ChatEnrichmentResponse(
            is_work_related=bool(result.get("is_work_related", False)),
            theme=result.get("theme", "non_work"),
            intent=result.get("intent", "non_work"),
            quality=result.get("quality"),
            feedback=result.get("feedback"),
            raw=result,
        )
    except Exception as e:
        logger.error(f"Simple enrichment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
