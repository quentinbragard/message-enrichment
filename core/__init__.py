# core/__init__.py
from .llm import LLMClient
from .redis import RedisClient
from .pubsub import PubSubClient
from .supabase import supabase

# Initialize singletons
llm_client = LLMClient()
redis_client = RedisClient()
pubsub_client = PubSubClient()

__all__ = ["llm_client", "redis_client", "pubsub_client", "supabase"]