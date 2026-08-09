import os
import tablib
import logging

logger = logging.getLogger(__name__)


class TemporaryDataset:
    """
    Context manager that loads a file into a clean tablib.Dataset 
    and guarantees file deletion upon exit.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def __enter__(self) -> tablib.Dataset:
        self.dataset = self._load()
        return self._filter(self.dataset)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError as e:
                logger.warning(f"Failed to delete temporary file {self.file_path}: {e}")

    def _load(self) -> tablib.Dataset:
        ext = os.path.splitext(self.file_path)[1].lower()
        
        if ext in ['.xlsx', '.xls']:
            with open(self.file_path, 'rb') as f:
                return tablib.Dataset().load(f.read(), ext.lstrip('.'))
        elif ext == '.csv':
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return tablib.Dataset().load(f.read(), 'csv')
                
        raise ValueError(f"Unsupported file format: {ext}")

    def _filter(self, dataset: tablib.Dataset) -> tablib.Dataset:
        # Filter out empty rows
        return tablib.Dataset(
            *[row for row in dataset if any(cell not in (None, '', ' ') for cell in row)],
            headers=dataset.headers
        )