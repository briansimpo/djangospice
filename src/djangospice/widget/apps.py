from djangospice.app_registry import DjangospiceConfig


class WidgetConfig(DjangospiceConfig):
    name = "djangospice.widget"

    
namespace = WidgetConfig.namespace