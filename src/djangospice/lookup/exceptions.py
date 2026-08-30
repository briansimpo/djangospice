class LookupError(Exception):
    """Base exception for lookup errors."""


class LookupModelNotFound(LookupError):
    """The requested model does not exist."""


class InvalidLookupField(LookupError):
    """A lookup filter is not a valid model relationship."""


class InvalidLookupValue(LookupError):
    """A lookup filter contains an invalid value."""


class LookupNotAllowed(LookupError):
    """The requested model is not exposed through the lookup engine."""