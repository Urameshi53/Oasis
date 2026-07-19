from django.apps import AppConfig


class VendorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vendor"
    verbose_name = "Vendor"

    def ready(self):
        from . import signals  # noqa: F401  (registers order_placed handler)
