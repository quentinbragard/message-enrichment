# domains/__init__.py
from .entities import (
    WorkClassification,
    TopicClassification,
    IntentClassification,
    QualityAnalysis,
    PIIDetection,
    EnrichmentResult
)
from .enums import (
    ConfidenceLevel,
    WorkType,
    TopicType,
    IntentType,
    QualityLevel,
    RiskLevel
)

__all__ = [
    "WorkClassification",
    "TopicClassification", 
    "IntentClassification",
    "QualityAnalysis",
    "PIIDetection",
    "EnrichmentResult",
    "ConfidenceLevel",
    "WorkType",
    "TopicType",
    "IntentType",
    "QualityLevel",
    "RiskLevel"
]