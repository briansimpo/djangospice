from __future__ import annotations

from html import escape

from django.http import HttpRequest

from djangospice.htmx.oob import OOBList, OOBEntry

from .fragments import FragmentRenderer


class OOBRenderer:
    """
    Materializes OOB fragments into HTMX-compatible response content.
    """

    def __init__(
        self,
        fragment_renderer: FragmentRenderer | None = None,
    ) -> None:
        self.fragments = (
            fragment_renderer
            or FragmentRenderer()
        )

    def render(
        self,
        oob: OOBList,
        *,
        request: HttpRequest | None = None,
    ) -> str:
        return "".join(
            self.render_entry(
                entry,
                request=request,
            )
            for entry in oob
        )

    def render_entry(
        self,
        entry: OOBEntry,
        *,
        request: HttpRequest | None = None,
    ) -> str:
        html = self.fragments.render(
            entry.fragment,
            request=request,
        )

        return self._compile(
            html,
            entry,
        )

    def _compile(
        self,
        html: str,
        entry: OOBEntry,
    ) -> str:
        swap = escape(
            entry.swap,
            quote=True,
        )

        target = (
            f' {entry.target}'
            if entry.target
            else ""
        )

        # The rendered fragment itself is expected to contain
        # the appropriate target element. HTMX can therefore use
        # the selector form directly.
        if entry.target:
            swap_value = (
                f"{swap}:{escape(entry.target, quote=True)}"
            )
        else:
            swap_value = swap

        return (
            f'<template '
            f'hx-swap-oob="{swap_value}">'
            f'{html}'
            f'</template>'
        )