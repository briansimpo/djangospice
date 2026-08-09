from .notifier import Notifier
from .base import BaseNotification


class Notifiable:

    def notify(self, notification: BaseNotification):
        return Notifier.send(
            users=self, 
            notification=notification
        )
    

