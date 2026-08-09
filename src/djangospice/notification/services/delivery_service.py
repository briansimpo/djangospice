import logging
from typing import Any
from django.db import transaction

from djangospice.notification.enums import Channel
from djangospice.notification.models import Notification, NotificationDelivery
from djangospice.notification.registry import ChannelRegistry

logger = logging.getLogger(__name__)


class DeliveryService:
    """
    Executes notification deliveries and manages delivery lifecycle,
    bridging the database state with domain events.
    """

    @classmethod
    def create(cls, notification: Notification, channel: Channel) -> NotificationDelivery:
        delivery = NotificationDelivery.objects.create(
            notification=notification,
            channel=channel
        )

        return delivery

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

            cls.mark_processing(delivery)

        # Outside transaction: network I/O starts here
        try:
            response = provider.send(
                user=delivery.notification.recipient,
                notification=delivery.notification,
                delivery=delivery,
            )
            cls.mark_success(delivery, metadata=response)

        except Exception as ex:
            logger.exception("Notification delivery %s failed.", delivery.pk)
            cls.mark_failure(delivery, error=ex)
            
            # Let Celery/Broker handle the retry backoff
            raise

    @classmethod
    def mark_processing(cls, delivery: NotificationDelivery) -> None:
        # Delegate state mutation to the model
        delivery.mark_processing()

    @classmethod
    def mark_success(cls, delivery: NotificationDelivery, metadata: dict[str, Any] | None = None) -> None:
        # Delegate state mutation to the model
        delivery.mark_sent(metadata=metadata)


    @classmethod
    def mark_failure(cls, delivery: NotificationDelivery, error: Exception | str) -> None:
        # Delegate state mutation to the model
        delivery.mark_failed(error=error)

