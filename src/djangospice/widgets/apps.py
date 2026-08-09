from djangospice.apps import AppConfig


class WidgetsConfig(AppConfig):
    name = "djangospice.widgets"
    label = "widgets"
    
    
namespace = WidgetsConfig.label