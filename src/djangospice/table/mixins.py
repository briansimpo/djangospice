from django.utils.html import format_html
from django_tables2.export import  ExportMixin as BaseExportMixin


class BooleanFieldMixin:

    def render_boolean(self, value):
        if value:
            icon_class = "fa fa-check"
        else:
            icon_class = "fa fa-times"
        return format_html(
            "<i class='{}'></i>",icon_class
        )



class ExportMixin(BaseExportMixin):
    """
    Handles table export (CSV, XLSX, etc.) without PDF.
    """

    export_formats = ["xlsx", "csv"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Optional: applied filters, verbose labels
        if hasattr(self, 'filterset') and self.filterset.form.is_valid():
            filter_params = {
                k: v for k, v in self.filterset.form.cleaned_data.items()
                if v not in [None, '', [], (), {}]
            }
            filter_labels = {f: fld.label for f, fld in self.filterset.form.fields.items()}
            context["applied_filters"] = {filter_labels[k]: v for k, v in filter_params.items()}

        return context
    
