import django_tables2 as tables
from .columns import SelectionColumn

class BaseTable(tables.Table):
    selection = SelectionColumn(
        accessor="pk", 
        exclude_from_export=True,
        orderable=False
    )
    
    class Meta:
        abstract = True
        
    