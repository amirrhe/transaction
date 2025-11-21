# notifications/senders.py
from abc import ABC, abstractmethod
from django.utils import timezone

from notifications.models import Notification, NotificationLog


class BaseMediumSender(ABC):
    """
    Strategy base class for sending notifications via a specific medium.
    Each concrete sender gets the notification + its log row.
    """

    @abstractmethod
    def send(self, notification: Notification, log: NotificationLog) -> None:
        """
        Implement medium-specific sending logic here.

        Raise an exception if sending fails.
        """
        raise NotImplementedError


class SMSSender(BaseMediumSender):
    def send(self, notification: Notification, log: NotificationLog) -> None:
        print(
            f"[{timezone.now()}] [SMS] user={notification.user_id} "
            f"title='{notification.title}' body='{notification.body}'"
        )


class EmailSender(BaseMediumSender):
    def send(self, notification: Notification, log: NotificationLog) -> None:
        print(
            f"[{timezone.now()}] [EMAIL] user={notification.user_id} "
            f"title='{notification.title}' body='{notification.body}'"
        )


class TelegramSender(BaseMediumSender):
    def send(self, notification: Notification, log: NotificationLog) -> None:
        print(
            f"[{timezone.now()}] [TELEGRAM] user={notification.user_id} "
            f"title='{notification.title}' body='{notification.body}'"
        )


class UnknownMediumError(Exception):
    pass


MEDIUM_SENDERS = {
    "sms": SMSSender(),
    "email": EmailSender(),
    "telegram": TelegramSender(),
}


def get_sender_for_medium(medium: str) -> BaseMediumSender:
    try:
        return MEDIUM_SENDERS[medium]
    except KeyError:
        raise UnknownMediumError(f"Unsupported medium: {medium}")
