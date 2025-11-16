from fastapi import HTTPException
from . import router
from dtos import PIIDetectRequest, PIIDetectResponse
from services import PIIService
import logging

logger = logging.getLogger(__name__)


@router.post("/detect-pii", response_model=PIIDetectResponse)
async def detect_pii(request: PIIDetectRequest):
    """Detect PII in a single message using GLiNER + regex."""
    try:
        service = PIIService()
        result = await service.detect(request.content)
        return PIIDetectResponse(**result)
    except Exception as e:
        logger.error(f"PII detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
