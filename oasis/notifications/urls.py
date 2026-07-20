from django.urls import path

from .views import (
    MarkAllReadView,
    NotificationFeedView,
    NotificationListView,
    OpenNotificationView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("feed/", NotificationFeedView.as_view(), name="feed"),
    path("read-all/", MarkAllReadView.as_view(), name="read-all"),
    path("<int:pk>/open/", OpenNotificationView.as_view(), name="open"),
]
