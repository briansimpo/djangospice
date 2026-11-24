from django.db import models
from django.utils.translation import gettext_lazy as _


class Weekday(models.TextChoices):
    MONDAY = "monday", _("Monday")
    TUESDAY = "tuesday", _("Tuesday")
    WEDNESDAY = "wednesday", _("Wednesday")
    THURSDAY = "thursday", _("Thursday")
    FRIDAY = "friday", _("Friday")
    SATURDAY = "saturday", _("Saturday")
    SUNDAY = "sunday", _("Sunday")


class Month(models.TextChoices):
    JANUARY = "january", _("January")
    FEBRUARY = "february", _("February")
    MARCH = "march", _("March")
    APRIL = "april", _("April")
    MAY = "may", _("May")
    JUNE = "june", _("June")
    JULY = "july", _("July")
    AUGUST = "august", _("August")
    SEPTEMBER = "september", _("September")
    OCTOBER = "october", _("October")
    NOVEMBER = "november", _("November")
    DECEMBER = "december", _("December")


class Recurrence(models.TextChoices):
    ONCE = "once", _("Once")
    DAILY = "daily", _("Daily")
    WEEKLY = "weekly", _("Weekly")
    MONTHLY = "monthly", _("Monthly")
    YEARLY = "yearly", _("Yearly")