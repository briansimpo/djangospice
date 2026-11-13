import django_tables2 as tables

class BaseTable(tables.Table):
    
    class Meta:
        abstract = True
        
    