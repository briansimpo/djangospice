from django.db import models
from django.utils.translation import gettext_lazy as _


class DataType(models.TextChoices):
    TEXT = "text", _("Text")
    INTEGER = "integer", _("Integer")
    DECIMAL = "decimal", _("Decimal")
    BOOLEAN = "boolean", _("Boolean")

    DATE = "date", _("Date")
    DATETIME = "datetime", _("Date & Time")
    TIME = "time", _("Time")

    EMAIL = "email", _("Email")
    URL = "url", _("URL")
    UUID = "uuid", _("UUID")

    JSON = "json", _("JSON")

    FILE = "file", _("File")
    IMAGE = "image", _("Image")