"""Repository for enriched chats (first message per chat)."""
from typing import Dict
from core import supabase
import logging

logger = logging.getLogger(__name__)


class EnrichedChatsRepository:
    """Persists enriched chat records."""

    table_name = "enriched_chats"

    @classmethod
    async def save(cls, record: Dict) -> bool:
        try:
            response = (
                supabase.table(cls.table_name)
                .upsert(record)
                .execute()
            )
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error saving enriched chat: {e}")
            return False
