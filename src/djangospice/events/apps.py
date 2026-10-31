from djangospice.package import AppConfig


class EventsConfig(AppConfig):
    name = "djangospice.events"
 
    def ready(self) -> None:
        self.load_module("listeners")
        

namespace = EventsConfig.namespace