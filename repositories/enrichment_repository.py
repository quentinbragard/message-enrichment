# repositories/enrichment_repository.py
"""
Enrichment repository for storing results
"""
from typing import Optional, Dict, List
from datetime import datetime
from core import supabase
import logging

logger = logging.getLogger(__name__)


class EnrichmentRepository:
    """Repository for enrichment results"""
    
    @staticmethod
    async def save(enrichment_result: Dict) -> bool:
        """Save enrichment result to database"""
        try:
            response = supabase.table("message_enrichments")\
                .upsert(enrichment_result)\
                .execute()
            return bool(response.data)
        except Exception as e:
            logger.error(f"Error saving enrichment: {e}")
            return False
    
    @staticmethod
    async def get_by_message_id(message_id: str) -> Optional[Dict]:
        """Get enrichment by message ID"""
        try:
            response = supabase.table("message_enrichments")\
                .select("*")\
                .eq("message_id", message_id)\
                .single()\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching enrichment for {message_id}: {e}")
            return None
    
    @staticmethod
    async def batch_save(enrichments: List[Dict]) -> int:
        """Save multiple enrichments"""
        try:
            response = supabase.table("message_enrichments")\
                .upsert(enrichments)\
                .execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            logger.error(f"Error batch saving enrichments: {e}")
            return 0
    
    @staticmethod
    async def get_organization_stats(
        organization_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get enrichment statistics for an organization"""
        try:
            response = supabase.table("message_enrichments")\
                .select("*")\
                .eq("organization_id", organization_id)\
                .gte("created_at", start_date.isoformat())\
                .lte("created_at", end_date.isoformat())\
                .execute()
            
            if not response.data:
                return {}
            
            # Calculate statistics
            total = len(response.data)
            work_count = sum(1 for r in response.data if r.get("is_work"))
            
            return {
                "total_messages": total,
                "work_percentage": (work_count / total * 100) if total > 0 else 0,
                "avg_quality_score": sum(r.get("quality_score", 0) for r in response.data) / total if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error fetching org stats: {e}")
            return {}