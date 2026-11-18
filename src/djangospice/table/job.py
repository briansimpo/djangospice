
from __future__ import annotations

import logging

from dataclasses import dataclass, field
from typing import Any, ClassVar, Type

from django.db import models

from djangospice.jobs.base import Job

from .builder import TableBuilder
from .exporter import TableExporter

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class TableExportJob(Job):
    """
    Background job responsible for exporting Django tables.

    Stores serializable configuration and reconstructs the table
    inside the worker before exporting it.
    """

    SUPPORTED_FORMATS: ClassVar[tuple[str, ...]] = (
        "csv",
        "xlsx",
    )

    table_class_path: str
    model_class_path: str
    export_format: str

    filters: dict[str, Any] = field(default_factory=dict)
    table_kwargs: dict[str, Any] = field(default_factory=dict)

    rename_file: bool = True
    directory: str = "exports"
    filename: str | None = None

    @classmethod
    def create(
        cls,
        table_class: Type[Any],
        model_class: Type[models.Model],
        export_format: str = "xlsx",
        filters: dict[str, Any] | None = None,
        table_kwargs: dict[str, Any] | None = None,
        rename_file: bool = True,
        directory: str = "exports",
        filename: str | None = None,
    ) -> TableExportJob:
        """
        Create a serializable export job.

        Class objects are converted to importable dotted paths.
        QuerySets must not be passed as job arguments.
        """

        export_format = export_format.lower().lstrip(".")

        if export_format not in cls.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported export format: {export_format}"
            )

        return cls(
            table_class_path=(
                f"{table_class.__module__}.{table_class.__qualname__}"
            ),
            model_class_path=(
                f"{model_class.__module__}.{model_class.__qualname__}"
            ),
            export_format=export_format,
            filters=filters or {},
            table_kwargs=table_kwargs or {},
            rename_file=rename_file,
            directory=directory,
            filename=filename,
        )

    def handle(self) -> tuple[str, str]:
        """
        Execute inside the worker.

        Returns:
            tuple[str, str]: (file_path, file_url)
        """
        try:
            builder = TableBuilder(
                table_class=self.table_class_path,
                model_class=self.model_class_path,
                filters=self.filters,
                table_kwargs=self.table_kwargs,
            )

            table = builder.build_table()

            exporter = TableExporter(
                table=table,
                export_format=self.export_format,
                rename_file=self.rename_file,
                directory=self.directory,
                filename=self.filename,
            )

            result = exporter.export()

            return result

        except Exception:
            logger.exception(
                "Table export failed: %s (%s)",
                self.table_class_path,
                self.export_format,
            )
            raise
