from djangospice.app_registry import AppConfig

class LookupConfig(AppConfig):
    name = "djangospice.lookup"

    def ready(self):
        self.load_module("lookup")

    
namespace = LookupConfig.namespace