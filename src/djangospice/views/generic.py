from django.http import Http404
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .mixins import HTMXTemplateMixin


class HTMXView(HTMXTemplateMixin,View):
    """
    Base HTMX-enabled Django View.

    Prefer composing HTMXTemplateMixin directly with a Django generic
    view when a specialized generic view is required.
    """

    pass


class HTMXTemplateView(HTMXTemplateMixin, TemplateView):
    """
    HTMX-enabled TemplateView.
    """

    pass


class HTMXListView(HTMXTemplateMixin, ListView):
    """
    HTMX-enabled ListView.
    """

    pass


class HTMXDetailView(HTMXTemplateMixin, DetailView):
    """
    HTMX-enabled DetailView.
    """

    pass


class HTMXFormView(HTMXTemplateMixin, FormView):
    """
    HTMX-enabled FormView.
    """

    pass


class HTMXCreateView(HTMXTemplateMixin, CreateView):
    """
    HTMX-enabled CreateView.
    """

    pass


class HTMXUpdateView(HTMXTemplateMixin, UpdateView):
    """
    HTMX-enabled UpdateView.
    """

    pass


class HTMXDeleteView(HTMXTemplateMixin, DeleteView):
    """
    HTMX-enabled DeleteView.
    """

    pass


class HTMXObjectView(TemplateView):
    model = None
    context_object_name = None
    object_parameter = "pk"

    def get_queryset(self):
        if self.model is None:
            raise NotImplementedError("Define model.")

        return self.model._default_manager.all()

    def get_object(self):
        object_id = self.kwargs.get(self.object_parameter)

        if object_id is None:
            return None

        return self.get_queryset().filter(pk=object_id).first()

    def get_context_object_name(self, obj):
        if self.context_object_name:
            return self.context_object_name

        return obj._meta.model_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        obj = self.get_object()

        if obj is None:
            raise Http404

        context["object"] = obj
        context[self.get_context_object_name(obj)] = obj

        return context