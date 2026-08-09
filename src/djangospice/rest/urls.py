from django.urls import include, path
from .discovery import discover_routers
from .router import router

discover_routers()

urlpatterns = [
    path("", include(router.registry.urls)),
]