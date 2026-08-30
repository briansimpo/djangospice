from django.urls import path

from djangospice.lookup.views import LookupView


urlpatterns = [
    path(
        "lookup/<str:app_label>/<str:model_name>/",
        LookupView.as_view(),
        name="djangospice_lookup",
    ),
]