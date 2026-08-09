from typing import Any
from slugify import slugify 
from tablib import Dataset
from django.db.models import Model


class ModelInspector:
    """Handles Django Meta-programming and dataset extraction logic."""
    @staticmethod
    def get_sheet_name(model: Model) -> str:
        return model._meta.verbose_name_plural.replace(" ", "_")[:31]

    @staticmethod
    def get_file_name(name: str) -> str:
        return f"{slugify(name, separator='-').upper()}.xlsx"

    @staticmethod
    def get_relation_dataset(queryset: Any) -> Dataset:
        dataset = Dataset(headers=["ID", "Value"])
        for index, obj in enumerate(queryset):
            if isinstance(obj, (tuple, list)) and len(obj) >= 2:
                dataset.append([obj[0], str(obj[1])])
            elif hasattr(obj, "pk"):
                dataset.append([obj.pk, str(obj)])
            else:
                dataset.append([index, str(obj)])
        return dataset

