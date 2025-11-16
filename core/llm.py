# core/llm.py - OpenAI client
"""Async LLM client using OpenAI Chat Completions API"""
from typing import Iterable, Optional
from config import settings
import logging
import os
import asyncio
import json
from openai import AsyncOpenAI


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """LLM client targeting gpt-4.1-nano for lowest cost."""

    def __init__(self, model: Optional[str] = None):
        api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for LLM access")

        self.model = model or getattr(settings, "DEFAULT_MODEL", "gpt-4.1-nano")
        self.client = AsyncOpenAI(api_key=api_key)

        logger.info("Initialized OpenAI LLM client")
        logger.info(f"Model: {self.model}")

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        """Single completion using Chat Completions API."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        return self._extract_text(response)

    async def complete_batch(
        self,
        system_prompt: str,
        user_messages: Iterable[str],
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> list[str]:
        """Run multiple prompts concurrently; still uses cheapest model."""

        tasks = [
            asyncio.create_task(
                self.complete(
                    system_prompt=system_prompt,
                    user_message=message,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            )
            for message in user_messages
        ]

        return await asyncio.gather(*tasks)

    @staticmethod
    def _extract_text(response) -> str:
        """Normalize Chat Completions output to plain text."""

        # Convert to dict early for consistent access across SDK shapes
        dump = response.model_dump(exclude_none=True) if hasattr(response, "model_dump") else None
        if dump:
            choices_dump = dump.get("choices")
            if choices_dump:
                choice0 = choices_dump[0]
                message_dump = choice0.get("message") if isinstance(choice0, dict) else None
                content_dump = None
                if message_dump:
                    if "parsed" in message_dump:
                        return LLMClient._parsed_to_text(message_dump["parsed"])
                    if "refusal" in message_dump:
                        return LLMClient._parsed_to_text(message_dump["refusal"])
                    content_dump = message_dump.get("content")
                if content_dump:
                    return LLMClient._content_to_text(content_dump)

        choices = getattr(response, "choices", None)
        if not choices:
            raise ValueError("Unexpected OpenAI response format: missing choices")

        first = choices[0]
        message = getattr(first, "message", None) or first.get("message") if isinstance(first, dict) else None

        content = None

        if message:
            content = getattr(message, "content", None) or message.get("content") if isinstance(message, dict) else None

            # If structured JSON is returned, it may live under `parsed`
            parsed = getattr(message, "parsed", None) or message.get("parsed") if isinstance(message, dict) else None
            if parsed is not None and (not content):
                return LLMClient._parsed_to_text(parsed)

            # Some SDK versions use `refusal` instead of content when blocked
            refusal = getattr(message, "refusal", None) or message.get("refusal") if isinstance(message, dict) else None
            if refusal is not None and not content:
                return LLMClient._parsed_to_text(refusal)

        # Some SDK versions may return content directly on the choice
        if not content:
            content = getattr(first, "content", None) or first.get("content") if isinstance(first, dict) else None

        # As a fallback, serialize the message/choice/response structures
        if content is None:
            if message and hasattr(message, "model_dump"):
                return LLMClient._parsed_to_text(message.model_dump(exclude_none=True))
            if hasattr(first, "model_dump"):
                return LLMClient._parsed_to_text(first.model_dump(exclude_none=True))
            if hasattr(response, "model_dump"):
                return LLMClient._parsed_to_text(response.model_dump(exclude_none=True))
            raise ValueError("Unexpected OpenAI response format: missing content text")

        return LLMClient._content_to_text(content)

    @staticmethod
    def _content_to_text(content) -> str:
        """Flatten content blocks or strings into a plain text result."""

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []
            for item in content:
                text = None
                if isinstance(item, dict):
                    text = item.get("text") or item.get("output_text") or item.get("value") or item.get("content")
                else:
                    text = (
                        getattr(item, "text", None)
                        or getattr(item, "output_text", None)
                        or getattr(item, "value", None)
                        or getattr(item, "content", None)
                    )

                if isinstance(text, (list, dict)):
                    parts.append(LLMClient._parsed_to_text(text))
                elif text is not None:
                    parts.append(str(text))

            return "".join(parts).strip()

        return str(content)

    @staticmethod
    def _parsed_to_text(parsed) -> str:
        """Convert parsed JSON content into a string payload."""

        try:
            return json.dumps(parsed)
        except Exception:
            return str(parsed)
