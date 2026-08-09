from django import forms
from django.core.validators import FileExtensionValidator
from djangospice.files.mimetypes import PDF_MIMETYPE, MS_WORD_MIMETYPE, MS_DOC_MIMETYPE

DOC_EXTENSIONS = ["pdf", "doc", "docx"]
DOC_MIMETYPES = ",".join([PDF_MIMETYPE, MS_WORD_MIMETYPE, MS_DOC_MIMETYPE])

class DocumentField(forms.FileField):
    def __init__(self, allowed_extensions=None, accepted_mimetypes=None, label=None, required=False, **kwargs):
        self.allowed_extensions = allowed_extensions or DOC_EXTENSIONS
        accepted_mimetypes = accepted_mimetypes or DOC_MIMETYPES

        kwargs["widget"] = forms.FileInput(attrs={"accept": DOC_MIMETYPES})
        kwargs["validators"] = [FileExtensionValidator(allowed_extensions=self.allowed_extensions)]
        super().__init__(label=label, required=required, **kwargs)


class MultipleDocumentsField(forms.FileField):
    def __init__(self, allowed_extensions=None, accepted_mimetypes=None, label=None, required=False, **kwargs):
        self.allowed_extensions = allowed_extensions or DOC_EXTENSIONS
        accepted_mimetypes = accepted_mimetypes or DOC_MIMETYPES

        kwargs["widget"] = forms.TextInput(attrs={"type": "file", "multiple": "True"})
        kwargs["validators"] = [FileExtensionValidator(allowed_extensions=self.allowed_extensions)]
        super().__init__(label=label, required=required, **kwargs)
        
        
