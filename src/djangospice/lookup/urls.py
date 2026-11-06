from django.urls import path

from .views import LookupView
from .apps import namespace

app_name = namespace

urlpatterns = [
    path(
        f"<slug:app_name>/<slug:model_name>/",
        LookupView.as_view(),
        name="lookup_view",
    ),
    
]