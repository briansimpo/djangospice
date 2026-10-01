from djangospice.config import AppConfig


class NotificationConfig(AppConfig):
    name = "djangospice.notification"
    label = "notification"
    
    
namespace = NotificationConfig.namespace