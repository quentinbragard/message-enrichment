"""Lightweight chat classification using gpt-4.1-nano + compact prompt."""
from typing import Dict, Optional
from core import llm_client
from utils import PromptLoader
import json
import re
import logging

logger = logging.getLogger(__name__)


class SimpleClassificationService:
    def __init__(self, prompt_name: str = "chat_classification_quality.txt"):
        self.llm = llm_client
        self.prompt_loader = PromptLoader()
        self.prompt_name = prompt_name

    async def classify(self, user_message: str, assistant_response: Optional[str] = None) -> Dict:
        prompt = self.prompt_loader.load(self.prompt_name)
        formatted = prompt.format(
            user_message=user_message[:2000],
            assistant_response=assistant_response[:2000] if assistant_response else "Not provided",
        )

        response = await self.llm.complete(
            system_prompt="You classify multilingual prompts into work/theme/intent. Return ONLY JSON.",
            user_message=formatted,
            temperature=0.1,
            max_tokens=400,
        )

        parsed = self._coerce_json(response)
        if parsed is not None:
            return parsed

        # Final fallback
        logger.error(f"Failed to parse classification response, returning default. Raw: {response}")
        return {
            "is_work_related": False,
            "theme": "non_work",
            "intent": "non_work",
            "raw": response,
        }

    def _coerce_json(self, text):
        """Attempt to coerce LLM output to JSON, removing fences and junk."""
        if isinstance(text, dict):
            return text
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                return None

        try:
            return json.loads(text)
        except Exception:
            pass

        cleaned = text.strip()

        # strip code fences
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1] if len(parts) > 1 else cleaned
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]

        # isolate first JSON object boundaries
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = cleaned[start : end + 1]
            try:
                return json.loads(candidate)
            except Exception:
                # try to remove trailing commas or control chars
                candidate = re.sub(r"\,\s*}\s*$", "}", candidate, flags=re.DOTALL)
                candidate = candidate.replace("\n", " ")
                try:
                    return json.loads(candidate)
                except Exception:
                    logger.debug(f"JSON coercion failed for candidate: {candidate}")
        return None
