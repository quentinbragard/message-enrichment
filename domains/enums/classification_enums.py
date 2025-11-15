# domains/enums/classification_enums.py
"""
Classification enums
"""
from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WorkType(str, Enum):
    EMAIL = "email"
    REPORT = "report"
    ANALYSIS = "analysis"
    CODING = "coding"
    MEETING = "meeting"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class TopicType(str, Enum):
    WRITING = "writing"
    ANALYSIS = "analysis"
    TECHNICAL = "technical"
    COMMUNICATION = "communication"
    LEARNING = "learning"
    CREATIVE = "creative"
    PERSONAL = "personal"
    OTHER = "other"


class IntentType(str, Enum):
    ASKING = "asking"
    DOING = "doing"
    EXPRESSING = "expressing"


class QualityLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"