from __future__ import annotations

from django.http import HttpRequest
from django.template.loader import render_to_string

from djangospice.htmx.fragments import HTMLFragment



class FragmentRenderer:
    """
    Renders Djangospice HTML fragments.
    """

    def render(
        self,
        fragment: HTMLFragment,
        *,
        request: HttpRequest | None = None,
    ) -> str:
        if getattr(fragment, "html", None) is not None:
            return fragment.html

        template_name = fragment.template_name

        if not template_name:
            return ""

        context = fragment.get_context()

        return render_to_string(
            template_name,
            context,
            request=request,
        )

    def render_many(
        self,
        fragments,
        *,
        request: HttpRequest | None = None,
    ) -> str:
        return "".join(
            self.render(
                fragment,
                request=request,
            )
            for fragment in fragments
        )