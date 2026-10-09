from django.urls import path

from .views import WidgetView
from .conf import APP_NAME_URL_KEY, WIDGET_NAME_URL_KEY
from .apps import namespace

app_name = namespace

urlpatterns = [
    path(
        f"{APP_NAME_URL_KEY}/{WIDGET_NAME_URL_KEY}/", 
        WidgetView.as_view(),
        name="widget_view",
    ),

]