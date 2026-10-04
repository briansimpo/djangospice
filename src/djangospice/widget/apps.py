from djangospice.app_registry import AppConfig


class WidgetConfig(AppConfig):
    name = "djangospice.widget"

    
namespace = WidgetConfig.namespace