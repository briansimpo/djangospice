from rest_framework import serializers
from djangospice.rest.serializers import NestedModelSerializer, OptionModelSerializer
from djangospice.apps.models import App, Category


class CategorySerializer(OptionModelSerializer):
    class Meta(OptionModelSerializer.Meta):
        model = Category
        
        
class AppSerializer(NestedModelSerializer):
    absolute_url = serializers.ReadOnlyField()

    flatten_fields = [
        "category"
    ]

    serializers = {
        "category": CategorySerializer
    }
    
    class Meta:
        model = App
        fields = [
            "id", "label", "name", "verbose_name", "description", 
            "url", "icon",  "absolute_url",
            "is_active", "is_service", "is_default",
        ]

