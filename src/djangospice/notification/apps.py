from djangospice.package import AppConfig


class NotificationConfig(AppConfig):
    name = "djangospice.notification"

    def ready(self):
        self.load_module("notifications")

    
namespace = NotificationConfig.namespace