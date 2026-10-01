import django_filters
from djangospice.filters.base import OptionFilter
from djangospice.apps.models import App, Category
from djangospice.apps.helpers import get_category_list


class CategoryFilter(OptionFilter):
    class Meta(OptionFilter.Meta):
        model = Category


class AppFilter(django_filters.FilterSet):
    label = django_filters.CharFilter(lookup_expr='icontains')
    is_active = django_filters.BooleanFilter()
    category = django_filters.ModelChoiceFilter(queryset=get_category_list)
    

    class Meta:
        model = App
        fields = ['label', 'is_active' , 'category']

