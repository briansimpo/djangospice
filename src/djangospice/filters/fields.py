import django_filters

from djangospice.forms.fields import LookupChoiceField,LookupMultipleChoiceField


class LookupChoiceFilter(django_filters.ModelChoiceFilter):
    field_class = LookupChoiceField


class LookupMultipleChoiceFilter(django_filters.ModelMultipleChoiceFilter):
    field_class = LookupMultipleChoiceField