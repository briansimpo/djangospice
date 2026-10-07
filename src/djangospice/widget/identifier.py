from __future__ import annotations


from django.utils.text import slugify


class WidgetIdentifier:
  

    def __init__(self, app_label, widget_name):
        self.app_label = slugify(app_label)
        self.widget_name = slugify(widget_name)
    
    @property
    def key(self) -> str:
        return f"{self.app_label}.{self.widget_name}"

    def __str__(self) -> str:
        return f"{self.app_label}.{self.widget_name}"

    @classmethod
    def from_widget(cls, widget: type) -> WidgetIdentifier:
        return cls(
            app_label=widget.app_label,
            widget_name=widget.name,
        )

    @classmethod
    def from_model(cls, model) -> WidgetIdentifier:
        return cls(
            app_label=model._meta.app_label,
            widget_name=model._meta.model_name,
        )