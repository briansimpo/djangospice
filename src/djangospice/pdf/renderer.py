import os
import uuid
from django_renderpdf import helpers
from django.core.files.storage import default_storage
from django.http import HttpResponse


class PDFRenderer:
    
    def __init__(self, download_name: str = "document.pdf", allow_force_html: bool = True, prompt_download: bool = False):
        self.download_name = download_name
        self.allow_force_html = allow_force_html
        self.prompt_download = prompt_download

    def get_download_name(self) -> str:
        return self.download_name or "document.pdf"

    def url_fetcher(self, url):
        return helpers.django_url_fetcher(url)

    def save_pdf(self, template, context, folder_path="pdfs") -> dict:
        """
        Renders the PDF with a unique UUID filename and saves it.
        Returns 'file_path' and 'file_url'.
        """
        # 1. Generate a unique filename
        unique_filename = f"{uuid.uuid4()}_{self.get_download_name()}"
        
        # 2. Construct the relative storage path
        relative_file_path = os.path.join(folder_path, unique_filename)
        
        # 3. Get the absolute system path
        full_system_path = default_storage.path(relative_file_path)
        
        # 4. Ensure the directory exists
        os.makedirs(os.path.dirname(full_system_path), exist_ok=True)
        
        # 5. Render and save the file
        with open(full_system_path, "wb") as f:
            helpers.render_pdf(
                template=template,
                file_=f,
                url_fetcher=self.url_fetcher,
                context=context,
            )
        
        # 6. Retrieve the web-accessible URL
        file_url = default_storage.url(relative_file_path)
        
        return {
            "file_path": full_system_path,
            "file_url": file_url,
            "filename": unique_filename
        }
        
    def render_pdf(self, request, template, context) -> HttpResponse:
        response = HttpResponse(content_type="application/pdf")
        if self.prompt_download:
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(
                self.get_download_name()
            )
        helpers.render_pdf(
            template=template,
            file_=response,
            url_fetcher=self.url_fetcher,
            context=context,
        )
        return response
    