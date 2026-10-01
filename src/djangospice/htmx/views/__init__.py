from .generic import (
    HTMXView,
    HTMXTemplateView,
    HTMXListView,
    HTMXDetailView,
    HTMXFormView,
    HTMXCreateView,
    HTMXUpdateView,
    HTMXDeleteView,
)

from .mixins import (
    HTMXTemplateMixin,
    HTMXFormMixin,
    HTMXModalMixin,
    HTMXTabMixin,
)

from .tabs import (
    HTMXTemplateTabView,
    HTMXDetailTabView,
    HTMXCreateTabView,
    HTMXUpdateTabView,
    HTMXDeleteTabView,
    HTMXTabContainerView,
    HTMXObjectTabContainerView,
)

from .modals import (
    HTMXModal,
    HTMXFormModal,
    HTMXCreateModal,
    HTMXUpdateModal,
    HTMXDeleteModal,
)

from .search import (
    HTMXSearchMixin,
    HTMXSearchView,
    HTMXFilterView,
    HTMXSearchFilterView,
)

__all__ = [
    # Generic views
    "HTMXView",
    "HTMXTemplateView",
    "HTMXListView",
    "HTMXDetailView",
    "HTMXFormView",
    "HTMXCreateView",
    "HTMXUpdateView",
    "HTMXDeleteView",

    # Mixins
    "HTMXTemplateMixin",
    "HTMXFormMixin",
    "HTMXModalMixin",
    "HTMXTabMixin",

    # Tabs
    "HTMXTemplateTabView",
    "HTMXDetailTabView",
    "HTMXCreateTabView",
    "HTMXUpdateTabView",
    "HTMXDeleteTabView",
    "HTMXTabContainerView",
    "HTMXObjectTabContainerView",

    # Modals
    "HTMXModal",
    "HTMXFormModal",
    "HTMXCreateModal",
    "HTMXUpdateModal",
    "HTMXDeleteModal",

    # Search / filtering
    "HTMXSearchMixin",
    "HTMXSearchView",
    "HTMXFilterView",
    "HTMXSearchFilterView",
]