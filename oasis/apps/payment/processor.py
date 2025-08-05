import requests
from oscar.apps.checkout import views
from oscar.apps.payment.exceptions import UnableToTakePayment
from oscar.apps.payment import models
from django.conf import settings
from django.shortcuts import redirect

class PaystackPaymentDetailsView(views.PaymentDetailsView):

    def handle_payment(self, order_number, total, **kwargs):
        # This is where you would verify Paystack transaction
        reference = self.request.GET.get("reference")

        if not reference:
            raise UnableToTakePayment("Missing payment reference")

        # Verify with Paystack
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
        }
        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)

        if response.status_code != 200:
            raise UnableToTakePayment("Verification failed")

        result = response.json()["data"]
        amount_paid = result["amount"] / 100

        if amount_paid < total.incl_tax:
            raise UnableToTakePayment("Underpaid")

        # Save source
        source_type, _ = models.SourceType.objects.get_or_create(name="Paystack")
        source = models.Source(
            source_type=source_type,
            currency=total.currency,
            amount_allocated=total.incl_tax,
        )
        self.add_payment_source(source)
        self.add_payment_event("Settled", total.incl_tax)
