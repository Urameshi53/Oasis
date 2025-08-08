import requests
from django.conf import settings
from oscar.apps.checkout.views import PaymentDetailsView
from oscar.apps.payment.models import SourceType, Source
from oscar.apps.payment.exceptions import PaymentError
from oscar.core.loading import get_model

Country = get_model('address', 'Country')

class PaystackPaymentView(PaymentDetailsView):
    '''def build_submission(self, **kwargs):
        # Get base submission data from Oscar
        submission = super().build_submission(**kwargs)

        # Set Ghana as the default shipping country
        try:
            ghana = Country.objects.get(iso_3166_1_a2='GH')
        except Country.DoesNotExist:
            ghana = Country.objects.create(iso_3166_1_a2='GH', name='Ghana')

        if submission['shipping_address']:
            submission['shipping_address'].country = ghana

        return submission'''

    def handle_payment(self, order_number, total, **kwargs):

        pass
        '''reference = self.request.POST.get('paystack_reference')

        if not reference:
            raise PaymentError("Missing Paystack reference.")

        try:
            # Verify payment with Paystack
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            }

            response = requests.get(
                "11223",
                headers=headers
            )
            data = response.json()

            if not data.get('status'):
                raise PaymentError("Transaction verification failed.")

            paid_amount = data['data']['amount'] / 100  # convert from pesewas

            if paid_amount != total.incl_tax:
                raise PaymentError("Paid amount doesn't match order total.")

            # Log to Oscar payment
            source_type, _ = SourceType.objects.get_or_create(name='Paystack')
            source = Source(
                source_type=source_type,
                currency=total.currency,
                amount_allocated=paid_amount
            )
            self.add_payment_source(source)
            self.add_payment_event('Settled', paid_amount)

            # Optional: log to custom model
            

        except Exception as e:
            raise PaymentError(f"Payment failed: {str(e)}")'''
