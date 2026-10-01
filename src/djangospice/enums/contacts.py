from django.db import models
from django.utils.translation import gettext_lazy as _


class ContactType(models.TextChoices):
    EMAIL = "email", _("Email")
    PHONE = "phone", _("Phone")
    ADDRESS = "address", _("Address")
    WEBSITE = "website", _("Website")
    SOCIAL_MEDIA = "social_media", _("Social Media")


class ContactChannel(models.TextChoices):
    EMAIL = "email", _("Email")
    PHONE = "phone", _("Phone")
    SMS = "sms", _("SMS")
    FAX = "fax", _("Fax")
    WEB = "web", _("Web")
    SOCIAL_MEDIA = "social_media", _("Social Media")
    POSTAL = "postal", _("Postal")


class ContactUsage(models.TextChoices):
    PERSONAL = "personal", _("Personal")
    BUSINESS = "business", _("Business")
    WORK = "work", _("Work")
    HOME = "home", _("Home")
    EMERGENCY = "emergency", _("Emergency")
    BILLING = "billing", _("Billing")
    SUPPORT = "support", _("Support")
    OTHER = "other", _("Other")


class ContactPreference(models.TextChoices):
    PRIMARY = "primary", _("Primary")
    PREFERRED = "preferred", _("Preferred")
    DO_NOT_CONTACT = "do_not_contact", _("Do Not Contact")