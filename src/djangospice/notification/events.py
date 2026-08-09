from dataclasses import dataclass
from djangospice.events import BaseEvent
from djangospice.notification.models import Notification


@dataclass
class NotificationRecordCreated(BaseEvent):
    notification: Notification
    
