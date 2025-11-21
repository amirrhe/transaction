from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from notifications.models import Notification, NotificationLog


class NotificationSendAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/notifications/send/"

    @patch("notifications.views.enqueue_notification")
    def test_creates_notification_and_logs_and_enqueues_task(self, mock_enqueue):
        payload = {
            "user_id": 42,
            "title": "Daily report",
            "body": "Your daily summary is ready.",
            "channels": ["sms", "email"],
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "queued")

        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.user_id, '42')
        self.assertEqual(notification.title, "Daily report")
        self.assertEqual(notification.body, "Your daily summary is ready.")
        self.assertEqual(sorted(notification.channels), ["email", "sms"])
        self.assertEqual(notification.status, Notification.Status.PENDING)

        logs = NotificationLog.objects.filter(notification=notification).order_by("medium")
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs[0].medium, "email")
        self.assertEqual(logs[0].status, NotificationLog.Status.PENDING)
        self.assertEqual(logs[0].attempts, 0)

        self.assertEqual(logs[1].medium, "sms")
        self.assertEqual(logs[1].status, NotificationLog.Status.PENDING)
        self.assertEqual(logs[1].attempts, 0)

        mock_enqueue.assert_called_once_with(notification)

    def test_invalid_channels_returns_400(self):
        payload = {
            "user_id": 42,
            "title": "Oops",
            "body": "Invalid channel",
            "channels": ["invalid-medium"],
        }

        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("channels", response.json())
