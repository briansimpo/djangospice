from __future__ import annotations

from typing import Any

from django.urls import reverse
from django.http import HttpRequest, HttpResponse

from .renderer import ResponseRenderer
from .response import Response


renderer = ResponseRenderer()


def response(
    content: str | bytes | Response | None = None,
    *,
    status: int = 200,
    content_type: str = "text/html; charset=utf-8",
    **headers: str,
) -> Response:
    """
    Create a Djangospice response descriptor.

    This is the primary shortcut for constructing responses in Django views.
    It accepts raw HTML content, an existing Response descriptor, or no
    content to create an empty response.

    The returned descriptor supports fluent configuration of status codes,
    headers, HTMX directives, out-of-band swaps, fragments, and documents.
    It is materialized into a Django HttpResponse by the response renderer.

    Args:
        content: Response body as a string or bytes, an existing Response
            descriptor, or None for an empty response.
        status: HTTP status code. Defaults to 200.
        content_type: Content-Type header for raw HTML or bytes.
            Defaults to text/html; charset=utf-8.
        **headers: Additional HTTP response headers.

    Returns:
        Response: A configurable Djangospice response descriptor.

    Examples:
        Return a simple HTML response:

            return response("Hello world")

        Return an empty response:

            return response()

        Configure an empty response:

            return response().status(204).emit("updated")

        Configure an HTML response:

            return (
                response("<h1>Hello</h1>")
                .target("#content")
                .swap("innerHTML")
                .emit("content_updated")
            )

        Set custom headers:

            return response("Created", status=201, X_Custom_Header="value")

        Use an existing descriptor:

            return response(Response.render("home.html"))
    """
    if isinstance(content, Response):
        return content

    if content is None:
        return Response.empty(status=status)

    return Response.html(
        content,
        status=status,
        content_type=content_type,
        **headers,
    )


def dispatch_response(
    request: HttpRequest,
    response: Response | HttpResponse,
) -> HttpResponse:
    """
    Dispatch a response descriptor or an existing Django HTTP response.

    Converts Djangospice Response descriptors into Django HttpResponse
    instances using the configured ResponseRenderer.

    Existing Django HttpResponse instances are returned unchanged, allowing
    Djangospice response handling to coexist with Django's native response
    classes and third-party responses.

    Args:
        request: The current Django request.
        response: A Djangospice Response descriptor or an existing Django
            HttpResponse.

    Returns:
        HttpResponse: The materialized or unchanged HTTP response.

    Examples:
        return dispatch_response(request, response("Hello world"))

        return dispatch_response(request, HttpResponse("Hello world"))
    """
    if isinstance(response, Response):
        return renderer.render(response, request)

    return response


def htmx_render(
    request: HttpRequest,
    template: str,
    context: dict[str, Any] | None = None,
    **kwargs: Any,
) -> HttpResponse:
    """
    Render a template and return it as an HTMX-compatible response.

    This shortcut is intended for rendering HTML fragments and partial
    templates directly from Django views.

    Additional keyword arguments are merged into the template context.
    The resulting Response descriptor is passed through the standard
    response renderer, ensuring that HTMX directives, fragments, headers,
    and out-of-band swaps are handled consistently.

    Args:
        request: The current Django request.
        template: Template path to render.
        context: Optional template context dictionary.
        **kwargs: Additional template context variables.

    Returns:
        HttpResponse: The rendered HTML response.

    Examples:
        return htmx_render(
            request,
            "users/partials/user_list.html",
            {"users": users},
        )

        return htmx_render(
            request,
            "users/partials/user_detail.html",
            user=user,
        )
    """
    result = Response.render(
        template=template,
        context=context,
        **kwargs,
    )

    return dispatch_response(request=request, response=result)


def htmx_redirect(
    to: str,
    *,
    safe: bool = False,
    app_name: str | None = None,
    args: tuple | list | None = None,
    kwargs: dict[str, Any] | None = None,
    **options: Any,
) -> Response:
    """
    Build an HTMX redirect response.

    Supports both direct URLs and Django URL names. When ``safe=True``,
    the destination is resolved using Django's URL reversing mechanism.
    An optional application namespace can be supplied through ``app_name``.

    The returned Response descriptor uses the HX-Redirect response header,
    instructing HTMX to perform a full browser navigation.

    Args:
        to: Destination URL or Django URL pattern name.
        safe: Whether to resolve ``to`` using Django's reverse().
            Defaults to False.
        app_name: Optional Django URL namespace used when resolving a
            named URL.
        args: Positional arguments for URL reversing.
        kwargs: Keyword arguments for URL reversing.
        **options: Additional response options. Supports ``status``,
            which defaults to 204.

    Returns:
        Response: A configurable HTMX redirect response descriptor.

    Examples:
        Redirect to a URL:

            return htmx_redirect("/dashboard/")

        Redirect using a named URL:

            return htmx_redirect("dashboard", safe=True)

        Redirect using an application namespace:

            return htmx_redirect(
                "detail",
                safe=True,
                app_name="products",
                kwargs={"pk": 10},
            )

        Customize the response:

            return htmx_redirect(
                "dashboard",
                safe=True,
                status=200,
            )
    """
    status = options.pop("status", 204)

    if safe:
        view_name = f"{app_name}:{to}" if app_name else to
        to = reverse(view_name, args=args, kwargs=kwargs)

    return Response.empty(status=status).redirect(to)