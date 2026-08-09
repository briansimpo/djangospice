import django_filters
from django.db.models import QuerySet


class OptionFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    value = django_filters.CharFilter(field_name="value", lookup_expr="icontains")
    slug = django_filters.CharFilter(field_name="slug", lookup_expr="icontains")
    code = django_filters.CharFilter(field_name="code", lookup_expr="icontains")

    class Meta:
        model = None  # to be defined in subclass
        fields = ["id", "name", "value", "slug", "code"]


class BaseFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method="search", label="Search")
    
    def evaluate(self, value):
        return NotImplementedError
    
    def search(self, queryset: QuerySet, name, value):
        value = str(value).strip().replace("/", "")
        search_query = self.evaluate(value)
        return queryset.filter(search_query)

