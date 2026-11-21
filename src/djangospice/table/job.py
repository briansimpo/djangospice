from __future__ import annotations

import logging
import django_tables2 as tables

from dataclasses import dataclass, field
from typing import Any, ClassVar, Type

from django.db import models

from djangospice.jobs.job import Job

from .builders import TableBuilder
from .exporter import TableExporter


logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class TableExportJob(Job):

    SUPPORTED_FORMATS: ClassVar[tuple[str, ...]] = (
        "csv",
        "xlsx",
    )

    model_class_path: str
    export_format: str

    table_class_path: str | None = None

    filters: dict[str, Any] = field(default_factory=dict)
    table_config: dict[str, Any] = field(default_factory=dict)
    table_kwargs: dict[str, Any] = field(default_factory=dict)

    rename_file: bool = True
    directory: str = "exports"
    filename: str | None = None

    @classmethod
    def create(
        cls,
        *,
        model_class: Type[models.Model],
        export_format: str = "xlsx",
        table_class: Type[tables.Table] | None = None,
        filters: dict[str, Any] | None = None,
        table_config: dict[str, Any] | None = None,
        table_kwargs: dict[str, Any] | None = None,
        rename_file: bool = True,
        directory: str = "exports",
        filename: str | None = None,
    ) -> TableExportJob:

        export_format = export_format.lower().lstrip(".")

        if export_format not in cls.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported export format: {export_format}"
            )

        return cls(
            model_class_path=(
                f"{model_class.__module__}.{model_class.__qualname__}"
            ),
            table_class_path=(
                f"{table_class.__module__}.{table_class.__qualname__}"
                if table_class is not None
                else None
            ),
            export_format=export_format,
            filters=filters or {},
            table_config=table_config or {},
            table_kwargs=table_kwargs or {},
            rename_file=rename_file,
            directory=directory,
            filename=filename,
        )

    def handle(self) -> str:

        try:
            self.progress(10, 100, message="Initializing export...")

            builder = TableBuilder(
                model=self.model_class_path,
                table_class=self.table_class_path,
                filters=self.filters,
                table_kwargs=self.table_kwargs,
                **self.table_config,
            )

            self.progress(40, 100, message="Generating dataset...")

            table = builder.build()

            exporter = TableExporter(
                table=table,
                export_format=self.export_format,
                rename_file=self.rename_file,
                directory=self.directory,
                filename=self.filename,
            )

            self.progress(100, 100, message="Export complete.")
                  
            return exporter.export()

        except Exception:
            logger.exception(
                "Table export failed: model=%s, table=%s, format=%s",
                self.model_class_path,
                self.table_class_path,
                self.export_format,
            )
            raise