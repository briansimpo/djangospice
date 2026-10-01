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


class HTMXDetailView(HTMXTemplateMixin,DetailView):
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