from djangospice.html.skeleton import Skeleton


class TableSkeleton(Skeleton):
    template_name = "table/skeleton.html"

    def __init__(self, rows=5, columns=5, **kwargs):
        self.rows = rows
        self.columns = columns

        super().__init__(**kwargs)

    def get_context(self):
        return {
            **super().get_context(),
            "rows": range(self.rows),
            "columns": range(self.columns),
        }