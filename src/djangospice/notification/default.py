from .base import Notification
from .messages import DatabaseMessage


class DefaultNotification(Notification):

    def __init__(self, title, body, template=None, context=None):
        self.title = title
        self.body = body
        self.template = template
        self.context = context

    def to_database(self, user):
        return DatabaseMessage(
            template=self.template,
            context=self.context,
            title=self.title,
            body=self.body
        )