from django import forms
from django.forms.models import ModelFormMetaclass, fields_for_model

from .helpers import create_form_field


class DynamicModelFormMetaclass(ModelFormMetaclass):

    def __new__(mcs, name, bases, attrs):

        meta = attrs.get("Meta")

        if meta is None:
            return super().__new__(
                mcs,
                name,
                bases,
                attrs,
            )

        model = getattr(meta, "model", None)

        if model is None:
            return super().__new__(
                mcs,
                name,
                bases,
                attrs,
            )

        lookups = getattr(meta, "lookups", [])
        auto_lookup = getattr(meta, "auto_lookup", True)

        callback = create_form_field(
            model=model,
            lookups=lookups,
            auto_lookup=auto_lookup,
        )

        meta_fields = getattr(meta, "fields", None)

        if meta_fields == "__all__":
            meta_fields = None

        generated_fields = fields_for_model(
            model,
            fields=meta_fields,
            exclude=getattr(meta, "exclude", None),
            widgets=getattr(meta, "widgets", None),
            localized_fields=getattr(
                meta,
                "localized_fields",
                None,
            ),
            labels=getattr(meta, "labels", None),
            help_texts=getattr(meta, "help_texts", None),
            error_messages=getattr(meta, "error_messages", None),
            field_classes=getattr(meta, "field_classes", None),
            formfield_callback=callback,
            apply_limit_choices_to=False,
        )

        # Explicitly declared fields take precedence.
        declared_fields = attrs.get("declared_fields", {})

        for field_name, field in attrs.items():
            if isinstance(field, forms.Field):
                declared_fields[field_name] = field

        generated_fields.update(declared_fields)

        # Explicit class fields take precedence over generated fields.
        for field_name, form_field in generated_fields.items():
            attrs.setdefault(field_name, form_field)

        return super().__new__(
            mcs,
            name,
            bases,
            attrs,
        )


class DynamicModelForm(forms.ModelForm, metaclass=DynamicModelFormMetaclass):
    """
    ModelForm with automatic Djangospice lookup generation.
    """

    pass
