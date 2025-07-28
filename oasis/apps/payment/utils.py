# payments/utils.py
import requests
from django.conf import settings

def initialize_payment(email, amount, reference):
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": amount * 100,  # Paystack expects amount in kobo/pesewas
        "reference": reference,
        "callback_url": "http://localhost:8000/payments/verify/"
    }
    url = "https://api.paystack.co/transaction/initialize"
    response = requests.post(url, json=data, headers=headers)
    return response.json()
