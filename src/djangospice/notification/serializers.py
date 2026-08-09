from rest_framework import serializers
from djangospice.rest.serializers import BaseModelSerializer
from .models import Notification


class NotificationSerializer(BaseModelSerializer):
    actor = serializers.StringRelatedField(read_only=True)
    timesince = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "actor",
            "verb",
            "level",
            "description",
            "timestamp",
            "timesince",
            "unread",
            "data",
        ]
        # Read-only fields ensure this serializer can be safely used for outputs
        read_only_fields = ["timestamp", "data"]

    def get_timesince(self, obj: Notification) -> str:
        """
        Returns a display-friendly version of the timestamp.
        """
        return obj.timesince()