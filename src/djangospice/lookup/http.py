from __future__ import annotations

from typing import Any

from django.http import HttpRequest, JsonResponse

from .definition import LookupDefinition
from .engine import LookupEngine
from .query import LookupQuery
from .result import LookupResult


class LookupHTTPAdapter:
    """
    HTTP adapter for the lookup engine.

    Converts an HTTP GET request into a LookupQuery and
    converts a LookupResult into a JsonResponse.

    The adapter does not perform lookup logic or ORM operations.
    """

    SEARCH_PARAMETER = "q"
    PAGE_PARAMETER = "page"
    PAGE_SIZE_PARAMETER = "page_size"

    def __init__(self, engine: LookupEngine | None = None) -> None:
        self.engine = engine or LookupEngine()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def build_query(self, request: HttpRequest, definition: LookupDefinition) -> LookupQuery:
        """
        Build a LookupQuery from an HTTP request.
        """

        return LookupQuery(
            definition=definition,
            search=self.get_search(request),
            dependencies=self.get_dependencies(
                request,
                definition,
            ),
            page=self.get_page(request),
            page_size=self.get_page_size(request),
        )

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(self, request: HttpRequest, definition: LookupDefinition) -> JsonResponse:
        """
        Execute a lookup request and return its HTTP response.
        """

        query = self.build_query(request, definition)

        result = self.engine.execute(query)

        return self.response(result)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def get_search(self, request: HttpRequest) -> str:
        """
        Return the lookup search term.
        """

        return request.GET.get(
            self.SEARCH_PARAMETER,
            "",
        ).strip()

    # ------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------

    def get_dependencies(self, request: HttpRequest, definition: LookupDefinition) -> dict[str, Any]:
        """
        Extract values for declared lookup dependencies.

        Only dependencies declared by ``definition.depends_on``
        are accepted.

        Example:

            depends_on=(
                Program,
                "program__department",
            )

        Request:

            ?program=<uuid>
            &program__department=<uuid>

        Result:

            {
                "program": "<uuid>",
                "program__department": "<uuid>",
            }
        """

        dependencies: dict[str, Any] = {}

        for dependency in definition.dependencies:
            path = dependency.path

            values = request.GET.getlist(
                path,
            )

            values = self.clean_values(
                values,
            )

            if not values:
                continue

            dependencies[path] = (
                values[0]
                if len(values) == 1
                else values
            )

        return dependencies

    @staticmethod
    def clean_values(values: list[str]) -> list[str]:
        """
        Remove empty values and normalize whitespace.
        """

        return [
            value.strip()
            for value in values
            if value.strip()
        ]

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def get_page(self, request: HttpRequest) -> int:
        return self.parse_positive_int(
            request.GET.get(
                self.PAGE_PARAMETER,
            ),
            default=1,
        )

    def get_page_size(self, request: HttpRequest) -> int | None:
        value = request.GET.get(
            self.PAGE_SIZE_PARAMETER,
        )

        if value in (None, ""):
            return None

        return self.parse_positive_int(
            value,
            default=None,
        )

    @staticmethod
    def parse_positive_int(value: str | None,*,default: int | None) -> int | None:
        """
        Parse a positive integer.

        Invalid or non-positive values fall back to ``default``.
        """

        if value in (None, ""):
            return default

        try:
            value = int(value)
        except (TypeError, ValueError):
            return default

        if value < 1:
            return default

        return value

    # ------------------------------------------------------------------
    # Response
    # ------------------------------------------------------------------

    def response(self, result: LookupResult) -> JsonResponse:
        """
        Convert a LookupResult into an HTTP response.

        Model objects are deliberately excluded from the HTTP
        representation.
        """

        return JsonResponse(
            result.as_dict(
                include_objects=False,
            )
        )