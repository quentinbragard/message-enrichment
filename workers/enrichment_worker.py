# workers/enrichment_worker.py
"""
Background worker for processing enrichment requests
"""
import asyncio
import json
from typing import Dict
from services import EnrichmentService
from workers.pubsub_handler import PubSubHandler
from utils import track_metric, log_event
from config import settings
import logging

logger = logging.getLogger(__name__)


class EnrichmentWorker:
    """Worker for processing enrichment requests from Pub/Sub"""
    
    def __init__(self):
        self.enrichment_service = EnrichmentService()
        self.pubsub_handler = PubSubHandler()
        self.running = False
    
    async def start(self):
        """Start the worker"""
        self.running = True
        logger.info(f"Starting enrichment worker with {settings.MAX_WORKERS} workers")
        
        # Create worker tasks
        tasks = []
        for i in range(settings.MAX_WORKERS):
            tasks.append(asyncio.create_task(self._worker(i)))
        
        # Wait for all workers
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        logger.info("Stopping enrichment worker")
    
    async def _worker(self, worker_id: int):
        """Individual worker process"""
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Pull message from Pub/Sub
                message = await self.pubsub_handler.pull_message()
                
                if not message:
                    # No messages, wait a bit
                    await asyncio.sleep(1)
                    continue
                
                # Process message
                await self._process_message(message, worker_id)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def _process_message(self, message: Dict, worker_id: int):
        """Process a single message"""
        try:
            logger.debug(f"Worker {worker_id} processing message")
            
            # Check if it's a batch
            if message.get("type") == "batch":
                await self._process_batch(message, worker_id)
            else:
                await self._process_single(message, worker_id)
            
            # Track metrics
            track_metric("messages_processed", 1, {"worker": str(worker_id)})
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            track_metric("processing_errors", 1, {"worker": str(worker_id)})
    
    async def _process_single(self, message: Dict, worker_id: int):
        """Process a single enrichment request"""
        from dtos import EnrichmentRequestDTO
        
        # Convert to DTO
        request = EnrichmentRequestDTO(**message)
        
        # Process
        result = await self.enrichment_service.enrich_message(request)
        
        logger.info(f"Worker {worker_id} processed message {request.message_id}")
        
        # Log event
        log_event("message_enriched", {
            "message_id": request.message_id,
            "worker_id": worker_id,
            "status": result.status,
            "cache_hit": result.cache_hit
        })
    
    async def _process_batch(self, message: Dict, worker_id: int):
        """Process a batch of enrichment requests"""
        messages = message.get("messages", [])
        
        logger.info(f"Worker {worker_id} processing batch of {len(messages)} messages")
        
        # Process each message
        for msg_data in messages:
            await self._process_single(msg_data, worker_id)
        
        logger.info(f"Worker {worker_id} completed batch processing")