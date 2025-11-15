# dtos/classification_dto.py
"""
Classification-specific DTOs
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from domains.enums import ConfidenceLevel, QualityLevel, RiskLevel


class WorkClassificationDTO(BaseModel):
    """Work classification DTO"""
    is_work: bool
    work_type: Optional[str] = None
    confidence: str
    reasoning: str
    signals: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_work": True,
                "work_type": "email",
                "confidence": "high",
                "reasoning": "Professional email composition",
                "signals": ["formal tone", "business context"]
            }
        }


class TopicClassificationDTO(BaseModel):
    """Topic classification DTO"""
    primary_topic: str
    sub_topics: List[str] = Field(default_factory=list)
    confidence: str
    keywords: List[str] = Field(default_factory=list)


class IntentClassificationDTO(BaseModel):
    """Intent classification DTO"""
    primary_intent: str
    detailed_intent: str
    confidence: str
    used_assistant_response: bool = False


class QualityAnalysisDTO(BaseModel):
    """Quality analysis DTO"""
    overall_score: float = Field(ge=0, le=10)
    quality_level: str
    
    has_clear_role: bool
    has_context: bool
    has_clear_goal: bool
    
    clarity_score: float = Field(ge=0, le=10)
    specificity_score: float = Field(ge=0, le=10)
    completeness_score: float = Field(ge=0, le=10)
    
    needs_clarification: bool
    ambiguity_level: str
    missing_elements: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)


class PIIDetectionDTO(BaseModel):
    """PII detection DTO"""
    has_pii: bool
    pii_types: List[str] = Field(default_factory=list)
    risk_level: str
    entities: List[dict] = Field(default_factory=list)
    redacted_content: Optional[str] = None