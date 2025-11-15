# utils/monitoring.py (modified for local development)
"""
Monitoring and metrics utilities
"""
import time
import asyncio
from functools import wraps
from typing import Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)

# Try to import GCP monitoring, but don't fail if not available
try:
    from google.cloud import monitoring_v3
    from google.cloud import logging as gcp_logging
    GCP_MONITORING_AVAILABLE = True
except ImportError:
    GCP_MONITORING_AVAILABLE = False
    logger.warning("GCP monitoring not available. Using local logging only.")

# Global clients
metrics_client = None
logging_client = None


def setup_monitoring():
    """Setup monitoring clients"""
    global metrics_client, logging_client
    
    if GCP_MONITORING_AVAILABLE and settings.GCP_PROJECT_ID != "local-project":
        try:
            metrics_client = monitoring_v3.MetricServiceClient()
            logging_client = gcp_logging.Client()
            logger.info("Monitoring clients initialized")
        except Exception as e:
            logger.warning(f"Monitoring setup failed: {e}")
    else:
        logger.info("Using local monitoring only")


def track_metric(name: str, value: float, labels: Dict[str, str] = None):
    """Track a custom metric"""
    # For local development, just log the metric
    logger.debug(f"Metric: {name}={value} labels={labels}")
    
    if not metrics_client:
        return
    
    try:
        project_name = f"projects/{settings.GCP_PROJECT_ID}"
        
        series = monitoring_v3.TimeSeries()
        series.metric.type = f"custom.googleapis.com/{name}"
        
        if labels:
            for key, val in labels.items():
                series.metric.labels[key] = val
        
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        interval = monitoring_v3.TimeInterval(
            {"end_time": {"seconds": seconds, "nanos": nanos}}
        )
        point = monitoring_v3.Point(
            {"interval": interval, "value": {"double_value": value}}
        )
        series.points = [point]
        
        metrics_client.create_time_series(
            name=project_name,
            time_series=[series]
        )
    except Exception as e:
        logger.error(f"Failed to track metric {name}: {e}")


def log_event(event_name: str, data: Dict[str, Any]):
    """Log a structured event"""
    # For local development, just use standard logging
    logger.info(f"Event: {event_name} data={data}")
    
    if not logging_client:
        return
    
    try:
        cloud_logger = logging_client.logger("enrichment-service")
        cloud_logger.log_struct({
            "event": event_name,
            "service": settings.SERVICE_NAME,
            "environment": settings.ENVIRONMENT,
            **data
        })
    except Exception as e:
        logger.error(f"Failed to log event {event_name}: {e}")


def measure_time(metric_name: str):
    """Decorator to measure function execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                track_metric(f"{metric_name}_duration_ms", duration)
                return result
            except Exception as e:
                track_metric(f"{metric_name}_errors", 1)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                track_metric(f"{metric_name}_duration_ms", duration)
                return result
            except Exception as e:
                track_metric(f"{metric_name}_errors", 1)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator