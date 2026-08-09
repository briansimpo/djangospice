import io
import os
import mimetypes
from PIL import Image
from slugify import slugify
from django.conf import settings
from django.http import HttpResponse, Http404
from .storage import MediaStorage
from .path import PathWrapper



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


def download(file_path: str) -> HttpResponse:
    """
    Return a Django HTTP response to serve a file from MEDIA_ROOT.
    """
    abs_path = os.path.join(settings.MEDIA_ROOT, file_path)
    if os.path.exists(abs_path):
        mime_type, _ = mimetypes.guess_type(abs_path)
        file_name = os.path.basename(abs_path)
        with open(abs_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = f'inline; filename={file_name}'
            return response
    raise Http404(f"File {file_path} not found")