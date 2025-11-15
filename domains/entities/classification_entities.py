# domains/entities/classification_entities.py
"""
Classification-specific entities
"""
from dataclasses import dataclass
from typing import List, Optional
from domains.enums import ConfidenceLevel, WorkType, TopicType, IntentType


@dataclass
class WorkClassification:
    """Work vs Non-Work classification entity"""
    is_work: bool
    work_type: Optional[WorkType]
    confidence: ConfidenceLevel
    reasoning: str
    signals: List[str]
    
    def to_dict(self) -> dict:
        return {
            "is_work": self.is_work,
            "work_type": self.work_type.value if self.work_type else None,
            "confidence": self.confidence.value,
            "reasoning": self.reasoning,
            "signals": self.signals
        }


@dataclass
class TopicClassification:
    """Topic classification entity"""
    primary_topic: TopicType
    sub_topics: List[str]
    confidence: ConfidenceLevel
    keywords: List[str]
    
    def to_dict(self) -> dict:
        return {
            "primary_topic": self.primary_topic.value,
            "sub_topics": self.sub_topics,
            "confidence": self.confidence.value,
            "keywords": self.keywords
        }


@dataclass
class IntentClassification:
    """Intent classification entity"""
    primary_intent: IntentType
    detailed_intent: str
    confidence: ConfidenceLevel
    used_assistant_response: bool
    
    def to_dict(self) -> dict:
        return {
            "primary_intent": self.primary_intent.value,
            "detailed_intent": self.detailed_intent,
            "confidence": self.confidence.value,
            "used_assistant_response": self.used_assistant_response
        }