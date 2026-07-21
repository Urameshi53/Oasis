from django.apps import AppConfig
import oscar.apps.customer.apps as apps

class CustomerConfig(apps.CustomerConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.customer'

    def ready(self):
        super().ready()
        self.user_registration_form = "apps.customer.forms.CustomUserCreationForm"