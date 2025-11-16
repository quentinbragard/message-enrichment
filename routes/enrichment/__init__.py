# routes/enrichment/__init__.py
from fastapi import APIRouter

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])

from . import enrich_message, enrich_batch, get_status
# Simple endpoints
from . import enrich_chat_simple, detect_pii
