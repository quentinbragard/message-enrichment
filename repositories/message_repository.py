# repositories/message_repository.py
"""
Message repository for database operations
"""
from typing import Optional, List, Dict
from datetime import datetime
from core import supabase
import logging

logger = logging.getLogger(__name__)


class MessageRepository:
    """Repository for message-related database operations"""
    
    @staticmethod
    async def get_message(message_id: str) -> Optional[Dict]:
        """Get a message by ID"""
        try:
            response = supabase.table("messages")\
                .select("*")\
                .eq("id", message_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching message {message_id}: {e}")
            return None
    
    @staticmethod
    async def get_conversation_messages(
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get messages from a conversation"""
        try:
            response = supabase.table("messages")\
                .select("*")\
                .eq("conversation_id", conversation_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching conversation {conversation_id}: {e}")
            return []
    
    @staticmethod
    async def get_assistant_response(
        conversation_id: str,
        parent_message_id: str
    ) -> Optional[str]:
        """Get assistant response for a user message"""
        try:
            response = supabase.table("messages")\
                .select("content")\
                .eq("conversation_id", conversation_id)\
                .eq("parent_message_id", parent_message_id)\
                .eq("role", "assistant")\
                .single()\
                .execute()
            return response.data.get("content") if response.data else None
        except Exception as e:
            logger.error(f"Error fetching assistant response: {e}")
            return None