import uuid
import requests
from django.conf import settings

BASE_URL = "https://sandbox.momodeveloper.mtn.com"
COLLECTION_PRIMARY_KEY = settings.MOMO_PRIMARY_KEY  # from settings.py

# Your API user credentials
API_USER_ID = settings.MOMO_API_USER
API_KEY = settings.MOMO_API_KEY
SUBSCRIPTION_KEY = settings.MOMO_SUBSCRIPTION_KEY
TARGET_ENV = "sandbox"  # or "production"

def get_token():
    url = f"{BASE_URL}/collection/token/"
    headers = {
        "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
        "Authorization": f"Basic {API_USER_ID}:{API_KEY}",
    }
    response = requests.post(url, headers=headers)
    return response.json().get("access_token")

def request_payment(amount, phone_number, external_id, payer_message, payee_note):
    token = get_token()
    url = f"{BASE_URL}/collection/v1_0/requesttopay"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Reference-Id": str(uuid.uuid4()),
        "X-Target-Environment": TARGET_ENV,
        "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "amount": str(amount),
        "currency": "EUR",  # or "GHS" depending on region
        "externalId": external_id,
        "payer": {
            "partyIdType": "MSISDN",
            "partyId": phone_number,
        },
        "payerMessage": payer_message,
        "payeeNote": payee_note,
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code, response.json() if response.content else {}
