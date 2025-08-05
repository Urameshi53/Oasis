from oscar.apps.payment.abstract_models import AbstractSource, AbstractTransaction
from django.db import models
import random

class Source(AbstractSource):
    paystack_reference = models.CharField(max_length=100)

class Transaction(AbstractTransaction):
    pass

from oscar.apps.payment.models import *  # noqaa
