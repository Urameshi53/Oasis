# custom_address/models.py
from oscar.apps.address.abstract_models import AbstractShippingAddress, AbstractUserAddress, AbstractCountry
from django.db import models
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import is_model_registered

__all__ = []

if not is_model_registered("address", "Country"):

    class Country(AbstractCountry):
        pass

    __all__.append("Country")


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
    

class ShippingAddress(AbstractShippingAddress):
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
    



