class FormBuilderError(Exception):
    """Base exception for Djangospice forms."""


class InvalidModelError(FormBuilderError):
    """Raised when an invalid Django model is supplied."""


class InvalidLookupError(FormBuilderError):
    """Raised when lookup configuration is invalid."""


class InvalidInlineError(FormBuilderError):
    """Raised when an inline declaration is invalid."""


class FormProcessingError(Exception):
    """Base exception for form processing errors."""


class InvalidFormError(FormProcessingError):
    """Raised when attempting to save invalid forms."""


class FormAlreadySavedError(FormProcessingError):
    """Raised when attempting to save a processor twice."""