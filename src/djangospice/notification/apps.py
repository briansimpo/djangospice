from djangospice.apps import AppConfig


class NotificationConfig(AppConfig):
    name = "djangospice.notification"
    label = "notification"
    
    
namespace = NotificationConfig.label