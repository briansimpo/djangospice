from django.db.models import QuerySet

class FormFieldMixin:
    """
    Mixin for dynamically setting field querysets and values.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filtered_fields()

    def set_field_queryset(self, field_name: str, queryset: QuerySet):
        if field_name in self.fields:
            self.fields[field_name].queryset = queryset

    def set_field_value(self, field_name: str, value):
        if field_name in self.fields:
            self.fields[field_name].initial = value

    def filtered_fields(self):
        """
        Override in subclasses to apply per-field filtering.
        """
        pass
    
    

class FormRequestMixin:
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"request": self.request})
        return kwargs