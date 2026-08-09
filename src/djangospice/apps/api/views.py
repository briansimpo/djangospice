from rest_framework import viewsets
from djangospice.rest.paginators import Pagination
from djangospice.apps.models import App
from .serializers import AppSerializer
from .filters import AppFilter


class AppViewSet(viewsets.ModelViewSet):
    queryset = App.objects.all()
    serializer_class = AppSerializer
    filterset_class = AppFilter
    pagination_class = Pagination
    search_fields = ['label']
    ordering_fields = ['label']
    ordering = ['label']

