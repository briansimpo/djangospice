class FormBuilderError(Exception):
    """Base exception for Djangospice forms."""


class InvalidModelError(FormBuilderError):
    """Raised when an invalid Django model is supplied."""


class InvalidLookupError(FormBuilderError):
    """Raised when lookup configuration is invalid."""