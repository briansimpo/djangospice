import logging
from celery import shared_task
from .services import DeliveryService

logger = logging.getLogger(__name__)

@shared_task
def deliver_notification(delivery_id):
    DeliveryService.process(delivery_id)
  