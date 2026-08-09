from django.http import HttpRequest
from djangospice.response.response import Response

from djangospice.widgets.widget import Widget
from djangospice.widgets.exceptions import DispatcherNotFound

from .dispatchers import ActionDispatcher, MethodDispatcher


class WidgetExecutor:
    """
    Executes a widget request.
    """

    dispatchers = (
        ActionDispatcher,
        MethodDispatcher,
    )

    def __init__(self, widget: Widget, request: HttpRequest) -> None:

        self.widget = widget
        self.request = request
        self.widget.request = request

    def execute(self) -> Response:

        self.widget.initialize()

        self.widget.configure()

        self.widget.configure_htmx()

        self.widget.authorize()

        return self.dispatch()

    def dispatch(self) -> Response:

        for dispatcher_cls in self.dispatchers:

            dispatcher = dispatcher_cls(
                self.widget,
                self.request,
            )

            if dispatcher.can_dispatch():
                return dispatcher.dispatch()

        raise DispatcherNotFound()