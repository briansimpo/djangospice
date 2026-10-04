from django.apps import AppConfig


class AppRegistryConfig(AppConfig):
    name = "djangospice.app_registry"
    label = "app_registry"

    def ready(self):
        import djangospice.app_registry.receivers