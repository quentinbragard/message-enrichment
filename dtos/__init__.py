# dtos/__init__.py
from .enrichment_dto import (
    EnrichmentRequestDTO,
    EnrichmentResponseDTO,
    BatchEnrichmentRequestDTO,
    BatchEnrichmentResponseDTO,
    BatchStatusRequestDTO,
    EnrichmentStatsDTO,
    EnrichmentResultDTO
)
from .classification_dto import (
    WorkClassificationDTO,
    TopicClassificationDTO,
    IntentClassificationDTO,
    QualityAnalysisDTO,
    PIIDetectionDTO
)
from .chat_enrichment_dto import (
    ChatEnrichmentRequest,
    ChatEnrichmentResponse,
    PIIDetectRequest,
    PIIDetectResponse,
)

__all__ = [
    # Enrichment DTOs
    "EnrichmentRequestDTO",
    "EnrichmentResponseDTO",
    "BatchEnrichmentRequestDTO",
    "BatchEnrichmentResponseDTO",
    "BatchStatusRequestDTO",
    "EnrichmentStatsDTO",
    "EnrichmentResultDTO",
    # Classification DTOs
    "WorkClassificationDTO",
    "TopicClassificationDTO",
    "IntentClassificationDTO",
    "QualityAnalysisDTO",
    "PIIDetectionDTO",
    # Simple chat enrichment / PII detection
    "ChatEnrichmentRequest",
    "ChatEnrichmentResponse",
    "PIIDetectRequest",
    "PIIDetectResponse",
]
