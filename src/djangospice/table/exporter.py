
from __future__ import annotations

import re
import uuid
from pathlib import PurePosixPath
from typing import Any

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django_tables2.export import TableExport


class TableExporter:
    """
    Exports a configured Django Table and persists the generated file.

    Responsibilities:
    - Export table data into the requested format.
    - Generate meaningful filenames.
    - Persist files using Django's configured storage backend.
    - Return the stored file path and URL.
    """

    def __init__(
        self,
        table: Any,
        export_format: str = "xlsx",
        rename_file: bool = True,
        storage=None,
        directory: str = "exports",
        filename: str | None = None,
    ) -> None:
        self.table = table
        self.export_format = export_format.lower().lstrip(".")
        self.rename_file = rename_file
        self.storage = storage or default_storage
        self.directory = directory.strip("/")
        self.filename = filename

    def _get_base_name(self) -> str:
        """Resolve a meaningful name from table/model metadata."""
        meta = getattr(self.table, "Meta", None)
        model = getattr(meta, "model", None)

        name = (
            model._meta.verbose_name_plural
            if model is not None
            else self.table.__class__.__name__
        )

        name = str(name).lower().replace(" ", "_")
        name = re.sub(r"[^a-z0-9_-]+", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")

        return name or "export"

    def _generate_filename(self) -> str:
        """Generate the final storage-relative filename."""
        if self.filename:
            name = PurePosixPath(self.filename).name
        else:
            name = self._get_base_name()

        # Avoid accidentally duplicating the extension.
        name = re.sub(
            rf"\.{re.escape(self.export_format)}$",
            "",
            name,
            flags=re.IGNORECASE,
        )

        if self.rename_file:
            name = f"{name}_{uuid.uuid4().hex[:8]}"

        return str(
            PurePosixPath(self.directory) / f"{name}.{self.export_format}"
        )

    def export(self) -> str:
        """
        Export and save the table.

        Returns:
            str: file_url
        """
        exporter = TableExport(
            self.export_format,
            self.table,
        )

        content = exporter.export()

        filename = self._generate_filename()

        file_path = self.storage.save(
            filename,
            ContentFile(content),
        )

        file_url = self.storage.url(file_path)

        return file_url
