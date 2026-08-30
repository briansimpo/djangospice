from djangospice.apps import AppConfig


class LookupConfig(AppConfig):
    name = "djangospice.lookup"
    label = "lookup"
    
    
namespace = LookupConfig.namespace