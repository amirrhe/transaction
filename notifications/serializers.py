from rest_framework import serializers

from notifications.models import Notification, NotificationLog


class NotificationCreateSerializer(serializers.ModelSerializer):
    channels = serializers.ListField(
        child=serializers.ChoiceField(
            choices=NotificationLog.Medium.choices
        ),
        allow_empty=False,
        help_text="List of mediums, e.g. ['sms', 'email']",
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "user_id",
            "title",
            "body",
            "channels",
        ]


class NotificationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "user_id",
            "title",
            "body",
            "channels",
            "status",
            "created_at",
            "updated_at",
        ]
