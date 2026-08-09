from __future__ import annotations

from django.http import HttpRequest, HttpResponse

from djangospice.response.response import Response

from .html import HTMLRenderer


class HTMXRenderer(HTMLRenderer):
    """
    Renders a transport-agnostic Response optimized for HTMX requests.

    Appends Out-of-Band (OOB) fragments to the core markup and injects
    actionable client-side headers into the final HttpResponse.
    """

    name: str = "htmx"
    priority: int = 10

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def supports(self, request: HttpRequest | None) -> bool:
        """
        Return True if the request originates from an active HTMX client component.
        """
        return (
            request is not None
            and request.headers.get("HX-Request") == "true"
        )

    # ------------------------------------------------------------------
    # Pipeline Content Delivery
    # ------------------------------------------------------------------

    def build_content(self, response: Response) -> str:
        """
        Render the primary target template and seamlessly append any registered 
        Out-of-Band fragments.
        """
        content = super().build_content(response)

        # Utilize pythonic truthiness check optimized on the Fragments collection
        if response.fragments:
            # Guard against AttributeError on slotted Response objects
            request = getattr(response, "request", None)
            content += response.fragments.render(request=request)

        return content

    # ------------------------------------------------------------------
    # Response Compilation & Finalization
    # ------------------------------------------------------------------

    def finalize_response(self, response: Response, rendered: HttpResponse) -> HttpResponse:
        """
        Final lifecycle hook to bind HTMX response header instructions 
        (e.g., HX-Trigger) into the native Django response headers.
        """
        # Utilize optimized pythonic truthiness check rather than '.empty'
        if response.htmx:
            rendered.headers.update(response.htmx.to_dict())

        return rendered