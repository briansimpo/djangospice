from djangospice.app_registry import DjangospiceConfig, Module

class LookupConfig(DjangospiceConfig):
    name = "djangospice.lookup"

    def ready(self):
        Module.discover("lookup")

    
namespace = LookupConfig.namespace