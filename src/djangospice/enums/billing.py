from django.db import models
from django.utils.translation import gettext_lazy as _


class PricingBasis(models.TextChoices):
    FLAT = "flat", _("Flat")
    UNIT = "unit", _("Per Unit")


class PricingUnit(models.TextChoices):
    USER = "user", _("User")
    MODULE = "module", _("Module")
    SERVICE = "service", _("Service")
    ITEM = "item", _("Item")


class BillingTiming(models.TextChoices):
    PREPAID = "prepaid", _("Prepaid")
    POSTPAID = "postpaid", _("Postpaid")


class BillingPeriod(models.TextChoices):
    ONE_TIME = "one_time", _("One Time")
    MONTHLY = "monthly", _("Monthly")
    QUARTERLY = "quarterly", _("Quarterly")
    TRIMESTERLY = "trimesterly", _("Trimesterly")
    SEMESTERLY = "semesterly", _("Semesterly")
    YEARLY = "yearly", _("Yearly")