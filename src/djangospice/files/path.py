import os
from uuid import uuid4
from slugify import slugify
from django.utils.deconstruct import deconstructible



@deconstructible
class PathWrapper:
    """
    A deconstructible class that handles the actual path logic.
    Django migrations can see this class because it is at the app level.
    """
    def __init__(self, sub_path):
        self.sub_path = sub_path

    def __call__(self, instance, filename):
        name, ext = os.path.splitext(filename)
        safe_name = slugify(name)
        final_filename = f"{uuid4().hex[:8]}-{safe_name}{ext}"
        return os.path.join(self.sub_path, final_filename)