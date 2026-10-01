from typing import Any
from functools import partial
from django.db import transaction

from .tasks import deliver_notification

class CeleryAdapter:

    def dispatch(self, delivery_id: Any) -> None:
        
        transaction.on_commit(
            partial(deliver_notification.delay, delivery_id)
        )