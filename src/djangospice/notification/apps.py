from djangospice.app_registry import AppConfig


class NotificationConfig(AppConfig):
    name = "djangospice.notification"

    
namespace = NotificationConfig.namespace