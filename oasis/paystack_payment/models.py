from oscar.apps.payment.abstract_models import AbstractSource, AbstractTransaction
from django.db import models

class PaystackSource(AbstractSource):
    paystack_reference = models.CharField(max_length=100, unique=True)

class PaystackTransaction(AbstractTransaction):
    pass

from oscar.apps.payment.models import *  # noqa
