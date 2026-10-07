from django.apps import AppConfig


class AppRegistryConfig(AppConfig):
    name = "djangospice.app_registry"
    label = "app_registry"
    verbose_name = "App Registry"

    def ready(self):
        import djangospice.app_registry.receivers