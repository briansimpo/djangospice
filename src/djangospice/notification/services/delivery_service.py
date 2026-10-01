import logging
from typing import Any
from django.db import transaction

from djangospice.notification.enums import Channel
from djangospice.notification.models import  NotificationDelivery
from djangospice.notification.registry import ChannelRegistry

logger = logging.getLogger(__name__)


class DeliveryService:
    """
    Executes notification deliveries and manages delivery lifecycle,
    bridging the database state with domain events.
    """

    @classmethod
    def process(cls, delivery_id: Any) -> None:
        # Lock delivery row to prevent race conditions from task retries
        with transaction.atomic():
            delivery = (
                NotificationDelivery.objects.select_for_update()
                .select_related("notification__recipient")
                .get(pk=delivery_id)
            )

            # Idempotency check
            if delivery.is_sent() or delivery.is_processing():
                return

            provider = ChannelRegistry.get_provider(Channel(delivery.channel))
            if provider is None:
                raise RuntimeError(f"No provider registered for '{delivery.channel}'.")

            delivery.mark_processing()

        # Outside transaction: network I/O starts here
        try:
            response = provider.send(
                user=delivery.notification.recipient,
                notification=delivery.notification
            )
            delivery.mark_sent(metadata=response)

        except Exception as ex:
            logger.exception("Notification delivery %s failed.", delivery.pk)
            delivery.mark_failed(error=ex)
            
            # Let Celery/Broker handle the retry backoff
            raise
