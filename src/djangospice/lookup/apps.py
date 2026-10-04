from djangospice.app_registry import AppConfig, Module

class LookupConfig(AppConfig):
    name = "djangospice.lookup"

    def ready(self):
        Module.discover("lookup")

    
namespace = LookupConfig.namespace