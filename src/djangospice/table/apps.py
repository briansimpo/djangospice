from djangospice.config import AppConfig


class TableConfig(AppConfig):
    name = "djangospice.table"

    
namespace = TableConfig.namespace