from rest_framework.permissions import BasePermission


class ApiModelPermissions(BasePermission):

    # Standard HTTP method to permission mapping
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def has_permission(self, request, view):
        # Superuser bypass
        if request.user.is_superuser:
            return True

        if not hasattr(view, 'queryset') or view.queryset is None:
            return False

        model = view.queryset.model

        # Determine the HTTP method
        method = request.method.upper()

        # Determine the permission(s) needed
        perms_needed = self.perms_map.get(method, [])

        # Check if this is a custom action
        if getattr(view, 'action', None):
            # For custom actions, use 'change' permission by default
            perms_needed = [f"{model._meta.app_label}.change_{model._meta.model_name}"]

        # Check if user has any required permission
        for perm in perms_needed:
            if request.user.has_perm(perm):
                return True

        return False
