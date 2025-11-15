# domains/entities/__init__.py
from .classification_entities import (
    WorkClassification,
    TopicClassification,
    IntentClassification
)
from .enrichment_entities import (
    QualityAnalysis,
    PIIDetection,
    EnrichmentResult
)

__all__ = [
    "WorkClassification",
    "TopicClassification",
    "IntentClassification",
    "QualityAnalysis",
    "PIIDetection",
    "EnrichmentResult"
]