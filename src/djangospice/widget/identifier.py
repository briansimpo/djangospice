from __future__ import annotations

from dataclasses import dataclass
from django.utils.text import slugify



@dataclass(frozen=True, slots=True)
class WidgetIdentifier:
    """
    Canonical identity of a registered lookup.
    """

    app_name: str
    widget_name: str

    def __post_init__(self) -> None:
        app_name = slugify(self.app_name)
        widget_name = slugify(self.widget_name)
            
        if not app_name:
            raise ValueError("Lookup app_name cannot be empty.")

        if not widget_name:
            raise ValueError("Lookup widget_name cannot be empty.")

        object.__setattr__(self, "app_name", app_name)
        object.__setattr__(self, "widget_name", widget_name)

    @property
    def key(self):
        return f"{self.app_name}.{self.widget_name}"

    def __str__(self) -> str:
        return self.key

  
    @classmethod
    def from_widget(cls, widget: type) -> WidgetIdentifier:
        return cls(
            app_name=widget.app_name,
            widget_name=widget.name,
        )

    @classmethod
    def from_model(cls, model) -> WidgetIdentifier:
        return cls(
            app_name=model._meta.app_label,
            widget_name=model._meta.model_name,
        )