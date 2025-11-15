# workers/pubsub_handler.py
"""
Pub/Sub message handler
"""
import json
from typing import Optional, Dict
from google.cloud import pubsub_v1
from google.api_core import retry
from config import settings
import logging

logger = logging.getLogger(__name__)


class PubSubHandler:
    """Handle Pub/Sub operations for the worker"""
    
    def __init__(self):
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(
            settings.GCP_PROJECT_ID,
            settings.PUBSUB_SUBSCRIPTION
        )
    
    async def pull_message(self) -> Optional[Dict]:
        """Pull a single message from Pub/Sub"""
        try:
            # Pull with immediate return
            response = self.subscriber.pull(
                request={
                    "subscription": self.subscription_path,
                    "max_messages": 1,
                    "return_immediately": True
                },
                retry=retry.Retry(deadline=10)
            )
            
            if not response.received_messages:
                return None
            
            # Get the message
            message = response.received_messages[0]
            
            # Parse message data
            data = json.loads(message.message.data.decode('utf-8'))
            
            # Acknowledge the message
            self.subscriber.acknowledge(
                request={
                    "subscription": self.subscription_path,
                    "ack_ids": [message.ack_id]
                }
            )
            
            logger.debug(f"Pulled message: {message.message.message_id}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to pull message: {e}")
            return None
    
    async def nack_message(self, ack_id: str):
        """Negative acknowledge a message (for retry)"""
        try:
            self.subscriber.modify_ack_deadline(
                request={
                    "subscription": self.subscription_path,
                    "ack_ids": [ack_id],
                    "ack_deadline_seconds": 0
                }
            )
            logger.debug(f"Nacked message: {ack_id}")
        except Exception as e:
            logger.error(f"Failed to nack message: {e}")