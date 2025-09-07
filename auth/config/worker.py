from celery import Celery
from auth.config.database import db_settings
from auth.logger.log import logger
from celery.signals import worker_ready, worker_shutdown, task_prerun, task_postrun, task_failure
"""Celery configuration for Auth system background task processing"""

try:
    # Initialize Celery application with Redis broker and backend
    celery_app = Celery(
        "auth_notifications",
        broker=db_settings.REDIS_URL(0),  # Use Redis DB 0 for message broker
        backend=db_settings.REDIS_URL(1),  # Use Redis DB 1 for results backend
        broker_connection_retry_on_startup=True,  # Auto-retry broker connections
    )
    logger("Auth", "Worker", "INFO", "null", "Celery app initialized successfully")
except Exception as e:
    logger("Auth", "Worker", "ERROR", "CRITICAL", f"Celery app initialization failed: {str(e)}")
    raise

# Production-ready Celery configuration settings
try:
    celery_app.conf.update(
        # Serialization settings for security and performance
        task_serializer='json',          # Use JSON for task serialization
        accept_content=['json'],         # Only accept JSON content
        result_serializer='json',        # Use JSON for result serialization
        
        # Timezone and UTC settings
        timezone='UTC',                  # Use UTC timezone
        enable_utc=True,                # Enable UTC for all timestamps
        
        # Task tracking and monitoring
        task_track_started=True,        # Track when tasks start execution
        
        # Task timeout settings for reliability
        task_time_limit=30 * 60,        # Hard timeout: 30 minutes
        task_soft_time_limit=25 * 60,   # Soft timeout: 25 minutes (allows cleanup)
        
        # Worker performance settings
        worker_prefetch_multiplier=1,   # Prefetch one task at a time for better distribution
        worker_max_tasks_per_child=1000, # Restart worker after 1000 tasks (memory management)
        
        # Task routing and delivery settings
        task_default_queue='celery',    # Default queue name
        task_default_exchange='celery', # Default exchange name
        task_default_routing_key='celery', # Default routing key
        
        # Result backend settings
        result_expires=3600,            # Results expire after 1 hour
        result_persistent=True,         # Persist results to backend
        
        # Error handling
        task_reject_on_worker_lost=True, # Reject tasks if worker is lost
        task_acks_late=True,            # Acknowledge tasks after completion
    )
    logger("Auth", "Worker", "INFO", "null", "Celery configuration updated successfully")
except Exception as e:
    logger("Auth", "Worker", "ERROR", "CRITICAL", f"Celery configuration failed: {str(e)}")
    raise

# Auto-discover and register tasks from notification services
try:
    celery_app.autodiscover_tasks(['auth.services.notifications'])
    logger("Auth", "Worker", "INFO", "null", "Celery task autodiscovery completed for notifications")
except Exception as e:
    logger("Auth", "Worker", "ERROR", "CRITICAL", f"Celery task autodiscovery failed: {str(e)}")
    raise


# Celery event handlers for monitoring and logging
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery worker functionality"""
    try:
        logger("Auth", "Worker", "INFO", "null", f"Debug task executed: {self.request!r}")
        return f"Debug task completed: {self.request.id}"
    except Exception as e:
        logger("Auth", "Worker", "ERROR", "ERROR", f"Debug task failed: {str(e)}")
        raise




@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Log when Celery worker is ready to accept tasks"""
    logger("Auth", "Worker", "INFO", "null", f"Celery worker ready: {sender}")

@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Log when Celery worker is shutting down"""
    logger("Auth", "Worker", "INFO", "null", f"Celery worker shutting down: {sender}")

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Log before task execution starts"""
    logger("Auth", "Worker", "INFO", "null", f"Task starting: {task.name} [{task_id}]")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Log after task execution completes"""
    logger("Auth", "Worker", "INFO", "null", f"Task completed: {task.name} [{task_id}] - State: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Log when task execution fails"""
    logger("Auth", "Worker", "ERROR", "HIGH", f"Task failed: {sender.name} [{task_id}] - Error: {str(exception)}")


logger("Auth", "Worker", "INFO", "null", "Celery worker configuration completed successfully")