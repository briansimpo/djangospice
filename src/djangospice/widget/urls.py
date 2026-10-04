from django.urls import path

from .views import WidgetView
from .conf import APP_NAME_URL_KEY, WIDGET_NAME_URL_KEY
from .apps import namespace


urlpatterns = [
    path(
        f"{APP_NAME_URL_KEY}/{WIDGET_NAME_URL_KEY}/", 
        WidgetView.as_view(),
        name=namespace,
    ),

]