from djangospice.app_registry import AppConfig


class TableConfig(AppConfig):
    name = "djangospice.table"

namespace = TableConfig.namespace