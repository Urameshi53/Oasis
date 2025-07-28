from oscar.apps.catalogue.abstract_models import AbstractProduct
from django.db import models 
'''
class Product(AbstractProduct):
    description = models.TextField()
    is_available = models.BooleanField(default=True)
    categories = models.CharField(max_length=100, choices=[
        ('starter', 'Starter'),
        ('main', 'Main Course'),
        ('dessert', 'Dessert'),
        ('drink', 'Drink'),
    ])
'''
from oscar.apps.catalogue.models import * # Keep the rest of the Oscar models
#from .abstract_models import RestaurantMenuItem