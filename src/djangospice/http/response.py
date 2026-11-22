
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self


from django.http import HttpResponse
from django.template.loader import render_to_string
from djangospice.files.helpers import download, stream

from .headers import HTMXHeaders


class Response(HttpResponse):
    """
    Djangospice's unified HTTP response.

    Extends Django's HttpResponse with:
        - Fluent response configuration.
        - Template rendering.
        - HTMX response headers.
        - Client-side navigation.
        - Browser events.
        - Response context management.

    HTMX headers are synchronized immediately whenever they change.
    """

    def __init__(
        self,
        content: str | bytes = b"",
        *,
        status: int = 200,
        content_type: str = "text/html; charset=utf-8",
        template: str | None = None,
        context: Mapping[str, Any] | None = None,
        htmx: HTMXHeaders | None = None,
    ) -> None:
        super().__init__(
            content=content,
            status=status,
            content_type=content_type,
        )

        self.template = template
        self.context: dict[str, Any] = dict(context or {})
        self.htmx = htmx if htmx is not None else HTMXHeaders()

        self._sync_htmx_headers()

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def create(cls, *, status: int = 200) -> Self:
        """Create an empty response."""
        return cls(status=status)

    @classmethod
    def from_template(
        cls,
        template: str,
        context: Mapping[str, Any] | None = None,
        *,
        status: int = 200,
        **values: Any,
    ) -> Self:
        """Create a response backed by a Django template."""
        ctx = dict(context or {})
        ctx.update(values)

        return cls(
            status=status,
            template=template,
            context=ctx,
        ).render()

    @classmethod
    def from_content(
        cls,
        content: str | bytes = b"",
        *,
        status: int = 200,
        content_type: str = "text/html; charset=utf-8",
        **headers: str,
    ) -> Self:
        """Create a response with direct content and optional headers."""
        response = cls(
            content=content,
            status=status,
            content_type=content_type,
        )

        for name, value in headers.items():
            response[name] = value

        return response

    @classmethod
    def redirect_to(
        cls,
        to: str,
        status: int = 302,
    ) -> Self:
        """Create an HTMX client-side redirect response."""
        return cls.create(status=status).redirect(to)

    @classmethod
    def navigate_to(
        cls,
        to: str,
        *,
        status: int = 200,
        target: str | None = None,
        swap: str | None = None,
        select: str | None = None,
    ) -> Self:
        """Create an HTMX client-side navigation response."""
        return cls.create(status=status).navigate(
            path=to,
            target=target,
            swap=swap,
            select=select,
        )

    @classmethod
    def download(
        cls,
        file,
        *,
        filename: str | None = None,
        content_type: str | None = None
    ):
        return download(
            file=file, 
            filename=filename, 
            content_type=content_type, 
        )

    @classmethod
    def stream(
        cls,
        streaming_content,
        *,
        content_type="application/octet-stream",
        filename=None,
        as_attachment=False,
        headers=None,
    ):
        return stream(
            streaming_content=streaming_content,
            content_type=content_type,
            filename=filename,
            as_attachment=as_attachment,
            headers=headers
        )

    # ------------------------------------------------------------------
    # Internal Synchronization
    # ------------------------------------------------------------------

    def _sync_htmx_headers(self) -> None:
        """Synchronize HTMX configuration with Django response headers."""

        for name in self.htmx.get_headers():
            if name in self.headers:
                del self.headers[name]

        for name, value in self.htmx.to_dict().items():
            self.headers[name] = value

    def _sync(self) -> Self:
        """Synchronize HTMX headers and return this response."""
        self._sync_htmx_headers()
        return self

    def finalize(self) -> Self:
        """
        Finalize the response before returning it to Django.

        Renders pending templates and synchronizes HTMX headers.
        """
        if self.template is not None:
            self.render()

        self._sync_htmx_headers()
        return self

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def has_htmx(self) -> bool:
        return bool(self.htmx)

    @property
    def has_template(self) -> bool:
        return bool(self.template)

    @property
    def has_content(self) -> bool:
        return bool(self.content)

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_template(self) -> str | None:
        return self.template

    def get_context(self) -> dict[str, Any]:
        return self.context

    def get_status_code(self) -> int:
        return self.status_code

    def get_headers(self) -> dict[str, str]:
        self._sync()
        return dict(self.headers.items())

    def get_content(self) -> str | bytes:
        return self.content

    def get_htmx(self) -> HTMXHeaders:
        return self.htmx

    # ------------------------------------------------------------------
    # Response Configuration
    # ------------------------------------------------------------------

    def status(self, status_code: int) -> Self:
        self.status_code = status_code
        return self

    def set(self, key: str, value: Any) -> Self:
        self.context[key] = value
        return self

    def update(self, **values: Any) -> Self:
        self.context.update(values)
        return self

    def header(self, name: str, value: str) -> Self:
        self[name] = value
        return self

    def set_content(self, content: str | bytes) -> Self:
        self.content = content
        return self

    def text(self, string: str) -> Self:
        self.content = string
        self["Content-Type"] = "text/plain; charset=utf-8"
        return self

    def html(self, content: Any) -> Self:
        self.content = str(content)
        self["Content-Type"] = "text/html; charset=utf-8"
        return self

    # ------------------------------------------------------------------
    # Template Rendering
    # ------------------------------------------------------------------

    def render(self, template: str | None = None, context: Mapping[str, Any] | None = None) -> Self:
        """Render a Django template into the response content."""
        if template is not None:
            self.template = template

        if context is not None:
            self.context.update(context)

        if self.template:
            self.content = render_to_string(
                self.template,
                self.context,
            )

        return self

    # ------------------------------------------------------------------
    # HTMX Navigation
    # ------------------------------------------------------------------

    def target(self, selector: str | None) -> Self:
        """Set HX-Retarget."""
        self.htmx.retarget(selector) if selector else None
        return self._sync()

    def swap(self, strategy: str | None) -> Self:
        """Set HX-Reswap."""
        if strategy:
            self.htmx.reswap(strategy)
        return self._sync()

    def focus(self, selector: str | None) -> Self:
        """Set HX-Reselect."""
        if selector:
            self.htmx.focus(selector)
        return self._sync()

    def redirect(self, url: str) -> Self:
        """Set HX-Redirect."""
        self.htmx.redirect(url)
        return self._sync()

    def navigate(self, path: str,*, target: str | None = None, swap: str | None = None, select: str | None = None) -> Self:
        """Set HX-Location for client-side navigation."""
        self.htmx.navigate(
            path,
            target=target,
            swap=swap,
            select=select,
        )
        return self._sync()

    def push_url(self, url: str | bool | None = True) -> Self:
        """Set HX-Push-Url."""
        self.htmx.push(url)
        return self._sync()

    def replace_url(self, url: str | bool | None = True) -> Self:
        """Set HX-Replace-Url."""
        self.htmx.replace(url)
        return self._sync()

    def refresh(self, enabled: bool = True) -> Self:
        """Set HX-Refresh."""
        self.htmx.refresh(enabled)
        return self._sync()

    # ------------------------------------------------------------------
    # HTMX Events
    # ------------------------------------------------------------------

    def trigger(self, event: str, **payload: Any) -> Self:
        """Trigger an immediate HTMX event."""
        self.htmx.trigger(event, **payload)
        return self._sync()

    def alert(self, message: str, type: str = "info") -> Self:
        """Trigger a client-side alert event."""
        return self.trigger(
            "show-alert",
            message=message,
            type=type,
        )

    def success(self, message: str) -> Self:
        return self.alert(message, "success")

    def error(self, message: str) -> Self:
        return self.alert(message, "error")

    def warning(self, message: str) -> Self:
        return self.alert(message, "warning")

    def info(self, message: str) -> Self:
        return self.alert(message, "info")

    def after_swap(self, event: str, **payload: Any) -> Self:
        """Trigger an event after the swap phase."""
        self.htmx.swap(event, **payload)
        return self._sync()

    def after_settle(self, event: str, **payload: Any) -> Self:
        """Trigger an event after the settle phase."""
        self.htmx.settle(event, **payload)
        return self._sync()

    # ------------------------------------------------------------------
    # HTMX Custom Headers
    # ------------------------------------------------------------------

    def htmx_header(self, name: str, value: Any) -> Self:
        """Set an additional custom HTMX response header."""
        self.htmx.set(name, value)
        return self._sync()

    # ------------------------------------------------------------------
    # Response Delivery
    # ------------------------------------------------------------------

    def __bytes__(self) -> bytes:
        self.finalize()
        return super().__bytes__()

    def __str__(self) -> str:
        self.finalize()
        return super().__str__()


    