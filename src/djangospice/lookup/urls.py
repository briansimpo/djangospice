from django.urls import path

from .views import LookupView
from .conf import APP_NAME_URL_KEY, MODEL_NAME_URL_KEY
from .apps import namespace

app_name = namespace

urlpatterns = [
    path(
        f"{APP_NAME_URL_KEY}/{MODEL_NAME_URL_KEY}/",
        LookupView.as_view(),
        name="lookup_view",
    ),
    
]