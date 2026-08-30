from __future__ import annotations

from django.http import JsonResponse
from django.views import View

from .engine import LookupEngine
from .query import LookupQuery
from .resolver import LookupModelResolver


class LookupView(View):

    engine = LookupEngine()

    RESERVED_PARAMETERS = frozenset({
        "q",
        "page",
        "page_size",
    })

    def get(self, request, app_label: str, model_name: str):
        model = LookupModelResolver.resolve(
            app_label,
            model_name,
        )

        query = LookupQuery(
            model=model,
            search=request.GET.get(
                "q",
                "",
            ),
            filters=self.get_filters(
                request
            ),
            page=self.get_int(
                request.GET.get("page"),
                default=1,
            ),
            page_size=self.get_int(
                request.GET.get("page_size"),
                default=20,
            ),
        )

        result = self.engine.execute(
            query
        )

        return JsonResponse(
            result.as_dict()
        )

    def get_filters(self, request) -> dict[str, str]:

        return {
            key: value
            for key, value in request.GET.items()
            if key not in self.RESERVED_PARAMETERS
        }

    @staticmethod
    def get_int(value, *, default: int) -> int:

        try:
            return int(value)
        except (TypeError, ValueError):
            return default