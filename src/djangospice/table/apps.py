from djangospice.app_registry import DjangospiceConfig


class TableConfig(DjangospiceConfig):
    name = "djangospice.table"

namespace = TableConfig.namespace