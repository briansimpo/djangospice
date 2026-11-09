from django import forms
from django.core.validators import FileExtensionValidator
from djangospice.files.mimetypes import PDF_MIMETYPE, MS_WORD_MIMETYPE, MS_DOC_MIMETYPE, MS_EXCEL_MIMETYPE
from djangospice.lookup.widget import LookupWidget


DOC_EXTENSIONS = ["pdf", "doc", "docx", "xlsx", "xls"]
DOC_MIMETYPES = ",".join([PDF_MIMETYPE, MS_WORD_MIMETYPE, MS_DOC_MIMETYPE, MS_EXCEL_MIMETYPE])


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
        

class LookupChoiceField(forms.ModelChoiceField):
    widget = LookupWidget

    def __init__(
        self,
        queryset,
        *,
        placeholder="Select...",
        search_placeholder="Search...",
        depends_on=None,
        **kwargs,
    ):
        widget = kwargs.pop("widget", None)

        if widget is None:
            widget = LookupWidget(
                queryset=queryset,
                placeholder=placeholder,
                search_placeholder=search_placeholder,
                depends_on=depends_on,
            )

        super().__init__(
            queryset=queryset,
            widget=widget,
            **kwargs,
        )


class LookupMultipleChoiceField(forms.ModelMultipleChoiceField):
    widget = LookupWidget

    def __init__(
        self,
        queryset,
        *,
        placeholder=None,
        search_placeholder=None,
        depends_on=None,
        **kwargs,
    ):
        widget = kwargs.pop("widget", None)

        if widget is None:
            widget = LookupWidget(
                queryset=queryset,
                placeholder=placeholder,
                search_placeholder=search_placeholder,
                depends_on=depends_on,
                multi_select=True,
            )

        super().__init__(
            queryset=queryset,
            widget=widget,
            **kwargs,
        )
