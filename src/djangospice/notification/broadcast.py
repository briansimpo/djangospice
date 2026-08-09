from djangospice.core.payload import Payload
from djangospice.html.fragments import HTMLFragment
from djangospice.notification.models import Notification
from djangospice.realtime.broadcast import Broadcast
from djangospice.web.templates import get_template_name
from djangospice.notification.services import NotificationService
from djangospice.notification.apps import namespace


class NotificationBroadcast:
    
    _COUNT_TEMPLATE = get_template_name("count", namespace)
    _ITEM_TEMPLATE = get_template_name("item", namespace)
    
    @classmethod
    def broadcast(cls, notification: Notification):
    
        unread_count = NotificationService.unread_count(notification.recipient)

        count_html = HTMLFragment(
            template=cls._COUNT_TEMPLATE,
            context=Payload(count=unread_count)
        ).render()
        
        item_html = HTMLFragment(
            template=cls._ITEM_TEMPLATE,
            context=Payload(notification=notification)
        ).render()

        combined_data = count_html+item_html
        
        Broadcast.user(notification.recipient_id, combined_data)