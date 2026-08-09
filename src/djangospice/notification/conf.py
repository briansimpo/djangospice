from django.conf import settings
from .enums import Channel

DEFAULT_PROVIDERS = {
    Channel.EMAIL: {
        "BACKEND": "djangospice.notification.channels.EmailChannel"
    }
}

class NotificationSettings:
    
    @property
    def PROVIDERS(self):
        """
        Merge developer settings with internal defaults. 
        If a developer defines a channel (like 'email'), it overwrites the default 'email'.
        """
        user_providers = getattr(settings, 'NOTIFICATION_PROVIDERS', {})
        
        merged_providers = DEFAULT_PROVIDERS.copy()
        merged_providers.update(user_providers)
        
        return merged_providers

notification_settings = NotificationSettings()