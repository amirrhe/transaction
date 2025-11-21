from dataclasses import dataclass
from typing import Sequence

from django.db import transaction

from notifications.models import Notification, NotificationLog
from notifications.tasks import send_notification_task


@dataclass
class NotificationCreateInput:
    user_id: int | str
    title: str
    body: str
    channels: Sequence[str]


def create_notification_with_logs(payload: NotificationCreateInput) -> Notification:
    """
    Pure(ish) service: creates Notification + NotificationLog rows in a transaction.
    Does NOT talk to Celery.
    """
    with transaction.atomic():
        notification = Notification.objects.create(
            user_id=payload.user_id,
            title=payload.title,
            body=payload.body,
            channels=list(payload.channels),
            status=Notification.Status.PENDING,
        )

        logs = [
            NotificationLog(
                notification=notification,
                medium=channel,
                status=NotificationLog.Status.PENDING,
                attempts=0,
            )
            for channel in payload.channels
        ]
        NotificationLog.objects.bulk_create(logs)

    return notification


def enqueue_notification(notification: Notification) -> None:
    """
    Thin wrapper around Celery makes it mockable in tests.
    """
    send_notification_task.delay(notification.id)
