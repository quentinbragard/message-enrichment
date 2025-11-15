# services/pii_service.py
"""
PII detection service
"""
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PIIService:
    """Service for PII detection"""
    
    def __init__(self):
        # Compile regex patterns
        self.patterns = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b(?:\+?[1-9]\d{0,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'),
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        }
        
        # Name patterns (simple heuristic)
        self.name_pattern = re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b')
    
    async def detect(self, content: str) -> Dict:
        """
        Detect PII in content
        """
        try:
            entities = []
            pii_types = []
            
            # Check each pattern
            for pii_type, pattern in self.patterns.items():
                matches = pattern.findall(content)
                if matches:
                    pii_types.append(pii_type)
                    for match in matches:
                        entities.append({
                            "type": pii_type,
                            "value": self._mask_value(match, pii_type),
                            "start": content.find(match),
                            "end": content.find(match) + len(match)
                        })
            
            # Check for potential names
            name_matches = self.name_pattern.findall(content)
            if name_matches:
                # Filter out common non-name matches
                potential_names = self._filter_names(name_matches)
                if potential_names:
                    pii_types.append("person_name")
                    for name in potential_names:
                        entities.append({
                            "type": "person_name",
                            "value": self._mask_value(name, "name"),
                            "start": content.find(name),
                            "end": content.find(name) + len(name)
                        })
            
            # Determine risk level
            risk_level = self._calculate_risk_level(pii_types)
            
            # Redact content if PII found
            redacted_content = None
            if entities:
                redacted_content = self._redact_content(content, entities)
            
            return {
                "has_pii": len(entities) > 0,
                "pii_types": pii_types,
                "risk_level": risk_level,
                "entities": entities,
                "redacted_content": redacted_content
            }
            
        except Exception as e:
            logger.error(f"PII detection failed: {e}")
            return {
                "has_pii": False,
                "pii_types": [],
                "risk_level": "none",
                "entities": [],
                "redacted_content": None
            }
    
    def _mask_value(self, value: str, pii_type: str) -> str:
        """Mask PII value for storage"""
        if pii_type == "email":
            parts = value.split("@")
            if len(parts) == 2:
                return f"{parts[0][:2]}***@{parts[1]}"
        elif pii_type == "phone":
            return f"***-***-{value[-4:]}"
        elif pii_type == "credit_card":
            return f"****-****-****-{value[-4:]}"
        elif pii_type == "ssn":
            return "***-**-" + value[-4:]
        elif pii_type == "name":
            parts = value.split()
            return f"{parts[0][0]}*** {parts[-1][0]}***"
        
        return "***REDACTED***"
    
    def _filter_names(self, potential_names: List[str]) -> List[str]:
        """Filter out common non-name matches"""
        # Common false positives
        false_positives = {
            "Hello World", "Thank You", "Best Regards",
            "United States", "New York", "Los Angeles",
            "Microsoft Office", "Google Chrome", "Apple iPhone"
        }
        
        return [name for name in potential_names if name not in false_positives]
    
    def _calculate_risk_level(self, pii_types: List[str]) -> str:
        """Calculate risk level based on PII types"""
        if not pii_types:
            return "none"
        
        high_risk = {"ssn", "credit_card"}
        medium_risk = {"email", "phone", "person_name"}
        
        if any(pii in high_risk for pii in pii_types):
            return "high"
        elif any(pii in medium_risk for pii in pii_types):
            return "medium"
        else:
            return "low"
    
    def _redact_content(self, content: str, entities: List[Dict]) -> str:
        """Redact PII from content"""
        redacted = content
        
        # Sort entities by position (reverse) to maintain positions
        sorted_entities = sorted(entities, key=lambda x: x["start"], reverse=True)
        
        for entity in sorted_entities:
            start = entity["start"]
            end = entity["end"]
            redacted = redacted[:start] + "[REDACTED]" + redacted[end:]
        
        return redacted