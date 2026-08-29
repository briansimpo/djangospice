from djangospice.apps import AppConfig


class TableConfig(AppConfig):
    name = "djangospice.table"
    label = "table"
    
    
namespace = TableConfig.namespace