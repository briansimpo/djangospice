from django.db.models import QuerySet
from django.http import HttpRequest
from django.core.exceptions import ImproperlyConfigured


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