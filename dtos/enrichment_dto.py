# dtos/enrichment_dto.py
"""
Enrichment DTOs - Complete file
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class EnrichmentRequestDTO(BaseModel):
    """Request for message enrichment"""
    message_id: str
    user_id: str
    organization_id: str
    content: str
    role: str = "user"
    
    # Optional context
    conversation_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    assistant_response: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None
    
    # Processing options
    priority: str = Field(default="normal", pattern="^(low|normal|high)$")
    wait_for_response: bool = True
    include_pii_detection: bool = True
    include_quality_analysis: bool = True
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError("Content cannot be empty")
        if len(v) > 100000:  # 100k char limit
            raise ValueError("Content exceeds maximum length")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_123",
                "user_id": "user_456",
                "organization_id": "org_789",
                "content": "Can you help me write a business proposal?",
                "role": "user",
                "priority": "normal"
            }
        }


class EnrichmentResponseDTO(BaseModel):
    """Response for enrichment request"""
    job_id: str
    status: str  # processing, completed, failed, skipped
    message_id: str
    
    # Results (when completed)
    result: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None
    cache_hit: bool = False
    
    # Error (when failed)
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_abc123",
                "status": "completed",
                "message_id": "msg_123",
                "result": {
                    "work_classification": {
                        "is_work": True,
                        "confidence": "high"
                    },
                    "topic_classification": {
                        "primary_topic": "WRITING",
                        "confidence": "high"
                    }
                },
                "processing_time_ms": 1234.5,
                "cache_hit": False
            }
        }


class BatchEnrichmentRequestDTO(BaseModel):
    """Request for batch message enrichment"""
    batch_id: Optional[str] = Field(
        None, 
        description="Optional batch ID for tracking"
    )
    organization_id: str
    messages: List[EnrichmentRequestDTO] = Field(
        ..., 
        min_items=1,
        max_items=100,
        description="List of messages to enrich"
    )
    
    # Batch processing options
    priority: str = Field(
        default="normal", 
        pattern="^(low|normal|high)$",
        description="Priority for the entire batch"
    )
    parallel_processing: bool = Field(
        default=True,
        description="Process messages in parallel"
    )
    fail_fast: bool = Field(
        default=False,
        description="Stop on first error"
    )
    
    # Optimization options
    share_context: bool = Field(
        default=True,
        description="Share conversation context across messages in same conversation"
    )
    deduplicate: bool = Field(
        default=True,
        description="Skip duplicate messages"
    )
    
    # Result options
    webhook_url: Optional[str] = Field(
        None,
        description="Webhook to call when batch is complete"
    )
    include_partial_results: bool = Field(
        default=True,
        description="Return partial results if some messages fail"
    )
    
    @validator('messages')
    def validate_messages(cls, v):
        if len(v) > 100:
            raise ValueError("Maximum 100 messages per batch")
        
        # Check for duplicate message IDs
        message_ids = [msg.message_id for msg in v]
        if len(message_ids) != len(set(message_ids)):
            raise ValueError("Duplicate message IDs found in batch")
        
        return v
    
    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError("Webhook URL must be a valid HTTP/HTTPS URL")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "messages": [
                    {
                        "message_id": "msg_1",
                        "user_id": "user_1",
                        "organization_id": "org_123",
                        "content": "Can you help me write a business proposal?"
                    },
                    {
                        "message_id": "msg_2",
                        "user_id": "user_1",
                        "organization_id": "org_123",
                        "content": "What's the weather today?"
                    }
                ],
                "priority": "normal",
                "parallel_processing": True,
                "webhook_url": "https://api.example.com/webhook/enrichment"
            }
        }


class BatchEnrichmentResponseDTO(BaseModel):
    """Response for batch enrichment request"""
    batch_id: str
    status: str = Field(
        ..., 
        pattern="^(processing|completed|failed|partial)$"
    )
    organization_id: str
    
    # Progress tracking
    total_messages: int
    processed_messages: int
    successful_messages: int
    failed_messages: int
    
    # Results - Using List of EnrichmentResponseDTO
    results: Optional[List[EnrichmentResponseDTO]] = None
    errors: Optional[List[Dict[str, str]]] = None
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[float] = None
    
    # Cache stats
    cache_hits: int = 0
    cache_misses: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_abc123",
                "status": "completed",
                "organization_id": "org_123",
                "total_messages": 2,
                "processed_messages": 2,
                "successful_messages": 2,
                "failed_messages": 0,
                "results": [
                    {
                        "job_id": "job_1",
                        "status": "completed",
                        "message_id": "msg_1",
                        "cache_hit": False
                    },
                    {
                        "job_id": "job_2",
                        "status": "completed",
                        "message_id": "msg_2",
                        "cache_hit": True
                    }
                ],
                "cache_hits": 1,
                "cache_misses": 1,
                "started_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:00:05Z",
                "processing_time_ms": 5000
            }
        }


class BatchStatusRequestDTO(BaseModel):
    """Request for batch status check"""
    batch_id: str
    include_results: bool = Field(
        default=False,
        description="Include full results in response"
    )


class EnrichmentStatsDTO(BaseModel):
    """Statistics for enrichment operations"""
    organization_id: str
    period_start: datetime
    period_end: datetime
    
    # Volume stats
    total_messages: int
    unique_users: int
    unique_conversations: int
    
    # Classification stats
    work_messages: int
    non_work_messages: int
    work_percentage: float
    
    # Topic distribution
    topic_distribution: Dict[str, int]
    
    # Quality stats
    avg_quality_score: float
    high_quality_percentage: float
    needs_clarification_percentage: float
    
    # PII stats
    messages_with_pii: int
    pii_percentage: float
    pii_types_found: List[str]
    
    # Performance stats
    avg_processing_time_ms: float
    cache_hit_rate: float
    error_rate: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "org_123",
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": "2024-01-31T23:59:59Z",
                "total_messages": 10000,
                "unique_users": 150,
                "unique_conversations": 2500,
                "work_messages": 7500,
                "non_work_messages": 2500,
                "work_percentage": 75.0,
                "topic_distribution": {
                    "WRITING": 3000,
                    "ANALYSIS": 2000,
                    "TECHNICAL": 2500,
                    "PERSONAL": 2500
                },
                "avg_quality_score": 7.2,
                "high_quality_percentage": 65.0,
                "needs_clarification_percentage": 15.0,
                "messages_with_pii": 1200,
                "pii_percentage": 12.0,
                "pii_types_found": ["email", "phone", "person_name"],
                "avg_processing_time_ms": 1500.0,
                "cache_hit_rate": 0.35,
                "error_rate": 0.02
            }
        }


class EnrichmentResultDTO(BaseModel):
    """Complete enrichment result data"""
    message_id: str
    user_id: str
    organization_id: str
    enriched_at: datetime
    processing_time_ms: float
    
    # Classifications
    work_classification: Dict[str, Any]
    topic_classification: Dict[str, Any] 
    intent_classification: Dict[str, Any]
    
    # Analysis
    quality_analysis: Optional[Dict[str, Any]] = None
    pii_detection: Optional[Dict[str, Any]] = None
    
    # Metadata
    overall_confidence: float
    used_assistant_response: bool
    model_used: str
    cache_hit: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_123",
                "user_id": "user_456",
                "organization_id": "org_789",
                "enriched_at": "2024-01-15T10:00:00Z",
                "processing_time_ms": 1234.5,
                "work_classification": {
                    "is_work": True,
                    "work_type": "email",
                    "confidence": "high",
                    "reasoning": "Professional email composition",
                    "signals": ["formal tone", "business context"]
                },
                "topic_classification": {
                    "primary": "WRITING",
                    "sub_topics": ["business", "proposal"],
                    "confidence": "high",
                    "keywords": ["proposal", "business", "client"]
                },
                "intent_classification": {
                    "primary": "DOING",
                    "detailed": "doing_creation",
                    "confidence": "high",
                    "used_assistant_response": False
                },
                "quality_analysis": {
                    "overall_score": 7.5,
                    "quality_level": "good",
                    "has_clear_role": False,
                    "has_context": True,
                    "has_clear_goal": True,
                    "clarity_score": 8.0,
                    "specificity_score": 7.0,
                    "completeness_score": 7.5,
                    "needs_clarification": False,
                    "ambiguity_level": "low",
                    "missing_elements": ["role definition"],
                    "improvement_suggestions": ["Define the AI's role explicitly"]
                },
                "pii_detection": {
                    "has_pii": False,
                    "pii_types": [],
                    "risk_level": "none",
                    "entities": [],
                    "redacted_content": None
                },
                "overall_confidence": 0.85,
                "used_assistant_response": False,
                "model_used": "gemma-9b",
                "cache_hit": False
            }
        }