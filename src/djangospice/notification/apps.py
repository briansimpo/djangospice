from djangospice.package import AppConfig


class NotificationConfig(AppConfig):
    name = "djangospice.notification"

    
namespace = NotificationConfig.namespace