import django_tables2 as tables
from djangospice.web.urls import get_view_name


def table_link(view_name, namespace=None, primary_key="pk"):
    view_name = get_view_name(view_name, namespace)
    args = tables.A(primary_key)
    return {"viewname": view_name, "args": [args]}