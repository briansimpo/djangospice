from djangospice.config import AppConfig, Module

class EventsConfig(AppConfig):
    name = "djangospice.events"
    label = "events"
 
    def ready(self) -> None:
        Module.discover("listeners")
        

namespace = EventsConfig.namespace