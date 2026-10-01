from __future__ import annotations


from django.http import HttpRequest, HttpResponse

from .rendering.content import ContentRenderer
from .rendering.document import DocumentRenderer
from .rendering.fragments import FragmentRenderer
from .rendering.headers import HeaderRenderer
from .rendering.oob import OOBRenderer

from .response import Response



class ResponseRenderer:
    """
    Internal coordinator responsible for materializing a
    Response into Django's HttpResponse.
    """

    def __init__(
        self,
        *,
        content: ContentRenderer | None = None,
        fragments: FragmentRenderer | None = None,
        oob: OOBRenderer | None = None,
        headers: HeaderRenderer | None = None,
        documents: DocumentRenderer | None = None,
    ) -> None:
        self.content = content or ContentRenderer()

        self.fragments = fragments or FragmentRenderer()

        self.oob = oob or OOBRenderer(
            fragment_renderer=self.fragments,
        )

        self.headers = headers or HeaderRenderer()

        self.documents = documents or DocumentRenderer()

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def render(
        self,
        response: Response,
        request: HttpRequest | None = None,
    ) -> HttpResponse:
        if response.has_document:
            return self.render_document(
                response,
                request=request,
            )

        return self.render_html(
            response,
            request=request,
        )

    # ------------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------------

    def render_html(
        self,
        response: Response,
        *,
        request: HttpRequest | None = None,
    ) -> HttpResponse:
        content = self.content.render(
            response,
            request=request,
        )

        if response.has_oob:
            content += self.oob.render(
                response.get_oob(),
                request=request,
            )

        http_response = HttpResponse(
            content=content,
            status=response.status_code,
        )

        self.headers.render(
            response,
            http_response,
        )

        return http_response

    # ------------------------------------------------------------------
    # Document
    # ------------------------------------------------------------------

    def render_document(
        self,
        response: Response,
        *,
        request: HttpRequest | None = None,
    ) -> HttpResponse:
        http_response = self.documents.render(
            response,
            request=request,
        )

        self.headers.render(
            response,
            http_response,
        )

        return http_response