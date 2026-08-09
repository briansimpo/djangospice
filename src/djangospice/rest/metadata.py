from rest_framework.metadata import SimpleMetadata
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import filters as df_filters
from django.db import models


class ModelResolver:
    @staticmethod
    def resolve_field(model, path: str):
        """
        Return the final related model and the final field for a nested path.
        """
        parts = path.split("__")
        related_model = model
        last_field = None
        try:
            for part in parts:
                field = related_model._meta.get_field(part)
                last_field = field
                if hasattr(field, "related_model"):
                    related_model = field.related_model
        except Exception:
            related_model = None
            last_field = None
        return related_model, last_field

    @staticmethod
    def get_depends_on(path: str):
        parts = path.split("__")
        return parts[0] if len(parts) > 1 else None

    @staticmethod
    def get_depends_chain(path: str):
        parts = path.split("__")
        return parts[:-1] if len(parts) > 1 else []


class MetadataHelper:
    """
    Shared utilities for metadata:
    - FK / M2M / Choice detection
    - dependency attachment
    - small dataset preloading
    - smart nested URL generation
    """
    PRELOAD_LIMIT = 100

    @classmethod
    def detect_type(cls, obj, related_model=None, last_field=None):
        if related_model and isinstance(last_field, (models.ForeignKey, models.ManyToManyField)):
            return "foreignkey" if isinstance(last_field, models.ForeignKey) else "manytomany"
        if isinstance(obj, (df_filters.ModelChoiceFilter, df_filters.ModelMultipleChoiceFilter, serializers.PrimaryKeyRelatedField)):
            return "foreignkey"
        if isinstance(obj, (df_filters.ChoiceFilter, serializers.ChoiceField)):
            return "choice"
        if isinstance(obj, (df_filters.NumberFilter, df_filters.RangeFilter,
                            serializers.IntegerField, serializers.FloatField, serializers.DecimalField)):
            return "number"
        if isinstance(obj, (df_filters.BooleanFilter, serializers.BooleanField)):
            return "boolean"
        return "string"

    @classmethod
    def attach_fk_m2m_or_choice_info(cls, data, obj, related_model=None, nested_path=None, base_model=None):
        """
        Attach FK / M2M / Choice info, preload small datasets,
        and generate smart nested URLs.
        """
        # Relational fields
        if data["type"] in ["foreignkey", "manytomany"]:
            model = related_model or getattr(getattr(obj, "queryset", None), "model", None)
            if model:
                data["model"] = model._meta.label
                data["related_url"] = cls._generate_smart_nested_url(base_model or model, nested_path)
                try:
                    if hasattr(model.objects, "count") and model.objects.count() <= cls.PRELOAD_LIMIT:
                        data["use_choices"] = True
                        data["choices"] = [{"value": str(o.pk), "label": str(o)} for o in model.objects.all()]
                    else:
                        data["use_choices"] = False
                except Exception:
                    pass

        elif data["type"] == "choice":
            raw_choices = getattr(obj, "choices", None) or getattr(getattr(obj, "extra", {}), "get", lambda k, d=None: [])("choices", [])
            
            formatted_choices = []

            def flatten(choices):
                for c in choices:
                    if isinstance(c, (list, tuple)):
                        # Grouped choices? e.g. (group_name, [(value, label), ...])
                        if len(c) == 2 and isinstance(c[1], (list, tuple)):
                            flatten(c[1])
                        elif len(c) == 2:
                            formatted_choices.append({"value": c[0], "label": c[1]})
                        else:
                            formatted_choices.append({"value": c, "label": str(c)})
                    else:
                        formatted_choices.append({"value": c, "label": str(c)})

            flatten(raw_choices)

            if formatted_choices:
                data["choices"] = formatted_choices

    @classmethod
    def _generate_smart_nested_url(cls, model, nested_path=None):
        """
        Resolves the final related model for a nested field path and returns a
        smart URL pattern with app_name/model_name.
        """
        if not model:
            return "/"

        current_model = model

        if nested_path:
            parts = nested_path.split("__")
            for part in parts:
                try:
                    field = current_model._meta.get_field(part)
                    if hasattr(field, "related_model") and field.related_model:
                        current_model = field.related_model
                except Exception:
                    # Stop if invalid intermediate path
                    break

        app_name = current_model._meta.app_label.lower()
        model_name = current_model._meta.model_name.lower()

        # Standardized API path
        return f"/{app_name}/{model_name}/"


    @classmethod
    def attach_dependencies(cls, data, depends_on, depends_chain):
        if depends_on:
            data["depends_on"] = depends_on
        if depends_chain:
            data["depends_chain"] = depends_chain
            data["filter_param"] = depends_chain[-1]
        elif depends_on:
            data["filter_param"] = depends_on


class FilterInspector:
    def __init__(self, view):
        self.view = view
        self.model = view.get_queryset().model

    def get_filterset_class(self):
        filterset_class = getattr(self.view, "filterset_class", None)
        if filterset_class:
            return filterset_class

        for backend in getattr(self.view, "filter_backends", []):
            if issubclass(backend, DjangoFilterBackend):
                try:
                    return backend().get_filterset_class(self.view, self.view.get_queryset())
                except Exception:
                    pass
        return None

    def describe_filters(self):
        cls = MetadataHelper
        filterset_class = self.get_filterset_class()
        if not filterset_class:
            return {}

        result = {}
        for name, f in filterset_class.base_filters.items():
            data = {"label": getattr(f, "label", name.replace("_", " ").title())}

            depends_on = ModelResolver.get_depends_on(name)
            depends_chain = ModelResolver.get_depends_chain(name)
            related_model, last_field = ModelResolver.resolve_field(self.model, name)

            data["type"] = cls.detect_type(f, related_model, last_field)
            cls.attach_fk_m2m_or_choice_info(data, f, related_model, nested_path=name, base_model=self.model)
            cls.attach_dependencies(data, depends_on, depends_chain)

            result[name] = data

        return result


class Metadata(SimpleMetadata):
    def get_field_info(self, field):
        cls = MetadataHelper
        field_info = super().get_field_info(field)
        field_info["name"] = getattr(field, "field_name", "")
        field_info["type"] = cls.detect_type(field)
        cls.attach_fk_m2m_or_choice_info(field_info, field)

        # Normalize label: remove "_id" and convert to title
        name = getattr(field, "source", None) or getattr(field, "field_name", "")
        if name:
            clean_name = name.replace("_id", "").replace("_", " ").title()
            field_info["label"] = clean_name

        # Add length/size info
        if hasattr(field, "max_length") and field.max_length is not None:
            field_info["max_length"] = field.max_length
        elif hasattr(field, "max_digits") and field.max_digits is not None:
            field_info["max_digits"] = field.max_digits
            field_info["decimal_places"] = getattr(field, "decimal_places", 0)
            
        return field_info

    def determine_metadata(self, request, view):
        metadata = super().determine_metadata(request, view)

        # Serializer fields
        serializer = getattr(view, "get_serializer", lambda: None)()
        if serializer:
            metadata["fields"] = {
                name: self.get_field_info(f) for name, f in 
                serializer.fields.items()
                if not getattr(f, "read_only", False)
            }

        # Filter fields
        inspector = FilterInspector(view)
        metadata["filter_fields"] = inspector.describe_filters()

        # Other metadata
        metadata["search_fields"] = getattr(view, "search_fields", [])
        metadata["ordering_fields"] = getattr(view, "ordering_fields", [])

        metadata.pop("actions")

        return metadata
