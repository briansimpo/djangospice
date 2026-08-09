from dataclasses import  dataclass, field
from django.template.loader import render_to_string
from djangospice.core.serializable import Serializable
from djangospice.core.payload import Payload


@dataclass(slots=True, kw_only=True)
class Message(Serializable):
    """
    Base message payload.
    
    Attributes:
        template (str | None): Optional template name for rendering the message.
        payload (dict[str, Any]): Payload variables for template rendering.
        metadata (dict[str, Any]): Additional arbitrary metadata payload.
    """
    template: str | None = None
    payload: Payload = field(default_factory=Payload)
    metadata: Payload= field(default_factory=Payload)
    
    def render(self) -> None:
        """
        If a template is provided, render it into the appropriate fields 
        (e.g., text, body, subject) using the stored context.
        """
        if self.template:
            # Logic: Render the template and inject it into the message object.
            # We assume the template returns a JSON string or we parse attributes.
            rendered_content = render_to_string(self.template, self.payload)
            # You would parse this content here or assign it to specific fields
            self.metadata["content"] = rendered_content


