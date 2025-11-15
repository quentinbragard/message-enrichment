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
    "PIIDetectionDTO"
]