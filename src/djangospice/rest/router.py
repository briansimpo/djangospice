from rest_framework.routers import DefaultRouter
from drf_spectacular.utils import extend_schema
from .permissions import ApiModelPermissions


class Router:
    def __init__(self):
        self.registry = DefaultRouter()
        self.registered = []

    def register(self, app_label, model_name, viewset, basename=None):
        prefix = f"{app_label}/{model_name}".lower()

        # Apply default admin RBAC if no custom permission class is set
        if not getattr(viewset, 'permission_classes', None):
            viewset.permission_classes = [ApiModelPermissions]

        self.registry.register(prefix, viewset, basename=basename or model_name)
        self.registered.append((app_label, model_name, viewset))

    def register_viewset(self, viewset, basename=None, permission_classes=None):

        if not hasattr(viewset, "queryset") or viewset.queryset is None:
            raise ValueError(f"{viewset.__name__} must define a queryset to auto-register")

        model = viewset.queryset.model
        app_label = model._meta.app_label

        # Pluralized model name
        model_name =  model._meta.model_name

        # Assign Swagger tag like: Admin / Users
        swagger_tag = app_label.capitalize()
        viewset = extend_schema(tags=[swagger_tag])(viewset)

        if permission_classes is not None:
            viewset.permission_classes = permission_classes
        elif not getattr(viewset, 'permission_classes', None):
            viewset.permission_classes = [ApiModelPermissions]

        self.register(app_label, model_name, viewset, basename or model_name)

    @property
    def urls(self):
        return self.registry.urls

# Global instance
router = Router()
