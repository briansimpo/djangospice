from django.urls import path

from .views import WidgetView

urlpatterns = [
    path(
        "widgets/<slug:app_label>/<slug:name>/", 
        WidgetView.as_view(),
        name="djangospice_widget",
    ),

]