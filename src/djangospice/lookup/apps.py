from djangospice.package import AppConfig

class LookupConfig(AppConfig):
    name = "djangospice.lookup"

    def ready(self):
        self.load_module("lookup")

    
namespace = LookupConfig.namespace