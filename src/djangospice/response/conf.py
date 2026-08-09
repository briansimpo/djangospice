from django.conf import settings
from .defaults import DEFAULT_RENDERERS


class ResponseSettings:
    """
    Response framework settings.
    """

    @property
    def RENDERERS(self):
        """
        Merge developer renderers with framework defaults.

        User-defined renderers override built-in ones.
        """
        renderers = DEFAULT_RENDERERS.copy()

        renderers.update(
            getattr(settings, "RESPONSE_RENDERERS", {})
        )

        return renderers


response_settings = ResponseSettings()