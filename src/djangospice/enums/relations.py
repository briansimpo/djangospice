from django.db import models
from django.utils.translation import gettext_lazy as _


class RelationType(models.TextChoices):
    PARENT = "parent", _("Parent")
    CHILD = "child", _("Child")
    SPOUSE = "spouse", _("Spouse")
    SIBLING = "sibling", _("Sibling")
    GRANDPARENT = "grandparent", _("Grandparent")
    GRANDCHILD = "grandchild", _("Grandchild")
    RELATIVE = "relative", _("Relative")
    FRIEND = "friend", _("Friend")
    COLLEAGUE = "colleague", _("Colleague")
    EMPLOYER = "employer", _("Employer")
    EMPLOYEE = "employee", _("Employee")
    CUSTOMER = "customer", _("Customer")
    SUPPLIER = "supplier", _("Supplier")
    PARTNER = "partner", _("Partner")
    REPRESENTATIVE = "representative", _("Representative")
    GUARDIAN = "guardian", _("Guardian")
    DEPENDENT = "dependent", _("Dependent")
    OTHER = "other", _("Other")