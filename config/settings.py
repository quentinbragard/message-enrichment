# config/settings.py
"""
Enrichment service configuration
"""
import os
from typing import List, Optional
from enum import Enum
import dotenv

dotenv.load_dotenv()


class Environment(str, Enum):
    """Environment types"""
    LOCAL = "local"
    STAGING = "staging"
    PROD = "prod"


class BaseSettings:
    """Base settings shared across all environments"""
    
    # GCP
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_REGION: str = os.getenv("GCP_REGION", "europe-west1")
    
    # Pub/Sub
    PUBSUB_TOPIC: str = os.getenv("PUBSUB_TOPIC", "enrichment-requests")
    PUBSUB_SUBSCRIPTION: str = os.getenv("PUBSUB_SUBSCRIPTION", "enrichment-worker")
    
    # Redis (Memorystore)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_TTL: int = int(os.getenv("REDIS_TTL", 3600))  # 1 hour
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # LLM
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "google/gemma-2-9b-it:nebius")
    
    # Service
    SERVICE_NAME: str = "enrichment-service"
    SERVICE_MODE: str = os.getenv("SERVICE_MODE", "api")  # api or worker
    APP_VERSION: str = "1.0.0"
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", 10))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", 10))
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", Environment.LOCAL.value)


class LocalSettings(BaseSettings):
    """Local development settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # Override for local development
    SERVICE_MODE: str = os.getenv("SERVICE_MODE", "api")
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", 2))


class StagingSettings(BaseSettings):
    """Staging environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"


class ProdSettings(BaseSettings):
    """Production environment settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    
    # Production optimizations
    BATCH_SIZE: int = 25
    MAX_WORKERS: int = 50


def get_settings() -> BaseSettings:
    """Factory function to get settings based on environment"""
    env = os.getenv("ENVIRONMENT", Environment.LOCAL.value).lower()
    
    settings_map = {
        Environment.LOCAL.value: LocalSettings,
        Environment.STAGING.value: StagingSettings,
        Environment.PROD.value: ProdSettings,
    }
    
    settings_class = settings_map.get(env, LocalSettings)
    return settings_class()


settings = get_settings()