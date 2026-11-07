from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views import View

from djangospice.exec.identity import ClassIdentity

from .engine import LookupEngine
from .adapter import LookupAdapter
from .security import LookupSecurity
from .resolver import LookupResolver
from .registry import lookup_registry


class LookupView(View):
    """
    Generic HTTP endpoint for model lookups.

    The view is responsible only for Django request handling and
    resolving the model/lookup definition. HTTP parsing and lookup
    execution are delegated to their respective services.

    """

    engine = LookupEngine()

    adapter = LookupAdapter(engine=engine)

    resolver = LookupResolver(lookup_registry)

    security = LookupSecurity.defaults()

    def get(self, request: HttpRequest, app_name: str, model_name: str) -> JsonResponse:

        identifier = ClassIdentity.build(app_name, model_name).to_string()

        self.security.authenticate(request, identifier)

        definition = self.resolver.resolve(identifier)

        result = self.adapter.execute(request, definition)

        return JsonResponse(result.as_dict())