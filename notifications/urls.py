from django.urls import path

from notifications.views import NotificationSendAPIView

urlpatterns = [
    path(
        "send/",
        NotificationSendAPIView.as_view(),
        name="notification-send",
    ),
]
