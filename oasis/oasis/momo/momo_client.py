import uuid
import requests

class MoMoAPI:
    def __init__(self):
        self.base_url = "https://sandbox.momodeveloper.mtn.com/collection/v1_0"
        self.token_url = "https://sandbox.momodeveloper.mtn.com/collection/token/"
        self.api_user = "Lancelot"
        self.api_key = "your_api_key"
        self.subscription_key = "473dcb5fdf2448cb9c35c992d7946ca3"
        self.environment = "sandbox"
        self.currency = "GHS"
        self.callback_host = "http://127.0.0.1:8000/"  # For live

    def get_token(self):
        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Authorization": f"Basic {self.api_user}:{self.api_key}"
        }
        response = requests.post(self.token_url, headers=headers)
        return response.json().get("access_token")

    def request_to_pay(self, amount, phone, external_id, message="Order Payment"):
        token = self.get_token()
        url = f"{self.base_url}/requesttopay"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": str(uuid.uuid4()),
            "X-Target-Environment": self.environment,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json"
        }
        body = {
            "amount": str(amount),
            "currency": self.currency,
            "externalId": external_id,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone
            },
            "payerMessage": message,
            "payeeNote": message
        }
        res = requests.post(url, json=body, headers=headers)
        return res.status_code == 202
