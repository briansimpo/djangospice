from typing import Union, List
from djangospice.core.payload import Payload
from djangospice.html.fragments import HTMLFragment
from djangospice.realtime.broadcast import Broadcast
from djangospice.web.templates import get_template_name
from djangospice.notification.apps import namespace

class Alert:
    _TEMPLATE = get_template_name("alert", namespace)

    @classmethod
    def _get_user_id(cls, user_or_id: Union[int, object]) -> int:
        """Helper to extract ID from model instances or primitive IDs."""
        return getattr(user_or_id, 'id', getattr(user_or_id, 'pk', user_or_id))
    
    @classmethod
    def get_template_name(cls) -> str:
        """Returns the cached, verified template path."""
        return cls._TEMPLATE
    
    @classmethod
    def send(cls, user_or_id: Union[int, object], message: str, tags: str = "info"):
        payload = Payload(tags=tags, message=message)
        data = cls.fragment(messages=[payload], oob=True).render()
        Broadcast.user(user=cls._get_user_id(user_or_id), data=data)

    @classmethod
    def fragment(cls, messages: Union[Payload, List[Payload]], oob: bool = True) -> HTMLFragment:
        if not isinstance(messages, (list, tuple)):
            messages = [messages]

        return HTMLFragment(
            template=cls._TEMPLATE,
            context=Payload(messages=messages, oob=oob)
        )

    @classmethod
    def success(cls, user_id, message): 
        cls.send(user_id, message, "success")
        
    @classmethod
    def error(cls, user_id, message):   
        cls.send(user_id, message, "error")
        
    @classmethod
    def warning(cls, user_id, message): 
        cls.send(user_id, message, "warning")
        
    @classmethod
    def info(cls, user_id, message):    
        cls.send(user_id, message, "info")