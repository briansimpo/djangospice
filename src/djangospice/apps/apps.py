from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .discovery import ModuleDiscovery
from .bootstrap import Bootstrap
from .installer import AppInstaller


class AppsConfig(AppConfig):
    name = "djangospice.apps"
    label = "apps"
 
    def install(self, **kwargs):
        installer = AppInstaller(self)
        installer.load_tasks()
        
    def ready(self) -> None:
        """
        Lifecycle hook triggered by Django when the registry is fully populated.
        Launches the djangospice application bootstrapping process.
        """
        post_migrate.connect(self.install, sender=self)
        ModuleDiscovery.discover("listeners")
        ModuleDiscovery.discover("widgets")
        Bootstrap().run()
        

