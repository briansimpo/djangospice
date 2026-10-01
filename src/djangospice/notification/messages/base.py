from dataclasses import  dataclass, field
from typing import Any
from django.template.loader import render_to_string
from djangospice.core.serializable import Serializable


@dataclass(slots=True, kw_only=True)
class Message(Serializable):
    """
    Base message payload.
    
    Attributes:
        template (str | None): Optional template name for rendering the message.
        context (dict[str, Any]): Context variables for template rendering.
        metadata (dict[str, Any]): Additional arbitrary metadata payload.
    """
    template: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any]= field(default_factory=dict)
    
    def render(self) -> None:
        """
        If a template is provided, render it into the appropriate fields 
        (e.g., text, body, subject) using the stored context.
        """
        if self.template:
            # Logic: Render the template and inject it into the message object.
            # We assume the template returns a JSON string or we parse attributes.
            rendered_content = render_to_string(self.template, self.context)
            # You would parse this content here or assign it to specific fields
            self.metadata["content"] = rendered_content


