from __future__ import annotations

from collections.abc import Iterable

from drf_spectacular.utils import extend_schema
from rest_framework.routers import BaseRouter, DefaultRouter

from .permissions import ApiModelPermissions


class APIRouter(DefaultRouter):
    """
    DjangoSpice API router.

    Provides:

    - model-based route registration
    - automatic API permissions
    - OpenAPI tags
    - router composition
    - duplicate route detection

    The router is built entirely on Django REST Framework and has no
    dependency on the DjangoSpice runtime.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.registered: list[dict] = []

    def register_model(
        self,
        app_label: str,
        model_name: str,
        viewset,
        *,
        basename: str | None = None,
        permission_classes=None,
        swagger_tags: Iterable[str] | None = None,
    ) -> None:
        """
        Register a ViewSet using a Django app label and model name.

        Example:

            router.register_model(
                "students",
                "student",
                StudentViewSet,
            )

        produces:

            /students/student/
        """
        prefix = f"{app_label}/{model_name}".lower()

        self._register(
            prefix,
            viewset,
            basename=basename or model_name,
            permission_classes=permission_classes,
            swagger_tags=swagger_tags or [app_label.capitalize()],
            app_label=app_label,
            model_name=model_name,
        )

    def register_viewset(
        self,
        viewset,
        *,
        basename: str | None = None,
        permission_classes=None,
        swagger_tags: Iterable[str] | None = None,
    ) -> None:
        """
        Automatically register a ViewSet from its queryset model.
        """
        queryset = getattr(viewset, "queryset", None)

        if queryset is None:
            raise ValueError(
                f"{viewset.__name__} must define a queryset "
                "to auto-register."
            )

        model = getattr(queryset, "model", None)

        if model is None:
            raise ValueError(
                f"{viewset.__name__}.queryset must expose a model "
                "to auto-register."
            )

        self.register_model(
            model._meta.app_label,
            model._meta.model_name,
            viewset,
            basename=basename,
            permission_classes=permission_classes,
            swagger_tags=swagger_tags,
        )

    def include_router(
        self,
        other_router: BaseRouter,
        *,
        namespace: str | None = None,
    ) -> None:
        """
        Include all routes from another DRF router.
        """
        if not isinstance(other_router, BaseRouter):
            raise TypeError(
                "other_router must be an instance of "
                "rest_framework.routers.BaseRouter."
            )

        for prefix, viewset, options in other_router.registry:
            if namespace:
                prefix = (
                    f"{namespace.strip('/')}/"
                    f"{prefix.lstrip('/')}"
                )

            if self._is_registered(prefix):
               continue

            self._configure_permissions(viewset)

            DefaultRouter.register(
                self,
                prefix,
                viewset,
                **options,
            )

            self._record(
                prefix,
                viewset,
            )

    def include(
        self,
        routers: Iterable[BaseRouter],
        *,
        namespace: str | None = None,
    ) -> None:
        """
        Include multiple DRF routers.
        """
        for other_router in routers:
            self.include_router(
                other_router,
                namespace=namespace,
            )

    def _register(
        self,
        prefix: str,
        viewset,
        *,
        basename: str,
        permission_classes=None,
        swagger_tags: Iterable[str] | None = None,
        app_label: str | None = None,
        model_name: str | None = None,
    ) -> None:
        prefix = prefix.strip("/")

        if self._is_registered(prefix):
            raise ValueError(
                f"Duplicate API route prefix: {prefix!r}"
            )

        self._configure_permissions(
            viewset,
            permission_classes,
        )

        if swagger_tags:
            viewset = extend_schema(
                tags=list(swagger_tags),
            )(viewset)

        DefaultRouter.register(
            self,
            prefix,
            viewset,
            basename=basename,
        )

        self.registered.append(
            {
                "prefix": prefix,
                "app_label": app_label,
                "model_name": model_name,
                "viewset": viewset,
                "basename": basename,
            }
        )

    def _configure_permissions(
        self,
        viewset,
        permission_classes=None,
    ) -> None:
        if permission_classes is not None:
            viewset.permission_classes = permission_classes
        elif not getattr(viewset, "permission_classes", None):
            viewset.permission_classes = [
                ApiModelPermissions,
            ]

    def _record(
        self,
        prefix: str,
        viewset,
    ) -> None:
        model = getattr(
            getattr(viewset, "queryset", None),
            "model",
            None,
        )

        self.registered.append(
            {
                "prefix": prefix,
                "app_label": (
                    model._meta.app_label
                    if model else None
                ),
                "model_name": (
                    model._meta.model_name
                    if model else None
                ),
                "viewset": viewset,
                "basename": None,
            }
        )

    def _is_registered(self, prefix: str) -> bool:
        return any(
            registered["prefix"] == prefix
            for registered in self.registered
        )


router = APIRouter()