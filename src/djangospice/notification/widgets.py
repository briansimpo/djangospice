from djangospice.widget import Widget, widget
from djangospice.templates import get_template_name

from .apps import namespace


@widget
class NotificationWidget(Widget):
    template_name = get_template_name("widgets/notification.html", namespace)
    lazy = True

    def get_context(self):
        context = super().get_context()
        notifications = self.user.notifications.unread()

        unread_count = notifications.count()
        unread_list = list(notifications)
    
        payload = {
            "unread_count": unread_count,
            "unread_list": unread_list,
        }

        context.update(payload)
        
        return context


