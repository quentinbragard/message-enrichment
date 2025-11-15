# domains/enums/quality_enums.py
"""
Quality-related enums
"""
from enum import Enum


class QualityLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    
    @classmethod
    def from_score(cls, score: float) -> 'QualityLevel':
        """Get quality level from numeric score"""
        if score >= 8:
            return cls.EXCELLENT
        elif score >= 6:
            return cls.GOOD
        elif score >= 4:
            return cls.AVERAGE
        else:
            return cls.POOR


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"
    
    @property
    def priority(self) -> int:
        """Get numeric priority for comparison"""
        priorities = {
            self.CRITICAL: 5,
            self.HIGH: 4,
            self.MEDIUM: 3,
            self.LOW: 2,
            self.NONE: 1
        }
        return priorities[self]