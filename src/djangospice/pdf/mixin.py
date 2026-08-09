from django.http import HttpResponse
from django.shortcuts import render
from django_renderpdf import helpers



class PDFViewMixin:
    """
    Handles PDF rendering for a view, including applied filters context.
    """

    pdf_template = None
    prompt_download: bool = False
    download_name: str = None
    allow_force_html: bool = True

    def get_download_name(self) -> str:
        return self.download_name or "document.pdf"

    def url_fetcher(self, url):
        return helpers.django_url_fetcher(url)

    def get_applied_filters_context(self, context: dict) -> dict:
        """
        Extract filterset form data and verbose labels to include in PDF context.
        """
        if hasattr(self, 'filterset') and self.filterset.form.is_valid():
            # Filter values
            filter_params = {
                k: v
                for k, v in self.filterset.form.cleaned_data.items()
                if v not in [None, '', [], (), {}]
            }
            # Field labels
            filter_labels = {
                f: fld.label
                for f, fld in self.filterset.form.fields.items()
            }
            # Combine label + value
            context["applied_filters"] = {filter_labels[k]: v for k, v in filter_params.items()}
        return context

    def generate_pdf(self, context: dict) -> HttpResponse:
        """
        Render PDF using django_renderpdf, injecting applied filters.
        """
        context = self.get_applied_filters_context(context)

        response = HttpResponse(content_type="application/pdf")
        if self.prompt_download:
            response["Content-Disposition"] = f'attachment; filename="{self.get_download_name()}"'
        helpers.render_pdf(
            template=self.pdf_template,
            file_=response,
            url_fetcher=self.url_fetcher,
            context=context,
        )
        return response

    def render_to_response(self, context: dict, **kwargs):
        """
        Decide PDF rendering or normal template rendering based on request GET parameter.
        """
        export_format = self.request.GET.get('export', None)
        if export_format == "pdf":
            return self.generate_pdf(context)
        return render(self.request, self.template_name, context)