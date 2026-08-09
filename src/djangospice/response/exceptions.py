class ResponseError(Exception):
    """Base response exception."""


class RendererNotFound(ResponseError):
    """Raised when a renderer is not registered."""


class InvalidResponse(ResponseError):
    """Raised when a response cannot be rendered."""