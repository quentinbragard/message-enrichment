# domains/entities/enrichment_entities.py
"""
Enrichment domain entities
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
from domains.enums import (
    ConfidenceLevel,
    QualityLevel,
    RiskLevel,
    WorkType,
    TopicType,
    IntentType
)


@dataclass
class WorkClassification:
    """Work vs Non-Work classification"""
    is_work: bool
    work_type: Optional[WorkType]
    confidence: ConfidenceLevel
    reasoning: str
    signals: List[str]


@dataclass
class TopicClassification:
    """Topic classification"""
    primary_topic: TopicType
    sub_topics: List[str]
    confidence: ConfidenceLevel
    keywords: List[str]


@dataclass
class IntentClassification:
    """Intent classification"""
    primary_intent: IntentType
    detailed_intent: str
    confidence: ConfidenceLevel
    used_assistant_response: bool


@dataclass
class QualityAnalysis:
    """Quality analysis of the prompt"""
    overall_score: float  # 0-10
    quality_level: QualityLevel
    
    # Structure elements
    has_clear_role: bool
    has_context: bool
    has_clear_goal: bool
    
    # Quality scores
    clarity_score: float
    specificity_score: float
    completeness_score: float
    
    # Issues
    needs_clarification: bool
    ambiguity_level: str
    missing_elements: List[str]
    
    # Suggestions
    improvement_suggestions: List[str]


@dataclass
class PIIDetection:
    """PII detection results"""
    has_pii: bool
    pii_types: List[str]
    risk_level: RiskLevel
    entities: List[Dict[str, str]]
    redacted_content: Optional[str]


@dataclass
class EnrichmentResult:
    """Complete enrichment result"""
    message_id: str
    user_id: str
    organization_id: str
    enriched_at: datetime
    processing_time_ms: float
    
    # Classifications
    work_classification: WorkClassification
    topic_classification: TopicClassification
    intent_classification: IntentClassification
    
    # Analysis
    quality_analysis: QualityAnalysis
    pii_detection: PIIDetection
    
    # Metadata
    overall_confidence: float
    used_assistant_response: bool
    model_used: str
    cache_hit: bool = False

