# custom_address/models.py
from oscar.apps.address.abstract_models import AbstractShippingAddress, AbstractUserAddress, AbstractCountry
from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import is_model_registered, get_model
from django.core.validators import RegexValidator
from oscar.core.loading import get_model


__all__ = []

# Validator: 10 digits, starting with 0
phone_validator = RegexValidator(
    regex=r'^0\d{9}$',
    message="Phone number must be exactly 10 digits and start with 0."
)

if not is_model_registered("address", "Country"):

    class Country(AbstractCountry):
        pass

    __all__.append("Country")

Country = get_model("address", "Country")

ghana = Country.objects.get(iso_3166_1_a2='GH')



class UserAddress(AbstractUserAddress):
    hostel = models.CharField(_("Hostel/Hall"), default='Indece', max_length=128)
    room_number = models.CharField(_("Room number"), default='001', max_length=10)
    LOCATION_CHOICES = [
        ('campus', 'Campus'),
        ('tech_junction', 'Tech Junction'),
        ('ayeduase', 'Ayeduase'),
        ('kotei', 'Kotei'),
        ('atonsu', 'Atonsu'),
        ('deduako', 'Deduako'),
        ('new_site', 'New Site'),
    ]
    location = models.CharField(_("Location"), choices=LOCATION_CHOICES, max_length=128, default='campus')
    phone = models.CharField(
        _("Phone Number"),
        max_length=10,
        validators=[phone_validator],
        help_text="Enter a valid 10-digit phone number starting with 0",
        default="0123456789",
    )


class ShippingAddress(AbstractShippingAddress):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country = ghana
    
    hostel = models.CharField(_("Hostel/Hall"), default='Indece', max_length=128)
    room_number = models.CharField(_("Room number"), default='001', max_length=10)
    LOCATION_CHOICES = [
        ('campus', 'Campus'),
        ('tech_junction', 'Tech Junction'),
        ('ayeduase', 'Ayeduase'),
        ('kotei', 'Kotei'),
        ('atonsu', 'Atonsu'),
        ('deduako', 'Deduako'),
        ('new_site', 'New Site'),
    ]
    location = models.CharField(_("Location"), choices=LOCATION_CHOICES, max_length=128, default='campus')
    phone = models.CharField(
        _("Phone Number"),
        max_length=10,
        validators=[phone_validator],
        help_text="Enter a valid 10-digit phone number starting with 0",
        default="0123456789",
    )


