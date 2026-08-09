from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.http import Http404
from .models import App


class UserApps:
    """
    Manages user access to apps and services for a specific tenant.
    """

    def __init__(self, user):
        self.user = user
        self._apps_cache = None
        self._services_cache = None
       

    def _base_queryset(self, is_service=False):
        return App.objects.filter(
            is_active=True,
            is_service=is_service
        )

    def _filter_by_permissions(self, queryset):
        if self.user.is_superuser:
            return queryset.order_by("name")

        return (
            queryset.filter(
                Q(permissions__user=self.user) |
                Q(permissions__group__user=self.user)
            )
            .distinct()
            .order_by("name")
        )

    def get_apps(self):
        if self._apps_cache is not None:
            return self._apps_cache

        qs = self._base_queryset(is_service=False)
        self._apps_cache = self._filter_by_permissions(qs)
        return self._apps_cache

    def get_services(self):
        if self._services_cache is not None:
            return self._services_cache

        qs = self._base_queryset(is_service=True)
        self._services_cache = self._filter_by_permissions(qs)
        return self._services_cache

    def get_by_label(self, label, include_services=False):
        """
        Retrieve a single app/service by label WITH permission enforcement.
        """
        queryset = (
            self.get_services() if include_services else self.get_apps()
        )

        return queryset.filter(label=label).first()

    def check_access(self, label, include_services=False):
        """
        Validate access to an app/service.

        Raises:
            Http404: if app does not exist or inactive
            PermissionDenied: if user lacks access
        """
        app = self.get_by_label(label, include_services=include_services)

        if not app:
            raise Http404("App not found")

        if not app.is_active:
            raise Http404("App is inactive")

        # Optional: stricter permission check
        if not self.user.is_superuser and not self.user.has_module_perms(app.label):
            raise PermissionDenied("You do not have access to this app")

        return app