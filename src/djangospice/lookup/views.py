from __future__ import annotations

from django.http import HttpRequest
from django.views import View

from .engine import LookupEngine
from .http import LookupHTTPAdapter, LookupWidgetHTTPAdapter
from .resolver import LookupDefinitionResolver, LookupModelResolver


class LookupView(View):
    """
    Generic HTTP endpoint for model lookups.

    The view is responsible only for Django request handling and
    resolving the model/lookup definition. HTTP parsing and lookup
    execution are delegated to their respective services.

    Example:

        /lookup/academic/course/

    Search:

        /lookup/academic/course/?q=computer

    Cascading:

        /lookup/academic/course/?program=<uuid>

    Multiple cascading dependencies:

        /lookup/academic/course/
            ?program=<uuid>
            &program__department=<uuid>
    """

    engine = LookupEngine()

    api_adapter = LookupHTTPAdapter(engine=engine)
    html_adapter = LookupWidgetHTTPAdapter(engine=engine)

    model_resolver = LookupModelResolver()
    definition_resolver = LookupDefinitionResolver()

    def get(self, request: HttpRequest, app_label: str, model_name: str):

        model = self.model_resolver.resolve(app_label, model_name)

        definition = self.definition_resolver.resolve(model)

        adapter = self.resolve_adapter(request)

        return adapter.execute(request, definition)
    

    def resolve_adapter(self, request: HttpRequest):
        if request.headers.get("HX-Request") == "true":
            return self.html_adapter

        if request.accepts("application/json"):
            return self.api_adapter

        return self.html_adapter