# workers/__init__.py
from .enrichment_worker import EnrichmentWorker
from .pubsub_handler import PubSubHandler

async def start_worker():
    """Start the background worker"""
    worker = EnrichmentWorker()
    await worker.start()

__all__ = ["EnrichmentWorker", "PubSubHandler", "start_worker"]