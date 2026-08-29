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



class RowActionsColumn(tables.TemplateColumn):
    """
    django-tables2 column for TableWidget row actions.
    """

    def __init__(self,*args, **kwargs):
        super().__init__(
            template_name = "djangospice/table/columns/actions.html",
            *args,
            **kwargs,
        )

    def render(self, record, table, value, bound_column, **kwargs):
        widget = table.widget

        return super().render(
            record,
            table,
            value,
            bound_column,
            actions=widget.get_bound_row_actions(record),
            **kwargs,
        )