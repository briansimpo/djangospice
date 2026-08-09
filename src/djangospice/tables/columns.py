import django_tables2 as tables
from django_tables2.columns import CheckBoxColumn as BaseCheckBoxColumn
from django.utils.formats import number_format


class CheckBoxColumn(BaseCheckBoxColumn):
    def __init__(self, attrs=None, checked=None, **extra):
        attrs = {"th__input": {"name": "selectall", "class": "selectall"}}
        super().__init__(attrs, checked, **extra)


class NumberColumn(tables.Column):
    def render(self, value):
        try:
            return number_format(value, use_l10n=True, force_grouping=True)
        except (ValueError, TypeError):
            return value