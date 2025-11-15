# core/pubsub.py
"""
Google Cloud Pub/Sub client
"""
from google.cloud import pubsub_v1
from config import settings
import json
import logging

logger = logging.getLogger(__name__)


class PubSubClient:
    """Pub/Sub client wrapper"""
    
    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.topic_path = self.publisher.topic_path(
            settings.GCP_PROJECT_ID,
            settings.PUBSUB_TOPIC
        )
        self.subscription_path = self.subscriber.subscription_path(
            settings.GCP_PROJECT_ID,
            settings.PUBSUB_SUBSCRIPTION
        )
        logger.info("PubSub client initialized")
    
    async def publish(self, message: dict) -> str:
        """Publish message to topic"""
        try:
            data = json.dumps(message).encode('utf-8')
            future = self.publisher.publish(self.topic_path, data)
            message_id = future.result()
            logger.debug(f"Published message: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"PubSub publish error: {e}")
            raise