from oscar.apps.payment.models import * 


# payments/models.py
from django.db import models

class PaystackPayment(models.Model):
    email = models.EmailField()
    amount = models.PositiveIntegerField()
    ref = models.CharField(max_length=100, unique=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} - {self.amount} - {self.verified}"
