import os
from uuid import uuid4
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile


class MediaStorage(FileSystemStorage):


    def url(self, name):
        """
        Generates a URL that includes the schema name in the media URL.
        """
        return f"{self.base_url}{name}"

    def path(self, name):
        """
        Ensure the path includes the schema directory when accessing the file.
        """
        return f"{self.base_location}{name}"

    def upload(self, uploaded_file, upload_path: str = "uploads", rename: bool = True) -> str:
        """
        Upload a file to media directory, optionally renaming it.

        Args:
            uploaded_file (UploadedFile): The file being uploaded.
            upload_path (str, optional): Subdirectory within the media directory 
                where the file should be uploaded. Defaults to uploads.
            rename (bool, optional): If True, the file will be renamed using a UUID. 
                Defaults to True.

        Returns:
            str: The path where the file has been saved.
        """
        file_name = uploaded_file.name

        # Optionally rename the file using a UUID
        if rename:
            file_extension = os.path.splitext(uploaded_file.name)[1]
            file_name = f"{uuid4()}{file_extension}"

        # If an upload path is provided, ensure the directory exists
        if upload_path:
            self._make_upload_path(upload_path)
            file_name = f'{upload_path}/{file_name}'

        # Save the uploaded file and return its saved path
        saved_file = self.save(file_name, ContentFile(uploaded_file.read()))
        
        return self.path(saved_file)

    def storage_path(self, path):
        self._make_upload_path(path)
        return self.path(path)

    def _make_upload_path(self, upload_path: str) -> None:
        """
        Ensure the specified upload directory exists by creating it if necessary.

        Args:
            upload_path (str): The path to the directory to be created.
        """
        # Create a dummy file to force the creation of the directory if it doesn't exist
        dummy_file_path = f'{upload_path.rstrip("/")}/.dummy'

        # Save an empty file (this will create the directory if it doesn't exist)
        if not self.exists(dummy_file_path):
            self.save(dummy_file_path, ContentFile(''))
        
        # Remove the dummy file after creating the directory
        if self.exists(dummy_file_path):
            self.delete(dummy_file_path)
