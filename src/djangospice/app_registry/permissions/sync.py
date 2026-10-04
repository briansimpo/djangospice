from __future__ import annotations

from collections.abc import Iterable

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


from djangospice.app_registry.metadata import Permission
from djangospice.app_registry.models import AppPermission

from .default import APP_ACCESS


class PermissionSynchronizer:
    """Synchronize app-level declarations into Django's auth tables."""

    content_type_model = "__djangospice_app__"

    def sync(self, app, declarations: Iterable[Permission]):
        desired = {APP_ACCESS.codename: APP_ACCESS}
        desired.update({item.codename: item for item in declarations})

        content_type, _ = ContentType.objects.get_or_create(
            app_label=app.app_label,
            model=self.content_type_model,
        )

        with transaction.atomic():
            records = []
            for declaration in desired.values():
                permission, _ = Permission.objects.update_or_create(
                    content_type=content_type,
                    codename=declaration.codename,
                    defaults={"name": declaration.name},
                )
                record, _ = AppPermission.objects.update_or_create(
                    app=app,
                    codename=declaration.codename,
                    defaults={
                        "permission": permission,
                        "name": declaration.name,
                        "description": declaration.description,
                    },
                )
                records.append(record)

            stale = AppPermission.objects.filter(app=app).exclude(
                codename__in=desired,
            )
            stale.delete()

        return records

    def remove(self, app) -> None:
        records = AppPermission.objects.filter(app=app)
        permission_ids = list(records.values_list("permission_id", flat=True))
        records.delete()
        Permission.objects.filter(id__in=permission_ids).delete()

        ContentType.objects.filter(
            app_label=app.app_label,
            model=self.content_type_model,
        ).delete()
      


permission_sync = PermissionSynchronizer()
