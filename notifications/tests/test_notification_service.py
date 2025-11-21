from django.test import TestCase

from notifications.models import Notification, NotificationLog
from notifications.services import (
    NotificationCreateInput,
    create_notification_with_logs,
)


class NotificationServiceTest(TestCase):
    def test_create_notification_with_logs(self):
        payload = NotificationCreateInput(
            user_id=99,
            title="Hello",
            body="Body here",
            channels=["sms", "email", "telegram"],
        )

        notification = create_notification_with_logs(payload)

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(notification.user_id, 99)
        self.assertEqual(notification.title, "Hello")
        self.assertEqual(notification.body, "Body here")
        self.assertEqual(sorted(notification.channels), ["email", "sms", "telegram"])
        self.assertEqual(notification.status, Notification.Status.PENDING)

        logs = NotificationLog.objects.filter(notification=notification).order_by("medium")
        self.assertEqual(logs.count(), 3)
        mediums = [log.medium for log in logs]
        self.assertEqual(sorted(mediums), ["email", "sms", "telegram"])
        for log in logs:
            self.assertEqual(log.status, NotificationLog.Status.PENDING)
            self.assertEqual(log.attempts, 0)
