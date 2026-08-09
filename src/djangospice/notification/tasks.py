import logging
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from .services import DeliveryService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=5)
def deliver_notification(self, delivery_id):
    try:
        DeliveryService.process(delivery_id)
    except Exception as exc:
        logger.warning(f"Delivery {delivery_id} failed. Retrying... Error: {exc}")
        try:
            # Exponential backoff: 2s, 4s, 8s, 16s, 32s
            countdown = 2 ** self.request.retries
            self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            # Update the database to FAILED only when all retries are exhausted
            DeliveryService.mark_failure(delivery_id, str(exc))
            raise