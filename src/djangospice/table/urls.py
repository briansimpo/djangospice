from django.urls import path
from djangospice.widget.conf import APP_NAME_URL_KEY, WIDGET_NAME_URL_KEY
from .apps import namespace
from .views import DataTableView

app_name = namespace

urlpatterns = [
    path(
        f"{APP_NAME_URL_KEY}/{WIDGET_NAME_URL_KEY}/", 
        DataTableView.as_view(),
        name="datatable_view",
    ),

]