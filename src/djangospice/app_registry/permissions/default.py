from __future__ import annotations

from djangospice.app_registry.metadata import Permission


APP_ACCESS = Permission(
    codename="access",
    name="Access application",
    description="Allows the user to access the application.",
)
