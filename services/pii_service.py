# services/pii_service.py
"""PII detection service (regex + GLiNER PII model when available)."""
import asyncio
import os
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PIIService:
    """Service for PII detection with model-assisted entities when enabled."""

    def __init__(self):
        # Regex patterns remain as a fast, low-latency fallback
        self.patterns = {
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "phone": re.compile(r"\b(?:\+?[1-9]\d{0,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b"),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
            "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
            "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        }

        self.name_pattern = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")

        # GLiNER configuration
        self.enable_gliner = os.getenv("ENABLE_GLINER_PII", "true").lower() == "true"
        self.gliner_model_name = os.getenv("GLINER_PII_MODEL", "nvidia/gliner-PII")
        self.gliner_threshold = float(os.getenv("GLINER_PII_THRESHOLD", 0.35))
        # Label set is intentionally broad; model will emit only what it knows
        self.gliner_labels = [
            "PERSON",
            "NAME",
            "EMAIL",
            "PHONE_NUMBER",
            "ADDRESS",
            "IP_ADDRESS",
            "CREDIT_CARD",
            "BANK_ACCOUNT",
            "PASSPORT",
            "DRIVER_LICENSE",
            "SSN",
            "USERNAME",
            "PASSWORD",
            "MEDICAL_INFO",
        ]

        self._gliner_model = None

    async def detect(self, content: str) -> Dict:
        """Detect PII using GLiNER if available, plus regex heuristics."""
        try:
            regex_entities = self._detect_with_regex(content)
            gliner_entities = await self._detect_with_gliner(content) if self.enable_gliner else []

            entities = self._merge_entities(regex_entities, gliner_entities)
            pii_types = sorted({entity["type"] for entity in entities})

            risk_level = self._calculate_risk_level(pii_types)

            redacted_content = None
            if entities:
                redacted_content = self._redact_content(content, entities)

            return {
                "has_pii": len(entities) > 0,
                "pii_types": pii_types,
                "risk_level": risk_level,
                "entities": entities,
                "redacted_content": redacted_content,
                "detector": "gliner+regex" if gliner_entities else "regex",
            }

        except Exception as e:
            logger.error(f"PII detection failed: {e}")
            return {
                "has_pii": False,
                "pii_types": [],
                "risk_level": "none",
                "entities": [],
                "redacted_content": None,
                "detector": "error",
            }

    def _detect_with_regex(self, content: str) -> List[Dict]:
        """Regex-based detections as a low-cost fallback."""
        entities: List[Dict] = []
        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(content)
            for match in matches:
                # Use find to track span; safe even if repeated because precision is coarse
                start = content.find(match)
                entities.append({
                    "type": pii_type,
                    "value": self._mask_value(match, pii_type),
                    "start": start,
                    "end": start + len(match),
                    "confidence": 0.6,
                    "source": "regex",
                })

        # Basic name detection
        name_matches = self.name_pattern.findall(content)
        potential_names = self._filter_names(name_matches)
        for name in potential_names:
            start = content.find(name)
            entities.append({
                "type": "person_name",
                "value": self._mask_value(name, "name"),
                "start": start,
                "end": start + len(name),
                "confidence": 0.4,
                "source": "regex",
            })

        return entities

    async def _detect_with_gliner(self, content: str) -> List[Dict]:
        """Model-based detection with GLiNER PII (runs in a thread to avoid blocking)."""
        model = self._ensure_gliner_loaded()
        if not model:
            return []

        def _predict():
            try:
                return model.predict_entities(
                    content,
                    labels=self.gliner_labels,
                    threshold=self.gliner_threshold,
                )
            except Exception as e:  # pragma: no cover - safety net
                logger.warning(f"GLiNER prediction failed, falling back to regex: {e}")
                return []

        results = await asyncio.to_thread(_predict)

        entities: List[Dict] = []
        for item in results:
            label = str(item.get("label", "")).upper()
            normalized = self._normalize_label(label)
            start = item.get("start", -1)
            end = item.get("end", -1)
            text = item.get("text", "")

            if not normalized or start < 0 or end < 0:
                continue

            entities.append({
                "type": normalized,
                "value": self._mask_value(text, normalized),
                "start": start,
                "end": end,
                "confidence": float(item.get("score", 0.0)),
                "source": "gliner",
            })

        return entities

    def _ensure_gliner_loaded(self):
        """Lazy-load the GLiNER model to keep startup light."""
        if not self.enable_gliner:
            return None

        if self._gliner_model is not None:
            return self._gliner_model

        try:
            from gliner import GLiNER

            token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
            self._gliner_model = GLiNER.from_pretrained(
                self.gliner_model_name,
                token=token,
            )
            logger.info(f"Loaded GLiNER model: {self.gliner_model_name}")
        except Exception as e:
            logger.warning(f"GLiNER unavailable, using regex only: {e}")
            self.enable_gliner = False
            self._gliner_model = None

        return self._gliner_model

    def _merge_entities(self, regex_entities: List[Dict], gliner_entities: List[Dict]) -> List[Dict]:
        """Combine entities, preferring GLiNER spans and dropping overlapping regex spans."""
        combined = gliner_entities + []

        for entity in regex_entities:
            # Skip any regex entity that overlaps a GLiNER span (any type) to avoid double-redaction
            if any(
                e["start"] <= entity["end"] and entity["start"] <= e["end"]
                for e in gliner_entities
            ):
                continue
            combined.append(entity)

        # Sort for deterministic output
        return sorted(combined, key=lambda e: (e["start"], -e.get("confidence", 0)))

    def _normalize_label(self, label: str) -> Optional[str]:
        mapping = {
            "PERSON": "person_name",
            "NAME": "person_name",
            "EMAIL": "email",
            "EMAIL_ADDRESS": "email",
            "PHONE": "phone",
            "PHONE_NUMBER": "phone",
            "ADDRESS": "address",
            "IP_ADDRESS": "ip_address",
            "CREDIT_CARD": "credit_card",
            "CARD": "credit_card",
            "BANK_ACCOUNT": "bank_account",
            "ACCOUNT_NUMBER": "bank_account",
            "PASSPORT": "passport",
            "DRIVER_LICENSE": "driver_license",
            "SSN": "ssn",
            "SOCIAL_SECURITY_NUMBER": "ssn",
            "USERNAME": "username",
            "PASSWORD": "password",
            "MEDICAL_INFO": "medical_info",
        }
        return mapping.get(label)

    def _mask_value(self, value: str, pii_type: str) -> str:
        """Mask PII value for storage."""
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
        elif pii_type in {"person_name", "name"}:
            parts = value.split()
            if len(parts) >= 2:
                return f"{parts[0][0]}*** {parts[-1][0]}***"
        elif pii_type == "bank_account":
            return "***" + value[-4:]
        elif pii_type in {"username", "password"}:
            return "***REDACTED***"

        return "***REDACTED***"

    def _filter_names(self, potential_names: List[str]) -> List[str]:
        """Filter out common non-name matches."""
        false_positives = {
            "Hello World",
            "Thank You",
            "Best Regards",
            "United States",
            "New York",
            "Los Angeles",
            "Microsoft Office",
            "Google Chrome",
            "Apple iPhone",
        }

        return [name for name in potential_names if name not in false_positives]

    def _calculate_risk_level(self, pii_types: List[str]) -> str:
        """Calculate risk level based on PII types."""
        if not pii_types:
            return "none"

        high_risk = {"ssn", "credit_card", "bank_account", "passport", "driver_license", "password"}
        medium_risk = {"email", "phone", "person_name", "address", "ip_address", "username", "medical_info"}

        if any(pii in high_risk for pii in pii_types):
            return "high"
        if any(pii in medium_risk for pii in pii_types):
            return "medium"
        return "low"

    def _redact_content(self, content: str, entities: List[Dict]) -> str:
        """Redact PII from content."""
        redacted = content

        sorted_entities = sorted(entities, key=lambda x: x["start"], reverse=True)

        for entity in sorted_entities:
            start = entity["start"]
            end = entity["end"]
            if start < 0 or end < 0:
                continue
            redacted = redacted[:start] + "[REDACTED]" + redacted[end:]

        return redacted
