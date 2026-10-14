from django import forms
from django.core.validators import FileExtensionValidator
from djangospice.files.mimetypes import MS_EXCEL_MIMETYPE

class ImportExcelForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={"accept": MS_EXCEL_MIMETYPE}),
        required=True,
        label="Excel File",
        validators=[FileExtensionValidator(allowed_extensions=["xlsx", "xls"])],
    )