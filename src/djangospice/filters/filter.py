import django_filters

from django.db import models

from .fields import LookupChoiceFilter, LookupMultipleChoiceFilter


class OptionFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    value = django_filters.CharFilter(field_name="value", lookup_expr="icontains")
    slug = django_filters.CharFilter(field_name="slug", lookup_expr="icontains")
    code = django_filters.CharFilter(field_name="code", lookup_expr="icontains")

    class Meta:
        model = None  # to be defined in subclass
        fields = ["id", "name", "value", "slug", "code"]


class DynamicFilter(django_filters.FilterSet):

    @classmethod
    def filter_for_lookup(cls, field, lookup_type):

        filter_class, params = super().filter_for_lookup(
            field,
            lookup_type,
        )

        if isinstance(field, models.ManyToManyField):
            filter_class = LookupMultipleChoiceFilter

        elif isinstance(
            field,
            (models.ForeignKey, models.OneToOneField),
        ):
            filter_class = LookupChoiceFilter

        return filter_class, params