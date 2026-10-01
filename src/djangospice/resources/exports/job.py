from typing import Any
from dataclasses import dataclass
from django.core.files.storage import default_storage
from djangospice.core.payload import Payload
from djangospice.jobs import Job
from djangospice.resources import BaseResource
from .exporter import ResourceExporter


@dataclass
class ResourceExportJob(Job):
    """Background job for heavy-duty data exports."""
    
    queue = "data-exports"
    export_dir = "exports"
    resource: BaseResource
    user_id: str
    rename_file: bool = False
    
        
    def handle(self) -> dict[str, Any]:
        self.progress(10, 100, message="Initializing export...")

        # 1. Initialize Service
        export_service = ResourceExporter(self.resource)
        
        self.progress(40, 100, message="Generating dataset...")
        
        # 2. Trigger Generation & Storage
        file_path = export_service.save(
            folder_path=self.export_dir, 
            use_uuid=self.rename_file
        )

        self.progress(100, 100, message="Export complete.")
        
        file_url = default_storage.url(file_path)
        message = "Export completed successfully."

        return Payload(file_url=file_url, message=message).to_dict()
