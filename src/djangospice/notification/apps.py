from djangospice.app_registry import DjangospiceConfig


class NotificationConfig(DjangospiceConfig):
    name = "djangospice.notification"

    
namespace = NotificationConfig.namespace