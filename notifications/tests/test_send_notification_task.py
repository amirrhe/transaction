from unittest.mock import Mock, patch

from django.test import TestCase

from notifications.models import Notification, NotificationLog
from notifications.tasks import send_notification_task
from notifications.senders import UnknownMediumError


class SendNotificationTaskTest(TestCase):
    def _create_notification_with_logs(self, mediums):
        notification = Notification.objects.create(
            user_id=1,
            title="Test",
            body="Body",
            channels=mediums,
            status=Notification.Status.PENDING,
        )
        logs = [
            NotificationLog.objects.create(
                notification=notification,
                medium=m,
                status=NotificationLog.Status.PENDING,
                attempts=0,
            )
            for m in mediums
        ]
        return notification, logs

    @patch("notifications.tasks.get_sender_for_medium")
    def test_all_mediums_success_marks_notification_sent(self, mock_get_sender):
        notification, logs = self._create_notification_with_logs(["sms", "email"])

        fake_sender = Mock()
        fake_sender.send = Mock()
        mock_get_sender.return_value = fake_sender

        send_notification_task(notification.id)

        notification.refresh_from_db()
        logs = list(notification.logs.order_by("medium"))

        self.assertEqual(notification.status, Notification.Status.SENT)
        for log in logs:
            self.assertEqual(log.status, NotificationLog.Status.SUCCESS)
            self.assertEqual(log.attempts, 1)
            self.assertIsNotNone(log.last_attempt_at)

        self.assertEqual(fake_sender.send.call_count, 2)

    def test_unknown_medium_marks_log_failed_but_does_not_retry(self):
        notification, logs = self._create_notification_with_logs(["unknown"])

        with patch(
            "notifications.tasks.get_sender_for_medium",
            side_effect=UnknownMediumError("Unsupported medium: unknown"),
        ):
            send_notification_task(notification.id)

        notification.refresh_from_db()
        log = notification.logs.get()

        self.assertEqual(log.status, NotificationLog.Status.FAILED)
        self.assertEqual(log.attempts, 1)
        self.assertIsNotNone(log.last_attempt_at)
        self.assertIn("Unsupported medium", log.error_message)

        self.assertEqual(notification.status, Notification.Status.FAILED)

    @patch("notifications.tasks.get_sender_for_medium")
    def test_sender_exception_marks_failed_and_raises_retry(self, mock_get_sender):
        notification, logs = self._create_notification_with_logs(["sms"])

        fake_sender = Mock()
        fake_sender.send.side_effect = RuntimeError("SMS gateway down")
        mock_get_sender.return_value = fake_sender
        with self.assertRaises(RuntimeError):
            send_notification_task(notification.id)

        notification.refresh_from_db()
        log = notification.logs.get()

        self.assertEqual(log.status, NotificationLog.Status.FAILED)
        self.assertEqual(log.attempts, 1)
        self.assertIsNotNone(log.last_attempt_at)
        self.assertIn("SMS gateway down", log.error_message)

    def test_no_logs_marks_notification_failed(self):
        notification = Notification.objects.create(
            user_id=1,
            title="No logs",
            body="",
            channels=[],
            status=Notification.Status.PENDING,
        )

        send_notification_task(notification.id)

        notification.refresh_from_db()
        self.assertEqual(notification.status, Notification.Status.FAILED)
