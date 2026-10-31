from djangospice.package import AppConfig


class AppRegistryConfig(AppConfig):
    name = "djangospice.apps"
    label = "apps"
    verbose_name = "Apps"

    def ready(self):
        import djangospice.apps.receivers