from djangospice.package import AppConfig


class WidgetConfig(AppConfig):
    name = "djangospice.widget"

    def ready(self):
        self.load_module("widgets")
        
    
namespace = WidgetConfig.namespace