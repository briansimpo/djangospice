def notify(user, title, body, template=None, context=None):
    from .default import DefaultNotification
    from .notifier import Notifier

    notification = DefaultNotification(
        title=title,
        body=body,
        template=template,
        context=context
    )

    return Notifier.send(user, notification)