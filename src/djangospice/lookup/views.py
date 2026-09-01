from __future__ import annotations

from django.views import View

from .engine import LookupEngine
from .http import LookupHTTPAdapter
from .resolver import LookupModelResolver, LookupDefinitionResolver


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
    adapter = LookupHTTPAdapter(engine=engine)
    definition_resolver = LookupDefinitionResolver()
    model_resolver = LookupModelResolver()

    def get(self, request, app_label: str, model_name: str):
        model = self.model_resolver.resolve(app_label, model_name)
        definition = self.definition_resolver.resolve(model)
        return self.adapter.execute(request,definition)