from typing import ClassVar

from djangospice.exec.dispatchers import (
    Dispatcher,
    MethodDispatcher,
    UnknownDispatcher,
)
from djangospice.exec.views import ExecutableView

from .dispatchers import HttpDispatcher


class WidgetView(ExecutableView):

    dispatchers: ClassVar[tuple[type[Dispatcher], ...]] = (
        MethodDispatcher,
        HttpDispatcher,
        UnknownDispatcher,
    )