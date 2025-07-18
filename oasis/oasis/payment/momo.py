import uuid
import requests
from django.conf import settings

BASE_URL = "https://sandbox.momodeveloper.mtn.com"
TARGET_ENV = "sandbox"

def get_token():
    url = f"{BASE_URL}/collection/token"
    headers = {
        "Ocp-Apim-Subscription-Key": settings.MOMO_SUBSCRIPTION_KEY,
        "Authorization": f"Basic {settings.MOMO_AUTH_STRING}"
    }
    response = requests.post(url, headers=headers)
    return response.json().get("access_token")


def request_payment(amount, phone_number, external_id, payer_message, payee_note):
    token = get_token()
    reference_id = str(uuid.uuid4())
    url = f"{BASE_URL}/collection/v1_0/requesttopay"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Target_Environment": TARGET_ENV,
        "Ocp-Apim-Subscription-Key": settings.MOMO_SUBSCRIPTION_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "amount" : str(amount),
        "currency": "GHS",
        "externalId": external_id,
        "payer": {
            "partyIdType": "MSIDN", 
            "partyId": phone_number,
        },
        "payerMessage": payer_message,
        "payeeNote": payee_note,
    }
    response = requests.post(url, headers=headers, json=payload)
    return reference_id, response.status_code, response.json() if response.content else {}