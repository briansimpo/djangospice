from djangospice.package import AppConfig


class WidgetConfig(AppConfig):
    name = "djangospice.widget"
        
    
namespace = WidgetConfig.namespace