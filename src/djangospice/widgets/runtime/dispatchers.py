from abc import ABC, abstractmethod
from django.http import HttpRequest

from djangospice.response.response import Response

from djangospice.widgets.widget import Widget
from djangospice.widgets.actions.context import ActionContext


class BaseDispatcher(ABC):
    
    def __init__(self, widget: Widget, request: HttpRequest):
        self.widget = widget
        self.request = request
        
    @abstractmethod
    def can_dispatch(self) -> bool:
        pass
    
    @abstractmethod
    def dispatch(self) -> Response:
        pass
    
    
class ActionDispatcher(BaseDispatcher):
    """
    Dispatches widget actions.
    """

    parameter = "action"

    def can_dispatch(self) -> bool:
        return self.parameter in self.request.GET or self.parameter in self.request.POST

    def dispatch(self) -> Response:

        name = (
            self.request.POST.get(self.parameter)
            or self.request.GET.get(self.parameter)
        )

        action = self.widget.actions.require(name)

        context = ActionContext(
            widget=self.widget,
            request=self.request,
            object=self.widget.get_object(),
            objects=self.widget.get_objects(),
            data=self.widget.get_data(),
        )

        return action.dispatch(context)
    

class MethodDispatcher(BaseDispatcher):
    """
    Dispatches HTTP methods.
    """

    def can_dispatch(self) -> bool:
        return True

    def dispatch(self) -> Response:

        handler = getattr(self.widget, self.request.method.lower(), None)

        if handler is None:
            return self.widget.method_not_allowed()

        return handler()