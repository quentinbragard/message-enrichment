# services/enrichment_service.py
"""
Main enrichment service with batch processing
"""
import asyncio
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, List, Set
from uuid import uuid4
from config import settings

from domains.entities import EnrichmentResult
from dtos import (
    EnrichmentRequestDTO,
    EnrichmentResponseDTO,
    BatchEnrichmentRequestDTO,
    BatchEnrichmentResponseDTO
)
from repositories import CacheRepository, EnrichmentRepository

# Fix: Use relative imports instead of importing from services package
from .classification_service import ClassificationService
from .quality_service import QualityService
from .pii_service import PIIService

from utils import PromptLoader
import logging

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Orchestrates the enrichment process"""
    
    def __init__(self):
        self.classification_service = ClassificationService()
        self.quality_service = QualityService()
        self.pii_service = PIIService()
        self.cache_repo = CacheRepository()
        self.enrichment_repo = EnrichmentRepository()
        self.prompt_loader = PromptLoader()
    
    async def enrich_message(
        self,
        request: EnrichmentRequestDTO
    ) -> EnrichmentResponseDTO:
        """
        Main enrichment orchestration
        """
        start_time = datetime.utcnow()
        job_id = self._generate_job_id(request)
        
        try:
            # Check cache
            cache_key = self._generate_cache_key(request)
            cached_result = await self.cache_repo.get(cache_key)
            
            if cached_result:
                logger.info(f"Cache hit for message {request.message_id}")
                return EnrichmentResponseDTO(
                    job_id=job_id,
                    status="completed",
                    message_id=request.message_id,
                    result=cached_result,
                    cache_hit=True
                )
            
            # Wait for assistant response if needed
            if request.wait_for_response and request.role == "user":
                assistant_response = await self._wait_for_assistant_response(
                    request.conversation_id,
                    request.message_id
                )
                if assistant_response:
                    request.assistant_response = assistant_response
            
            # Run enrichments in parallel
            tasks = []
            
            # Classification (always run)
            tasks.append(
                self.classification_service.classify(
                    request.content,
                    request.assistant_response,
                    request.conversation_history
                )
            )
            
            # Quality analysis
            if request.include_quality_analysis:
                tasks.append(
                    self.quality_service.analyze(
                        request.content,
                        request.assistant_response
                    )
                )
            
            # PII detection
            if request.include_pii_detection:
                tasks.append(
                    self.pii_service.detect(request.content)
                )
            
            # Execute all tasks
            results = await asyncio.gather(*tasks)
            
            # Build result
            enrichment_result = self._build_result(
                request,
                results,
                start_time
            )
            
            # Cache result
            await self.cache_repo.set(
                cache_key,
                enrichment_result,
                ttl=3600
            )
            
            # Store in database
            await self.enrichment_repo.save(enrichment_result)
            
            return EnrichmentResponseDTO(
                job_id=job_id,
                status="completed",
                message_id=request.message_id,
                result=enrichment_result,
                processing_time_ms=self._calculate_processing_time(start_time),
                cache_hit=False
            )
            
        except Exception as e:
            logger.error(f"Enrichment failed for message {request.message_id}: {e}")
            return EnrichmentResponseDTO(
                job_id=job_id,
                status="failed",
                message_id=request.message_id,
                error=str(e)
            )
    
    async def enrich_batch(
        self,
        request: BatchEnrichmentRequestDTO
    ) -> BatchEnrichmentResponseDTO:
        """
        Process a batch of messages
        """
        start_time = datetime.utcnow()
        batch_id = request.batch_id or f"batch_{uuid4().hex[:8]}"
        
        logger.info(f"Starting batch {batch_id} with {len(request.messages)} messages")
        
        # Initialize response
        response = BatchEnrichmentResponseDTO(
            batch_id=batch_id,
            status="processing",
            organization_id=request.organization_id,
            total_messages=len(request.messages),
            processed_messages=0,
            successful_messages=0,
            failed_messages=0,
            started_at=start_time
        )
        
        try:
            # Deduplicate if requested
            messages_to_process = request.messages
            if request.deduplicate:
                messages_to_process = self._deduplicate_messages(request.messages)
                logger.info(f"Deduplicated: {len(request.messages)} -> {len(messages_to_process)}")
            
            # Group by conversation if context sharing is enabled
            if request.share_context:
                conversation_groups = self._group_by_conversation(messages_to_process)
            else:
                conversation_groups = {msg.message_id: [msg] for msg in messages_to_process}
            
            # Process messages
            results = []
            errors = []
            cache_hits = 0
            cache_misses = 0
            
            if request.parallel_processing:
                # Process in parallel
                tasks = []
                for group_messages in conversation_groups.values():
                    # Share context within conversation group
                    shared_context = self._build_shared_context(group_messages)
                    
                    for msg in group_messages:
                        if shared_context:
                            msg.conversation_history = shared_context
                        tasks.append(self._process_single_with_tracking(msg))
                
                # Execute all tasks
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(task_results):
                    if isinstance(result, Exception):
                        if request.fail_fast:
                            raise result
                        errors.append({
                            "message_id": messages_to_process[i].message_id,
                            "error": str(result)
                        })
                        response.failed_messages += 1
                    else:
                        results.append(result)
                        response.successful_messages += 1
                        if result.cache_hit:
                            cache_hits += 1
                        else:
                            cache_misses += 1
                    
                    response.processed_messages += 1
            
            else:
                # Process sequentially
                for group_messages in conversation_groups.values():
                    shared_context = self._build_shared_context(group_messages)
                    
                    for msg in group_messages:
                        try:
                            if shared_context:
                                msg.conversation_history = shared_context
                            
                            result = await self._process_single_with_tracking(msg)
                            results.append(result)
                            response.successful_messages += 1
                            
                            if result.cache_hit:
                                cache_hits += 1
                            else:
                                cache_misses += 1
                        
                        except Exception as e:
                            if request.fail_fast:
                                raise
                            errors.append({
                                "message_id": msg.message_id,
                                "error": str(e)
                            })
                            response.failed_messages += 1
                        
                        response.processed_messages += 1
            
            # Update response
            response.status = "completed" if not errors else "partial"
            response.results = results if request.include_partial_results or not errors else None
            response.errors = errors if errors else None
            response.completed_at = datetime.utcnow()
            response.processing_time_ms = self._calculate_processing_time(start_time)
            response.cache_hits = cache_hits
            response.cache_misses = cache_misses
            
            # Store batch result
            await self._store_batch_result(response)
            
            # Trigger webhook if provided
            if request.webhook_url:
                asyncio.create_task(self._trigger_webhook(request.webhook_url, response))
            
            logger.info(f"Batch {batch_id} completed: {response.successful_messages}/{response.total_messages} successful")
            
            return response
            
        except Exception as e:
            logger.error(f"Batch {batch_id} failed: {e}")
            response.status = "failed"
            response.errors = [{"batch_error": str(e)}]
            response.completed_at = datetime.utcnow()
            response.processing_time_ms = self._calculate_processing_time(start_time)
            return response
    
    def _generate_job_id(self, request: EnrichmentRequestDTO) -> str:
        """Generate unique job ID"""
        data = f"{request.message_id}:{datetime.utcnow().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _generate_cache_key(self, request: EnrichmentRequestDTO) -> str:
        """Generate cache key for request"""
        # Include assistant response in cache key if available
        data = f"{request.content}:{request.assistant_response or ''}"
        return f"enrichment:{hashlib.md5(data.encode()).hexdigest()}"
    
    async def _wait_for_assistant_response(
        self,
        conversation_id: Optional[str],
        message_id: str,
        timeout: float = 5.0
    ) -> Optional[str]:
        """Wait for assistant response with timeout"""
        if not conversation_id:
            return None
        
        for _ in range(int(timeout * 10)):  # Check every 100ms
            response = await self.cache_repo.get(
                f"assistant:{conversation_id}:{message_id}"
            )
            if response:
                return response
            await asyncio.sleep(0.1)
        
        return None
    
    def _build_result(
        self,
        request: EnrichmentRequestDTO,
        results: List,
        start_time: datetime
    ) -> Dict:
        """Build enrichment result from component results"""
        classification = results[0]
        quality = results[1] if len(results) > 1 else None
        pii = results[2] if len(results) > 2 else None
        
        return {
            "message_id": request.message_id,
            "user_id": request.user_id,
            "organization_id": request.organization_id,
            "enriched_at": datetime.utcnow().isoformat(),
            "processing_time_ms": self._calculate_processing_time(start_time),
            "work_classification": classification.get("work"),
            "topic_classification": classification.get("topic"),
            "intent_classification": classification.get("intent"),
            "quality_analysis": quality,
            "pii_detection": pii,
            "overall_confidence": self._calculate_overall_confidence(classification),
            "used_assistant_response": bool(request.assistant_response),
            "model_used": getattr(settings, "DEFAULT_MODEL", "gpt-4.1-nano")
        }
    
    def _calculate_processing_time(self, start_time: datetime) -> float:
        """Calculate processing time in milliseconds"""
        delta = datetime.utcnow() - start_time
        return delta.total_seconds() * 1000
    
    def _calculate_overall_confidence(self, classification: Dict) -> float:
        """Calculate overall confidence score"""
        confidences = []
        
        for key in ["work", "topic", "intent"]:
            if key in classification:
                conf = classification[key].get("confidence", "medium")
                if conf == "high":
                    confidences.append(1.0)
                elif conf == "medium":
                    confidences.append(0.5)
                else:
                    confidences.append(0.25)
        
        return sum(confidences) / len(confidences) if confidences else 0.5
    
    async def _process_single_with_tracking(
        self,
        request: EnrichmentRequestDTO
    ) -> EnrichmentResponseDTO:
        """Process single message with metrics tracking"""
        start = datetime.utcnow()
        result = await self.enrich_message(request)
        
        # Track per-message metrics (if monitoring is available)
        try:
            from utils import track_metric
            track_metric("message_processing_time", 
                        (datetime.utcnow() - start).total_seconds() * 1000,
                        {"organization": request.organization_id})
        except ImportError:
            pass  # Monitoring not available
        
        return result
    
    def _deduplicate_messages(
        self,
        messages: List[EnrichmentRequestDTO]
    ) -> List[EnrichmentRequestDTO]:
        """Remove duplicate messages based on content hash"""
        seen: Set[str] = set()
        unique_messages = []
        
        for msg in messages:
            # Create content hash
            content_hash = hashlib.md5(msg.content.encode()).hexdigest()
            
            if content_hash not in seen:
                seen.add(content_hash)
                unique_messages.append(msg)
            else:
                logger.debug(f"Skipping duplicate message {msg.message_id}")
        
        return unique_messages
    
    def _group_by_conversation(
        self,
        messages: List[EnrichmentRequestDTO]
    ) -> Dict[str, List[EnrichmentRequestDTO]]:
        """Group messages by conversation ID"""
        groups = {}
        
        for msg in messages:
            conv_id = msg.conversation_id or msg.message_id
            if conv_id not in groups:
                groups[conv_id] = []
            groups[conv_id].append(msg)
        
        # Sort messages within each conversation by message_id (assuming chronological)
        for conv_id in groups:
            groups[conv_id].sort(key=lambda m: m.message_id)
        
        return groups
    
    def _build_shared_context(
        self,
        messages: List[EnrichmentRequestDTO]
    ) -> List[Dict]:
        """Build shared context for a conversation group"""
        context = []
        
        for msg in messages:
            context.append({
                "role": msg.role,
                "content": msg.content[:500],  # Truncate for context
                "message_id": msg.message_id
            })
        
        return context
    
    async def _store_batch_result(self, response: BatchEnrichmentResponseDTO):
        """Store batch processing result"""
        try:
            await self.cache_repo.set(
                f"batch:{response.batch_id}",
                response.dict(),
                ttl=86400  # 24 hours
            )
        except Exception as e:
            logger.error(f"Failed to store batch result: {e}")
    
    async def _trigger_webhook(self, webhook_url: str, response: BatchEnrichmentResponseDTO):
        """Trigger webhook with batch results"""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    webhook_url,
                    json=response.dict(),
                    timeout=30.0
                )
            
            logger.info(f"Webhook triggered for batch {response.batch_id}")
        except Exception as e:
            logger.error(f"Failed to trigger webhook: {e}")
    
    async def get_batch_status(
        self,
        batch_id: str,
        include_results: bool = False
    ) -> Optional[BatchEnrichmentResponseDTO]:
        """Get status of a batch processing job"""
        try:
            # Check cache
            cached = await self.cache_repo.get(f"batch:{batch_id}")
            if cached:
                response = BatchEnrichmentResponseDTO(**cached)
                if not include_results:
                    response.results = None
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get batch status: {e}")
            return None
