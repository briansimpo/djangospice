from djangospice.app_registry import AppConfig, Module

class EventsConfig(AppConfig):
    name = "djangospice.events"
 
    def ready(self) -> None:
        Module.discover("listeners")
        

namespace = EventsConfig.namespace