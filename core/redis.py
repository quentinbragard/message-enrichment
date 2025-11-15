# core/redis.py
"""
Redis client for caching
"""
import redis
import json
from typing import Optional, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for caching"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            connection_pool=redis.BlockingConnectionPool(
                max_connections=50,
                timeout=20
            )
        )
        logger.info("Redis client initialized")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or settings.REDIS_TTL
            self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
