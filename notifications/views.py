# notifications/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from notifications.models import Notification, NotificationLog
from notifications.serializers import (
    NotificationCreateSerializer,
    NotificationDetailSerializer,
)
from notifications.tasks import send_notification_task


class NotificationSendAPIView(APIView):
    """
    POST /api/notifications/send/

    Body:
    {
      "user_id": "42",
      "title": "Daily report",
      "body": "Your daily summary is ready.",
      "channels": ["sms", "email", "telegram"]
    }

    Creates a Notification + NotificationLog rows and enqueues Celery task.
    """

    def post(self, request, *args, **kwargs):
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification: Notification = Notification.objects.create(
            user_id=serializer.validated_data.get("user_id"),
            title=serializer.validated_data["title"],
            body=serializer.validated_data["body"],
            channels=serializer.validated_data["channels"],
            status=Notification.Status.PENDING,
        )

        channels = serializer.validated_data["channels"]
        logs = []
        for channel in channels:
            logs.append(
                NotificationLog(
                    notification=notification,
                    medium=channel,
                    status=NotificationLog.Status.PENDING,
                    attempts=0,
                )
            )
        NotificationLog.objects.bulk_create(logs)

        send_notification_task.delay(notification.id)

        response_data = {
            "id": notification.id,
            "status": "queued",
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
