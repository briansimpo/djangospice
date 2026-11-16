
from djangospice.html.component import Component
from .widget import Widget


class WidgetPlaceholder(Component):
    template_name = "widget/placeholder.html"

    def __init__(self, widget: Widget, skeleton=None):
        self.widget = widget

        super().__init__(
            *([skeleton] if skeleton is not None else []),
            request=widget.request,
        )

    def get_context(self):
        return {
            **super().get_context(),
            "target_id": self.widget.id,
            "target_url": self.widget.url,
            "target_title": self.widget.title,
        }