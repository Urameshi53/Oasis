# payments/paystack.py

import requests
from django.conf import settings

def initialize_payment(email, amount, reference, callback_url):
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "email": email,
        "amount": int(amount * 100),  # Paystack expects amount in kobo
        "reference": reference,
        "callback_url": callback_url,
    }
    response = requests.post(settings.PAYSTACK_INITIALIZE_URL, json=data, headers=headers)
    return response.json()

def verify_payment(reference):
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    url = settings.PAYSTACK_VERIFY_URL + reference
    response = requests.get(url, headers=headers)
    return response.json()
