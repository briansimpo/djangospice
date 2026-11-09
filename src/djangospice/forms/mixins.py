from __future__ import annotations


from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.edit import ModelFormMixin

from .processor import ModelFormProcessor


class FormFieldMixin:
    """
    Mixin for dynamically setting field querysets and values.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_fields()

    def set_field_queryset(self, field_name: str, queryset: QuerySet):
        if field_name in self.fields:
            self.fields[field_name].queryset = queryset

    def set_field_value(self, field_name: str, value):
        if field_name in self.fields:
            self.fields[field_name].initial = value

    def set_fields(self):
        """
        Override in subclasses to apply per-field filtering.
        """
        pass
    

class FormRequestMixin:
    
    def __init__(self, *args, **kwargs):
        """
        Initializes the form with the request object and sets up filtered fields.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments, expected to include "request".

        Raises:
            ImproperlyConfigured: If the "request" argument is not provided or is not an instance of HttpRequest.
        """
        request = kwargs.pop("request", None)

        if not isinstance(request, HttpRequest):
            raise ImproperlyConfigured(
                "The 'request' argument must be an HttpRequest instance."
            )

        self.request = request

        super().__init__(*args, **kwargs)



class InlineFormMixin(ModelFormMixin):
    processor_class = ModelFormProcessor

    def get_processor(self, *, data=None, files=None):
        return self.processor_class(
            self.get_form_class(),
            data=data,
            files=files,
            instance=self.object,
            prefix=self.get_prefix(),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        processor = kwargs.get("processor")

        if processor is None:
            processor = self.get_processor()

        context["processor"] = processor
        context["form"] = processor.form
        context["inline_formsets"] = processor.formsets

        return context

    def post(self, request, *args, **kwargs):
        self.object = (
            self.get_object()
            if hasattr(self, "get_object")
            else None
        )

        processor = self.get_processor(
            data=request.POST,
            files=request.FILES,
        )

        if processor.is_valid():
            return self.form_valid(processor)

        return self.form_invalid(processor)

    def form_valid(self, processor):
        self.object = processor.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, processor):
        return self.render_to_response(
            self.get_context_data(processor=processor)
        )
