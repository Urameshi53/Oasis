from django.apps import AppConfig


class RiderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rider"
    verbose_name = "Rider"

    def ready(self):
        from . import signals  # noqa: F401  (registers order_placed handler)
