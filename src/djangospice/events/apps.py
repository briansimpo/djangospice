from djangospice.app_registry import DjangospiceConfig, Module

class EventsConfig(DjangospiceConfig):
    name = "djangospice.events"
 
    def ready(self) -> None:
        Module.discover("listeners")
        

namespace = EventsConfig.namespace