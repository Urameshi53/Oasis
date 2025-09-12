from django.utils import timezone
import datetime
from django.db import models
from django.contrib.auth.models import User
from django.forms import DateInput, ModelForm
from django.utils.timezone import now
from django.contrib import admin


# Create your models here.
class Shop(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    location = models.CharField(max_length=60, blank=True, default='Kumasi')
    school_name = models.CharField(max_length=60, blank=True, default='KNUST')
    email = models.EmailField(blank=True, default='knust@gmail.com')
    password = models.CharField(max_length=120)

    def __str__(self) -> str:
        return self.school_name
    
class Restaurant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    location = models.CharField(max_length=60, blank=True, default='Kumasi')
    school_name = models.CharField(max_length=60, blank=True, default='KNUST')
    email = models.EmailField(blank=True, default='knust@gmail.com')
    password = models.CharField(max_length=120)

    def __str__(self) -> str:
        return self.school_name
    

