from django.conf import settings
from django.db import models


class Notification(models.Model):
    """A single in-app notification for a user (customer, seller or rider)."""

    INFO, SUCCESS, WARNING = "info", "success", "warning"
    LEVELS = [(INFO, "Info"), (SUCCESS, "Success"), (WARNING, "Warning")]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="app_notifications",
    )
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=400, blank=True)
    #: bootstrap-icons name (without the "bi-" prefix), e.g. "bag-check".
    icon = models.CharField(max_length=40, default="bell", blank=True)
    level = models.CharField(max_length=10, choices=LEVELS, default=INFO)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"To {self.recipient}: {self.message}"
