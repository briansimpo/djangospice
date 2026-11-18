import io
import os
import mimetypes
from PIL import Image
from slugify import slugify
from pathlib import Path
from django.utils.http import content_disposition_header
from django.core.files.base import ContentFile
from django.http import FileResponse, StreamingHttpResponse

from django.core.files.storage import default_storage
from .storage import MediaStorage
from .path import PathWrapper


def file_exists(file_path):
    return bool(file_path) and default_storage.exists(file_path)


def file_url(file_path):
    return default_storage.url(file_path)


def file_path(file_path):
    """
    Get the local filesystem path.

    Only supported by filesystem-based storage backends.
    """
    return default_storage.path(file_path)


def file_upload_path(sub_path):
    """
    The wrapper function you use in your models.
    """
    return PathWrapper(sub_path)


def resize_image(image_path, size, format='PNG', quality=90):
    """
    Resize an image in-place.
    """
    with Image.open(image_path) as img:
        img = img.convert("RGB")
        img.thumbnail(size)
        img.save(image_path, format=format, quality=quality)


def save_uploaded_file(uploaded_file, upload_path="uploads", rename=True):
    storage = MediaStorage()
    saved_file_path = storage.upload(uploaded_file, upload_path, rename)
    return saved_file_path


def remove_uploaded_file(file_path):
    if os.path.exists(file_path):
        try:
            # Delete the file from the file system
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

        
def get_file_path(file_name, app_name=None):
    if app_name is None:
        return file_name
    else:
        return f"{app_name}/{file_name}"
    

def get_file_slug(file_name, file_extension=None, capitalize=True):
    file_name = slugify(file_name)
    if capitalize:
        file_name = file_name.upper()
    if file_extension:
        file_name = f"{file_name}.{file_extension}"
    return file_name


def read_imported_file(file_path, size=None):
    # Get the file extension
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # Read the file and load into an appropriate in-memory stream
    if file_extension in ['.xlsx', '.xls']:
        with open(file_path, 'rb') as f:
            in_stream = io.BytesIO(f.read(size))
        file_format = file_extension.lstrip('.')
    elif file_extension == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            in_stream = io.StringIO(f.read(size))
        file_format = 'csv'
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    return in_stream, file_format



def download(file,*,filename=None,content_type=None):
    """Return a browser file download."""

    if isinstance(file, bytes):
        file = ContentFile(file)

    elif isinstance(file, (str, os.PathLike)):
        path = Path(file)
        filename = filename or path.name
        file = path.open("rb")

    elif hasattr(file, "storage") and hasattr(file, "name"):
        if not file:
            raise ValueError("File does not exist.")

        filename = filename or Path(file.name).name
        file.open("rb")

    elif not hasattr(file, "read"):
        raise TypeError(
            f"Unsupported file type: {type(file).__name__}"
        )

    filename = filename or getattr(file, "name", None)

    if filename:
        filename = Path(filename).name

    content_type = (
        content_type
        or (
            mimetypes.guess_type(filename)[0]
            if filename else None
        )
        or "application/octet-stream"
    )

    return FileResponse(
        file,
        as_attachment=True,
        filename=filename,
        content_type=content_type,
    )


def stream(streaming_content,*,content_type="application/octet-stream",filename=None,as_attachment=False,headers=None):
    """Return a streaming HTTP response."""

    response = StreamingHttpResponse(
        streaming_content,
        content_type=content_type,
        headers=headers,
    )

    if filename:
        response["Content-Disposition"] = (
            content_disposition_header(
                as_attachment,
                filename,
            )
        )

    return response