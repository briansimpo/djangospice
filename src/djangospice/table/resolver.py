
from __future__ import annotations


from .factory import create_table_class
from .fields import TableField


class TableResolver:
    """Resolve a model and its django-tables2 table class."""

    def __init__(
        self,
        *,
        model=None,
        table_class=None,
        fields=None,
        exclude=None,
    ):
        self.model = model
        self.table_class = table_class
        self.fields = fields
        self.exclude = exclude

    def get_fields(self):
        if self.fields is None:
            return None

        fields = self.fields

        if isinstance(fields, (str, TableField)):
            fields = (fields,)

        return tuple(
            TableField.normalize(item)
            for item in fields
        )

    def resolve(self):
        table_class = self.table_class

        model = self.model

        if model is None and table_class is not None:
            model = getattr(
                getattr(table_class, "Meta", None),
                "model",
                None,
            )

        if model is None:
            raise ValueError("A model or table_class is required.")

        if table_class is None:
            table_class = create_table_class(
                model=model,
                fields=self.get_fields(),
                exclude=self.exclude,
            )

        return table_class, model

    def get_table_class(self):
        return self.resolve()[0]

    def get_model(self):
        return self.resolve()[1]