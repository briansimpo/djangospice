from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Self
from django.urls import reverse

from .fragments import HTMLFragment, HTMLFragments
from .document import Document
from .headers import HTMXHeaders
from .oob import OOBList


@dataclass(slots=True, kw_only=True)
class Response:
    """The single Djangospice response descriptor.It describes the
    response independently of Django's ``HttpResponse`` while providing the
    fluent htmx, oob, header, and document operations used by Djangospice.

    """

    template: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    content_value: str | bytes | None = None
    fragments: HTMLFragments = field(default_factory=HTMLFragments)

    _htmx: HTMXHeaders = field(default_factory=HTMXHeaders, repr=False)
    _oob: OOBList = field(default_factory=OOBList, repr=False)
    _document: Document | None = field(default=None, repr=False)

    @classmethod
    def render(
        cls,
        template: str,
        context: Mapping[str, Any] | None = None,
        *,
        status: int = 200,
        **values: Any,
    ) -> Self:
        payload = dict(context or {})
        payload.update(values)
        return cls(template=template, payload=payload, status_code=status)

    @classmethod
    def content(
        cls,
        content: str | bytes = b"",
        *,
        status: int = 200,
        content_type: str = "text/html; charset=utf-8",
        **headers: str,
    ) -> Self:
        result = cls(content_value=content, status_code=status)
        result.headers["Content-Type"] = content_type
        result.headers.update(headers)
        return result

    @classmethod
    def empty(cls, *, status: int = 204) -> Self:
        return cls(status_code=status)

    @classmethod
    def redirect_to(cls, to: str, *args: Any, status: int = 302, **kwargs: Any) -> Self:
        return cls.empty(status=status).header(
            "Location", reverse(to, args=args or None, kwargs=kwargs or None)
        )

    @classmethod
    def document(
        cls,
        content: str | bytes,
        *,
        filename: str | None = None,
        content_type: str | None = None,
        disposition: str = "attachment",
        title: str | None = None,
        status: int = 200,
    ) -> Self:
        result = cls(content_value=content, status_code=status)
        result._document = Document(
            filename=filename,
            content_type=content_type,
            disposition=disposition,
            title=title,
        )
        return result

    @property
    def has_document(self) -> bool:
        return self._document is not None

    @property
    def has_htmx(self) -> bool:
        return bool(self._htmx)

    @property
    def has_oob(self) -> bool:
        return bool(self._oob)

    def get_oob(self):
        return self._oob

    def status(self, status_code: int) -> Self:
        self.status_code = status_code
        return self

    def set(self, key: str, value: Any) -> Self:
        self.payload[key] = value
        return self

    def update(self, **values: Any) -> Self:
        self.payload.update(values)
        return self

    def header(self, name: str, value: str) -> Self:
        self.headers[name] = value
        return self

    # ------------------------------------------------------------------
    # htmx response directives
    # ------------------------------------------------------------------

    def target(self, selector: str | None) -> Self:
        self._htmx.retarget = selector
        return self

    def swap(self, strategy: str | None) -> Self:
        self._htmx.reswap = strategy
        return self

    def select(self, selector: str | None) -> Self:
        self._htmx.reselect(selector)
        return self

    def redirect(self, url: str) -> Self:
        self._htmx.redirect = url
        return self

    def location(
        self,
        path: str,
        *,
        target: str | None = None,
        swap: str | None = None,
        select: str | None = None,
        values: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Self:
        self._htmx.navigate(
            path, target=target, swap=swap, select=select,
            values=dict(values or {}), headers=dict(headers or {}),
        )
        return self

    def push_url(self, url: str | bool | None) -> Self:
        self._htmx.push_url = url
        return self

    def replace_url(self, url: str | bool | None) -> Self:
        self._htmx.replace_url = url
        return self

    def refresh(self, enabled: bool = True) -> Self:
        self._htmx.refresh = enabled
        return self

    def event(self, event: Any, detail: Any = None, **values: Any) -> Self:
        detail = values if values else detail
        self._htmx.trigger(event, detail)
        return self

    def after_swap(self, event: Any, detail: Any = None, **values: Any) -> Self:
        detail = values if values else detail
        self._htmx.after_swap(event, detail)
        return self

    def after_settle(self, event: Any, detail: Any = None, **values: Any) -> Self:
        detail = values if values else detail
        self._htmx.after_settle(event, detail)
        return self

    def fragment(self,template: str, **context: Any) -> Self:
        self.fragments.add(
            HTMLFragment(
                template_name=template,
                context=context,
            )
        )
        return self

    # ------------------------------------------------------------------
    # oob / documents
    # ------------------------------------------------------------------
    def oob(self, template: str, *, target: str | None = None, swap: str = "outerHTML", select: str | None = None, **context: Any) -> Self:
        fragment = HTMLFragment(
            template_name=template,
            context=context,
        )

        self._oob.add(
            fragment,
            target=target,
            swap=swap,
            select=select,
        )

        return self

    def oob_html(self, html: str, *, target: str | None = None, swap: str = "outerHTML",) -> Self:
        fragment = HTMLFragment.from_html(html)

        self._oob.add(
            fragment,
            target=target,
            swap=swap,
        )

        return self
   
    def oob_fragment(self, fragment: HTMLFragment, *, target: str | None = None, swap: str = "outerHTML", select: str | None = None) -> Self:
        self._oob.add(
            fragment,
            target=target,
            swap=swap,
            select=select,
        )
        return self

    def clear_oob(self) -> Self:
        self._oob.clear()
        return self