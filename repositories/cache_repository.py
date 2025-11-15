# repositories/cache_repository.py
"""
Cache repository using Redis
"""
from typing import Optional, Any
import json
from core import redis_client
import logging

logger = logging.getLogger(__name__)


class CacheRepository:
    """Repository for cache operations"""
    
    def __init__(self):
        self.client = redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        return await self.client.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        return await self.client.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.client.client.delete(key))
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(self.client.client.exists(key))
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        try:
            return self.client.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing {key}: {e}")
            return 0