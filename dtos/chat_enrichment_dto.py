from pydantic import BaseModel, Field
from typing import Optional, Dict


class ChatEnrichmentRequest(BaseModel):
    """First-turn chat classification request."""
    user_message: str = Field(..., min_length=1, max_length=4000)
    assistant_response: Optional[str] = Field(None, max_length=6000)


class ChatEnrichmentResponse(BaseModel):
    """Classification result."""
    is_work_related: bool
    theme: str
    intent: str
    quality: Optional[Dict] = None
    feedback: Optional[Dict] = None
    raw: Dict


class PIIDetectRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000)


class PIIDetectResponse(BaseModel):
    has_pii: bool
    pii_types: list
    risk_level: str
    entities: list
    redacted_content: Optional[str] = None
    detector: Optional[str] = None
