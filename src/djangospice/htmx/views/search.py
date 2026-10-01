from __future__ import annotations

from django_filters.views import FilterView

from .mixins import HTMXTemplateMixin, HTMXSearchMixin
from .generic import HTMXListView




class HTMXSearchView(
    HTMXSearchMixin,
    HTMXListView,
):
    """
    HTMX-enabled searchable Django ListView.
    """

    pass



class HTMXFilterView(
    HTMXTemplateMixin,
    FilterView,
):
    pass


class HTMXSearchFilterView(
    HTMXSearchMixin,
    HTMXTemplateMixin,
    FilterView,
):
    pass