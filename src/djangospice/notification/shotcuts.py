def notify(user, notification):
    from .notifier import Notifier
    Notifier.send(user, notification)