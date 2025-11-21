from celery import shared_task
from django.utils import timezone

from notifications.models import Notification, NotificationLog
from notifications.senders import get_sender_for_medium, UnknownMediumError


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_notification_task(self, notification_id: int):
    """
    Load the notification and its logs, send via medium-specific strategies.

    - Uses Strategy Pattern (per-medium sender)
    - Skips logs already marked as SUCCESS (idempotent on retry)
    - On first failure, marks log as FAILED and retries the task
    """

    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return

    notification.status = Notification.Status.PROCESSING
    notification.save(update_fields=["status"])

    logs = notification.logs.all()

    for log in logs:
        if log.status == NotificationLog.Status.SUCCESS:
            continue

        try:
            sender = get_sender_for_medium(log.medium)
        except UnknownMediumError as e:
            log.status = NotificationLog.Status.FAILED
            log.attempts += 1
            log.last_attempt_at = timezone.now()
            log.error_message = str(e)
            log.save(
                update_fields=["status", "attempts", "last_attempt_at", "error_message"]
            )
            continue

        try:
            sender.send(notification, log)

            log.status = NotificationLog.Status.SUCCESS
            log.attempts += 1
            log.last_attempt_at = timezone.now()
            log.error_message = ""
            log.save(
                update_fields=["status", "attempts", "last_attempt_at", "error_message"]
            )

        except Exception as e:
            log.status = NotificationLog.Status.FAILED
            log.attempts += 1
            log.last_attempt_at = timezone.now()
            log.error_message = str(e)
            log.save(
                update_fields=["status", "attempts", "last_attempt_at", "error_message"]
            )
            raise self.retry(exc=e)

    total_logs = notification.logs.count()
    success_logs = notification.logs.filter(
        status=NotificationLog.Status.SUCCESS
    ).count()

    if total_logs == 0:
        notification.status = Notification.Status.FAILED
    elif success_logs == total_logs:
        notification.status = Notification.Status.SENT
    else:
        notification.status = Notification.Status.FAILED

    notification.updated_at = timezone.now()
    notification.save(update_fields=["status", "updated_at"])
