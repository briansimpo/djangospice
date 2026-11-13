
import django_tables2 as tables
from django.utils.formats import number_format


class NumberColumn(tables.Column):
    def render(self, value):
        try:
            return number_format(value, use_l10n=True, force_grouping=True)
        except (ValueError, TypeError):
            return value



class TableColumn(tables.Column):
    """
    Base Djangospice column.

    This is intentionally a thin extension of django-tables2.Column.
    """

    pass


class SelectionColumn(tables.CheckBoxColumn):
    """
    Checkbox column for row selection.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("accessor", "pk")
        kwargs.setdefault("orderable", False)

        super().__init__(*args, **kwargs)



