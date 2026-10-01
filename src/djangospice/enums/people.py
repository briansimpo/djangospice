from django.db import models
from django.utils.translation import gettext_lazy as _


class BloodType(models.TextChoices):
    A_POSITIVE = "a_positive", _("A+")
    A_NEGATIVE = "a_negative", _("A-")
    B_POSITIVE = "b_positive", _("B+")
    B_NEGATIVE = "b_negative", _("B-")
    AB_POSITIVE = "ab_positive", _("AB+")
    AB_NEGATIVE = "ab_negative", _("AB-")
    O_POSITIVE = "o_positive", _("O+")
    O_NEGATIVE = "o_negative", _("O-")


class Title(models.TextChoices):
    MISS = "miss", _("Miss")
    MR = "mr", _("Mr")
    MRS = "mrs", _("Mrs")
    MS = "ms", _("Ms")
    DR = "dr", _("Dr")
    PROF = "prof", _("Prof")


class Gender(models.TextChoices):
    MALE = "male", _("Male")
    FEMALE = "female", _("Female")
    NON_BINARY = "non_binary", _("Non-binary")
    PREFER_NOT_TO_SAY = "prefer_not_to_say", _("Prefer not to say")
    OTHER = "other", _("Other")


class IDType(models.TextChoices):
    NATIONAL_ID = "national_id", _("National ID")
    PASSPORT = "passport", _("Passport")
    DRIVING_LICENSE = "driving_license", _("Driving License")
    VOTER_ID = "voter_id", _("Voter ID")
    RESIDENCE_PERMIT = "residence_permit", _("Residence Permit")
    WORK_PERMIT = "work_permit", _("Work Permit")
    BIRTH_CERTIFICATE = "birth_certificate", _("Birth Certificate")
    TAX_ID = "tax_id", _("Tax ID")
    SOCIAL_SECURITY_ID = "social_security_id", _("Social Security ID")
    STUDENT_ID = "student_id", _("Student ID")
    EMPLOYEE_ID = "employee_id", _("Employee ID")
    MILITARY_ID = "military_id", _("Military ID")
    REFUGEE_ID = "refugee_id", _("Refugee ID")
    OTHER = "other", _("Other")


class MaritalStatus(models.TextChoices):
    SINGLE = "single", _("Single")
    MARRIED = "married", _("Married")
    DIVORCED = "divorced", _("Divorced")
    WIDOWED = "widowed", _("Widowed")