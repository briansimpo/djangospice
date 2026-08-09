from django.urls import path

from .views import WidgetView

urlpatterns = [
    path(
        "<slug:app_label>/widgets/<slug:name>/", 
        WidgetView.as_view(),
        name="djangospice_widget",
    ),

]