from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from notifications.serializers import NotificationCreateSerializer
from notifications.services import (
    NotificationCreateInput,
    create_notification_with_logs,
    enqueue_notification,
)


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

        payload = NotificationCreateInput(
            user_id=serializer.validated_data["user_id"],
            title=serializer.validated_data["title"],
            body=serializer.validated_data["body"],
            channels=serializer.validated_data["channels"],
        )

        notification = create_notification_with_logs(payload)
        enqueue_notification(notification)

        response_data = {
            "id": notification.id,
            "status": "queued",
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
