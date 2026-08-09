from dataclasses import asdict
from typing import Any, Optional
from tablib import Dataset

from djangospice.excel.exporter import Exporter
from djangospice.excel.reference import ReferenceMapBuilder
from djangospice.resources import BaseResource


class ResourceExporter:
    """Service orchestrating ModelResource data extraction and Excel generation."""
    
    def __init__(self, resource: BaseResource, **kwargs: Any):
        self.resource = resource
        self.model = resource.model
        self.export_options = kwargs
        self._exporter: Optional[Exporter] = None

    @property
    def exporter(self) -> Exporter:
        if self._exporter is None:
            self._exporter = self._build_exporter()
        return self._exporter

    def _get_dataset(self) -> Dataset:
        """Centralized data extraction logic."""
        if not self.resource.config.export_data:
            return Dataset(headers=self.resource.fields)
        
        queryset = self.resource.get_queryset()
        return self.resource.export(queryset, **self.export_options)

    def _build_exporter(self) -> Exporter:
        """Constructs the Exporter with resolved dependencies."""
        reference_map = (
            ReferenceMapBuilder(
                model=self.model,
                fields=self.resource.fields,
                custom_foreign=self.resource.custom_foreign,
                custom_choices=self.resource.custom_choices
            )
            .add_foreign_keys()
            .add_choices()
            .build()
        )
            
        return Exporter(
            model=self.model, 
            dataset=self._get_dataset(), 
            reference_sheets=reference_map, 
            **asdict(self.resource.config)
        )

    def generate_response(self, streaming: bool = False, cache_key: str = None) -> Any:
        return self.exporter.generate_response(streaming=streaming, cache_key=cache_key)

    def save(self, folder_path: str, use_uuid: bool = False) -> str:
        return self.exporter.save_to_storage(folder_path, use_uuid=use_uuid)