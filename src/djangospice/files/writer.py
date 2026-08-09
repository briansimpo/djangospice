from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

class FileWriter:
    """Handles persistence of exported data."""
    
    @staticmethod
    def save(path: str, content: bytes | str) -> tuple[str, str]:
        """Saves content and returns (path, url)."""
        if isinstance(content, str):
            content = content.encode('utf-8')
            
        return default_storage.save(path, ContentFile(content))
