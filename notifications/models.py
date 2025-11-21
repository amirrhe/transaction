# notifications/models.py
from djongo import models


class Notification(models.Model):
    """
    A high-level notification created by the API.
    Celery will create NotificationLog rows for each medium.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    user_id = models.CharField(max_length=128, null=True, blank=True)

    title = models.CharField(max_length=255)
    body = models.TextField()

    # Example: ["sms", "email", "telegram"]
    channels = models.JSONField(default=list)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notification"

    def __str__(self):
        return f"[{self.status}] {self.title} (user={self.user_id})"


class NotificationLog(models.Model):
    """
    One row per notification per channel (medium).
    Required for retry, exactly-once delivery, and reporting.
    """

    class Medium(models.TextChoices):
        SMS = "sms", "SMS"
        EMAIL = "email", "Email"
        TELEGRAM = "telegram", "Telegram"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    notification = models.ForeignKey(
        Notification,
        related_name="logs",
        on_delete=models.CASCADE,
    )

    medium = models.CharField(
        max_length=20,
        choices=Medium.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    attempts = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification_log"

    def __str__(self):
        return f"{self.notification_id} – {self.medium} – {self.status}"
