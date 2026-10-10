from django.conf import settings


class DjangospiceSettings:
    """Central configuration for Djangospice."""

    DEFAULTS = {
        "DJANGOSPICE_URL": "djangospice/",
    }

    @property
    def DJANGOSPICE_URL(self) -> str:
        return getattr(
            settings,
            "DJANGOSPICE_URL",
            self.DEFAULTS["DJANGOSPICE_URL"],
        )


djangospice_settings = DjangospiceSettings()