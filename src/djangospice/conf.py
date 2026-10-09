from django.conf import settings


class DjangospiceSettings:
    """Central configuration for Djangospice."""

    DEFAULTS = {
        "URL": "djangospice/",
    }

    @property
    def URL(self) -> str:
        return getattr(
            settings,
            "DJANGOSPICE_URL",
            self.DEFAULTS["URL"],
        )


djangospice_settings = DjangospiceSettings()