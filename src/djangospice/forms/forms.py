
from django import forms
from django.forms.models import ModelFormMetaclass, fields_for_model

from .helpers import create_form_field
from .meta import get_meta_options


class DynamicModelFormMetaclass(ModelFormMetaclass):

    def __new__(mcs, name, bases, attrs):

        meta = attrs.get("Meta")
        meta_options = get_meta_options(meta, bases)

        model = meta_options.get("model")

        if model is None:
            new_class = super().__new__(
                mcs,
                name,
                bases,
                attrs,
            )
            return new_class

        lookups = meta_options.get("lookups", ())
        auto_lookup = meta_options.get("auto_lookup", True)

        inlines = meta_options.get("inlines", ())
        auto_inlines = meta_options.get("auto_inlines", False)

        callback = create_form_field(
            model=model,
            lookups=lookups,
            auto_lookup=auto_lookup,
        )

        meta_fields = meta_options.get("fields")

        if meta_fields == "__all__":
            meta_fields = None

        generated_fields = fields_for_model(
            model,
            fields=meta_fields,
            exclude=meta_options.get("exclude"),
            widgets=meta_options.get("widgets"),
            localized_fields=meta_options.get("localized_fields"),
            labels=meta_options.get("labels"),
            help_texts=meta_options.get("help_texts"),
            error_messages=meta_options.get("error_messages"),
            field_classes=meta_options.get("field_classes"),
            formfield_callback=callback,
            apply_limit_choices_to=False,
        )

        declared_fields = attrs.get(
            "declared_fields",
            {},
        ).copy()

        for field_name, value in attrs.items():
            if isinstance(value, forms.Field):
                declared_fields[field_name] = value

        generated_fields.update(declared_fields)

        for field_name, form_field in generated_fields.items():
            attrs.setdefault(field_name, form_field)

        new_class = super().__new__(
            mcs,
            name,
            bases,
            attrs,
        )

        new_class._inline_definitions = tuple(inlines)
        new_class._auto_inlines = auto_inlines

        return new_class


class DynamicModelForm(forms.ModelForm, metaclass=DynamicModelFormMetaclass):
    """ModelForm with dynamic fields and inline formset support."""

    @classmethod
    def get_inline_formsets(cls):
        from .builders import InlineFormBuilder

        return InlineFormBuilder(
            cls._meta.model,
            inlines=cls._inline_definitions,
            auto_discover=cls._auto_inlines,
        ).build()