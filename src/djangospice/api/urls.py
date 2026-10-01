from django.urls import include, path

from .discovery import discover_routers
from .router import router


router.include(
    discover_routers(),
)


urlpatterns = [
    path("", include(router.urls)),
]