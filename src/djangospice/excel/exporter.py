import uuid
from slugify import slugify
from io import BytesIO
from django.utils import timezone
from django.http import HttpResponse, StreamingHttpResponse
from djangospice.files.writer import FileWriter

from .engine import WorkbookEngine
from .inspection import ModelInspector


class Exporter:
    """Orchestrates Excel generation with optimized memory usage."""

    CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def __init__(self, model, dataset, reference_sheets=None, export_name=None, **kwargs):
        self.engine = WorkbookEngine(model, dataset, reference_sheets or {}, **kwargs)
        self.export_name = export_name or str(model._meta.verbose_name_plural)
        self.base_filename = ModelInspector.get_file_name(self.export_name)

    def get_buffer(self) -> BytesIO:
        """Centralized buffer creation."""
        buffer = BytesIO()
        self.engine.build().save(buffer)
        buffer.seek(0)
        return buffer

    def _get_filename(self, use_uuid: bool) -> str:
        """Handles naming convention logic."""
        if use_uuid:
            return f"{uuid.uuid4()}.xlsx"
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"{slugify(self.base_filename)}_{timestamp}.xlsx"

    def generate_response(self, streaming: bool = False) -> HttpResponse:
        buffer = self.get_buffer()
        klass = StreamingHttpResponse if streaming else HttpResponse
        
        response = klass(buffer if streaming else buffer.getvalue(), content_type=self.CONTENT_TYPE)
        response['Content-Disposition'] = f'attachment; filename="{self.base_filename}.xlsx"'
        return response

    def save_to_storage(self, folder_path: str, use_uuid: bool = False) -> str:
        """Persists the generated file to Django storage."""
        full_path = f"{folder_path.strip('/')}/{self._get_filename(use_uuid)}"
        
        buffer = self.get_buffer()
        content = buffer.read()
        
        return FileWriter.save(full_path, content)