from django.db.models.signals import post_migrate

from djangospice.config import AppConfig
from .installer import AppInstaller


class AppsConfig(AppConfig):
    name = "djangospice.apps"
    label = "apps"
 
    def install(self, **kwargs):
        installer = AppInstaller(self)
        installer.load_tasks()
        
    def ready(self) -> None:
        post_migrate.connect(self.install, sender=self)
        

namespace = AppsConfig.namespace