from django import forms
from django.forms.models import modelform_factory

from .exceptions import InvalidModelError
from .helpers import create_form_field


class ModelFormBuilder:

    def __init__(
        self,
        model,
        *,
        fields="__all__",
        exclude=None,
        form=None,
        lookups=None,
        auto_lookup=True,
        formfield_callback=None,
        widgets=None,
        labels=None,
        help_texts=None,
        error_messages=None,
        field_classes=None,
        inlines=None,
        auto_inlines=False,
    ):
        if not hasattr(model, "_meta"):
            raise InvalidModelError(
                f"{model!r} is not a Django model."
            )

        self.model = model
        self.fields = fields
        self.exclude = exclude
        self.form = form or forms.ModelForm

        self.lookups = lookups or []
        self.auto_lookup = auto_lookup

        self.formfield_callback = create_form_field(
            model=model,
            lookups=self.lookups,
            auto_lookup=auto_lookup,
            callback=formfield_callback,
        )

        self.widgets = widgets
        self.labels = labels
        self.help_texts = help_texts
        self.error_messages = error_messages
        self.field_classes = field_classes
        self.inlines = list(inlines or ())
        self.auto_inlines = auto_inlines

    def build(self, name="DynamicModelForm"):
        return modelform_factory(
            model=self.model,
            form=self.form,
            fields=self.fields,
            exclude=self.exclude,
            formfield_callback=self.formfield_callback,
            widgets=self.widgets,
            labels=self.labels,
            help_texts=self.help_texts,
            error_messages=self.error_messages,
            field_classes=self.field_classes,
        )

    def build_inlines(self):
        from .inlines import InlineFormBuilder

        return InlineFormBuilder(
            parent_model=self.model,
            inlines=self.inlines,
            auto_discover=self.auto_inlines,
        ).build()

    @classmethod
    def create(cls, model, **kwargs):
        return cls(model, **kwargs).build()